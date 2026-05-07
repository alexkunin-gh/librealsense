# License: Apache 2.0. See LICENSE file in root directory.
# Copyright(c) 2026 RealSense, Inc. All Rights Reserved.

import json
import logging
import time

import pytest
import pyrealsense2 as rs
from pytest_check import check
from rspy.pytest.device_helpers import is_jetson_platform

import hdr_helper
from hdr_helper import HDR_CONFIGURATIONS

log = logging.getLogger(__name__)

pytestmark = [
    pytest.mark.device("D457" if is_jetson_platform() else "D455"),
    pytest.mark.context("nightly"),
]

EXPECTED_FPS = 30
ACCEPTABLE_FPS = EXPECTED_FPS * 0.9
TIME_FOR_STEADY_STATE = 3
TIME_TO_COUNT_FRAMES = 5


class FrameCounter:
    def __init__(self):
        self.count = 0
        self.counting = False

    def callback(self, frame):
        if not self.counting:
            return  # Skip counting if not enabled
        self.count += 1
        log.debug("Frame callback called, frame number: %s", frame.get_frame_number())


def test_hdr_performance(test_device):
    """
    Test HDR performance with various configurations
    """
    hdr_helper.setup_for_device(test_device)
    sensor = hdr_helper.sensor

    counter = FrameCounter()

    for i, config in enumerate(HDR_CONFIGURATIONS):
        config_type = "Auto" if "depth-ae" in json.dumps(config) else "Manual"
        num_items = len(config["hdr-preset"]["items"])
        test_name = f"Config {i + 1} ({config_type}, {num_items} items)"
        hdr_helper.test_json_load(config, test_name)

        counter.count = 0
        depth_profile = next(p for p in sensor.get_stream_profiles() if p.stream_type() == rs.stream.depth)
        sensor.open(depth_profile)
        sensor.start(counter.callback)

        time.sleep(TIME_FOR_STEADY_STATE)
        counter.counting = True  # Start counting frames
        time.sleep(TIME_TO_COUNT_FRAMES)
        counter.counting = False  # Stop counting

        sensor.stop()
        sensor.close()

        measured_fps = counter.count / TIME_TO_COUNT_FRAMES
        log.debug("Test %s: Counted frames = %d, Measured FPS = %.2f", test_name, counter.count, measured_fps)
        check.greater(measured_fps, ACCEPTABLE_FPS, f"Measured FPS {measured_fps:.2f}")
