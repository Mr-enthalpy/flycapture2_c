from __future__ import annotations

import pytest

from flycapture2_c import Camera
from flycapture2_c._hardware_tools import capture_one_frame

pytestmark = pytest.mark.hardware


def test_hardware_grab_one(hardware_guard, hardware_config) -> None:
    with Camera.open(index=hardware_config.camera_index) as camera:
        summary = capture_one_frame(camera, timeout_ms=hardware_config.capture_timeout_ms)

    assert len(summary.shape) == 2
    assert summary.shape == (summary.height, summary.width)
    assert summary.own_data is True
    itemsize = 1 if summary.dtype == "uint8" else 2
    assert summary.stride >= summary.width * itemsize
    assert summary.dtype in {"uint8", "uint16"}
    assert summary.pixel_format in {"MONO8", "MONO16", "RAW8", "RAW16"}
