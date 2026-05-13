# License: Apache 2.0. See LICENSE file in root directory.
# Copyright(c) 2026 RealSense, Inc. All Rights Reserved.

"""
Sanity tests for iq_helper.is_color_close.

is_color_close is the basis of the image-quality color checks. We compare in HSV
rather than per-channel RGB because lab illumination drifts together across all
channels — a dim rig shifts every bright color toward darker RGB and trips a
per-channel tolerance, but in HSV the hue stays stable and V absorbs the
brightness shift. The test below pins this behavior:

- identical colors pass, slight per-channel drift passes, dimmer-same-hue passes
- clearly distinct colors fail (e.g. blue must not match red)
- achromatic (black/white) must not match a chromatic swatch, and black must
  not match white (V tolerance is bounded)
"""

import sys, os, types

# CI runners don't ship pyrealsense2; iq_helper imports it at module top but
# is_color_close itself only uses cv2+numpy, so a stub module is enough.
sys.modules.setdefault('pyrealsense2', types.ModuleType('pyrealsense2'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'live', 'image-quality'))

from iq_helper import is_color_close


RED    = (220, 20, 30)
GREEN  = (30, 200, 50)
BLUE   = (30, 50, 220)
BLACK  = (10, 10, 10)
WHITE  = (240, 240, 240)
YELLOW = (220, 200, 30)


def test_same_color_passes():
    for c in (RED, GREEN, BLUE, BLACK, WHITE, YELLOW):
        assert is_color_close(c, c), f"identical {c} should match itself"


def test_distinct_chromatic_colors_fail():
    # If the gate were too loose, blue could pass for red. It must not.
    assert not is_color_close(BLUE, RED),     "blue must not match red"
    assert not is_color_close(RED, BLUE),     "red must not match blue"
    assert not is_color_close(RED, GREEN),    "red must not match green"
    assert not is_color_close(YELLOW, BLUE),  "yellow must not match blue"


def test_achromatic_vs_chromatic_fail():
    # Black/white can't pass for a colored swatch.
    assert not is_color_close(BLACK, RED),    "black must not match red"
    assert not is_color_close(WHITE, BLUE),   "white must not match blue"
    assert not is_color_close(RED, BLACK),    "red must not match black"


def test_slight_drift_passes():
    # Small per-channel drift on a chromatic color should pass.
    drifted_red = (RED[0] - 5, RED[1] + 3, RED[2] - 2)
    assert is_color_close(drifted_red, RED), f"slight drift {drifted_red} should still match red"


def test_brightness_drift_passes_for_chromatic():
    # Lighting-driven V shift on a colored swatch — hue identity preserved.
    dim_red = (RED[0] - 30, RED[1] - 15, RED[2] - 15)
    assert is_color_close(dim_red, RED), "dimmer-but-same-hue red should still match"


def test_black_vs_white_fail():
    # Both achromatic but very different brightness — V tolerance must reject.
    assert not is_color_close(BLACK, WHITE), "black must not match white"
    assert not is_color_close(WHITE, BLACK), "white must not match black"
