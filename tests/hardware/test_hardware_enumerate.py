from __future__ import annotations

import pytest

from flycapture2_c import enumerate_cameras

pytestmark = pytest.mark.hardware


def test_hardware_enumerate(hardware_guard, hardware_config) -> None:
    cameras = enumerate_cameras()
    assert cameras
    assert 0 <= hardware_config.camera_index < len(cameras)
