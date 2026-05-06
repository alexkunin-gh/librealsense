# License: Apache 2.0. See LICENSE file in root directory.
# Copyright(c) 2026 RealSense, Inc. All Rights Reserved.

import logging
import numpy as np
import pytest
import pyrealsense2 as rs

log = logging.getLogger(__name__)

pytestmark = [
    pytest.mark.device_each("D400*"),
    pytest.mark.device_each("D500*"),
    pytest.mark.device_exclude("D555"),
]

# rotation tolerance - units are in cosinus of radians
ROTATION_TOLERANCE = 1e-5
# translation tolerance - units are in meters
TRANSLATION_TOLERANCE = 1e-4  # 0.1mm


def matrix_4x4_from_extrinsics(extr):
    """Build a 4x4 pose matrix from rs2_extrinsics.

    Rotation in extr.rotation is column-major 3x3 (9 floats).
    """
    r = extr.rotation
    t = extr.translation
    m = np.eye(4)
    m[0, 0] = r[0]
    m[1, 0] = r[1]
    m[2, 0] = r[2]
    m[0, 1] = r[3]
    m[1, 1] = r[4]
    m[2, 1] = r[5]
    m[0, 2] = r[6]
    m[1, 2] = r[7]
    m[2, 2] = r[8]
    m[0, 3] = t[0]
    m[1, 3] = t[1]
    m[2, 3] = t[2]
    return m


def matrices_equal(a, b):
    """Check 4x4 pose matrices match within rotation/translation tolerances."""
    diff = np.abs(a - b)
    rotation_part_ok = np.all(diff[:, 0:3] <= ROTATION_TOLERANCE)
    translation_part_ok = np.all(diff[:, 3] <= TRANSLATION_TOLERANCE)
    if not (rotation_part_ok and translation_part_ok):
        log.info("matrix diff:\n%s", diff)
    return rotation_part_ok and translation_part_ok


def is_identity(m):
    return matrices_equal(m, np.eye(4))


ROTATION_DIAGONAL_MIN = 0.95
ROTATION_DIAGONAL_MAX = 1.0


def check_calibration_criteria(extr):
    r = extr.rotation
    return (ROTATION_DIAGONAL_MIN < r[0] <= ROTATION_DIAGONAL_MAX
            and ROTATION_DIAGONAL_MIN < r[4] <= ROTATION_DIAGONAL_MAX
            and ROTATION_DIAGONAL_MIN < r[8] <= ROTATION_DIAGONAL_MAX)


def is_rgb_calibrated(profiles):
    depth = next((p for p in profiles if p.stream_type() == rs.stream.depth), None)
    color = next((p for p in profiles if p.stream_type() == rs.stream.color), None)
    if depth is None or color is None:
        return False
    return check_calibration_criteria(depth.get_extrinsics_to(color))


def test_extrinsics_graph_4x4(test_device):
    """Extrinsics graph - matrices 4x4

    For each pair of stream profiles A,B on the device, check:
      1. extr(A->B) * extr(B->A) == identity
      2. rs2_transform_point_to_point round-trips a point through A->B->A
      3. The point+orientation 4x4 matrix round-trips through A->B->A
    """
    device, _ = test_device
    log.info("device: %s", device.get_info(rs.camera_info.name))
    sensors = device.query_sensors()

    profiles = []
    for sensor in sensors:
        profiles.extend(sensor.get_stream_profiles())

    streams_to_ignore = [rs.stream.accel, rs.stream.gyro]
    if not is_rgb_calibrated(profiles):
        log.info("RGB is not calibrated on this device")
        streams_to_ignore.append(rs.stream.color)

    relevant_profiles = [p for p in profiles if p.stream_type() not in streams_to_ignore]

    start_point = [1.0, 2.0, 3.0]

    # rotation part with 30 degrees rotation on each axis
    point_and_orientation = np.array([
        [ 0.75,      -0.4330127,  0.5,       1.0],
        [ 0.649519,   0.625,     -0.4330127, 2.0],
        [-0.125,      0.649519,   0.75,      3.0],
        [ 0.0,        0.0,        0.0,       1.0],
    ])

    for i in range(len(relevant_profiles) - 2):
        for j in range(i + 1, len(relevant_profiles) - 1):
            p_i = relevant_profiles[i]
            p_j = relevant_profiles[j]
            extr_i_to_j = p_i.get_extrinsics_to(p_j)
            extr_j_to_i = p_j.get_extrinsics_to(p_i)

            pr_i_to_j = matrix_4x4_from_extrinsics(extr_i_to_j)
            pr_j_to_i = matrix_4x4_from_extrinsics(extr_j_to_i)

            product = pr_i_to_j @ pr_j_to_i
            if not is_identity(product):
                log.info("i : stream %s, format %s, fps %s, index %s",
                         p_i.stream_type(), p_i.format(), p_i.fps(), p_i.stream_index())
                log.info("j : stream %s, format %s, fps %s, index %s",
                         p_j.stream_type(), p_j.format(), p_j.fps(), p_j.stream_index())
            assert is_identity(product)

            # checking with API rs2_transform_point_to_point
            transformed_point = rs.rs2_transform_point_to_point(extr_i_to_j, start_point)
            end_point = rs.rs2_transform_point_to_point(extr_j_to_i, transformed_point)
            assert end_point == pytest.approx(start_point, abs=1e-3)

            # applying extrinsics from i to j on point with orientation
            retransformed_temp = pr_j_to_i @ point_and_orientation
            # applying extrinsics from j to i
            retransformed = pr_i_to_j @ retransformed_temp
            assert matrices_equal(retransformed, point_and_orientation)
