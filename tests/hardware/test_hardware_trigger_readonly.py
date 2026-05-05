from __future__ import annotations

import pytest

from flycapture2_c import Camera, enumerate_cameras

pytestmark = pytest.mark.hardware


def test_hardware_trigger_readonly(hardware_guard, hardware_config) -> None:
    cameras = enumerate_cameras()
    with Camera.open(index=hardware_config.camera_index) as camera:
        info = camera.get_trigger_mode_info()
        mode = camera.get_trigger_mode()

    assert len(cameras) > hardware_config.camera_index
    assert isinstance(info.present, bool)
    assert isinstance(info.source_mask, int)
    assert isinstance(info.mode_mask, int)
    assert isinstance(mode.on_off, bool)
    assert isinstance(mode.source, int)
    assert isinstance(mode.mode, int)
    if not info.present:
        pytest.skip("camera reports no trigger mode support")
    assert info.read_out_supported or info.value_readable
