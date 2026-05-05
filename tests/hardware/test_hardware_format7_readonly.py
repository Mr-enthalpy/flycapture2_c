from __future__ import annotations

import pytest

from flycapture2_c import Camera
from flycapture2_c.errors import FlyCapture2Error

pytestmark = pytest.mark.hardware


def test_hardware_format7_and_configuration_readonly(hardware_guard, hardware_config) -> None:
    with Camera.open(index=hardware_config.camera_index) as camera:
        try:
            info = camera.get_format7_info(mode=0)
        except FlyCapture2Error as exc:
            pytest.skip(f"Format7 info query failed on this camera: {exc}")
        configuration = camera.get_configuration()

        current_format7 = None
        if info.supported:
            try:
                current_format7 = camera.get_format7_configuration()
            except FlyCapture2Error:
                current_format7 = None

    assert isinstance(info.supported, bool)
    assert isinstance(info.max_width, int)
    assert isinstance(info.max_height, int)
    assert isinstance(configuration.grab_timeout, int)
    assert configuration.num_buffers >= 0
    if not info.supported:
        pytest.skip("Format7 mode 0 is not supported by this camera")
    assert info.max_width > 0
    assert info.max_height > 0
    if current_format7 is not None:
        assert current_format7.settings.mode == 0
        assert current_format7.settings.width > 0
        assert current_format7.settings.height > 0
