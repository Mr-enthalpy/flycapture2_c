from __future__ import annotations

import math

import pytest

from flycapture2_c import Camera
from flycapture2_c._hardware_tools import capture_short_sequence

pytestmark = pytest.mark.hardware


def test_hardware_grab_short_sequence(hardware_guard, hardware_config) -> None:
    with Camera.open(index=hardware_config.camera_index) as camera:
        summary = capture_short_sequence(
            camera,
            frame_count=hardware_config.frame_count,
            timeout_ms=hardware_config.capture_timeout_ms,
        )

    assert summary.frame_count == hardware_config.frame_count
    assert len(summary.shape) == 2
    assert summary.dtype in {"uint8", "uint16"}
    assert summary.pixel_format in {"MONO8", "MONO16", "RAW8", "RAW16"}
    assert math.isfinite(summary.min_value)
    assert math.isfinite(summary.max_value)
    assert math.isfinite(summary.mean_value)
    assert math.isfinite(summary.fps_estimate)
