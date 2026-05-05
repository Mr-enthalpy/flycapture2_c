from __future__ import annotations

import pytest

from flycapture2_c import Camera
from flycapture2_c.errors import FlyCapture2Error


def test_hardware_strobe_info_readonly(hardware_guard, hardware_config) -> None:
    _ = hardware_guard
    with Camera.open(index=hardware_config.camera_index) as camera:
        try:
            info = camera.get_strobe_info(source=0)
        except FlyCapture2Error as exc:
            pytest.skip(f"strobe source 0 info is not available: {exc}")
        if not info.present:
            pytest.skip("strobe source 0 is not present on this camera")

        assert info.source == 0
        assert info.max_value >= info.min_value

        if info.read_out_supported:
            control = camera.get_strobe(source=0)
            assert control.source == 0
            assert control.duration >= 0


def test_hardware_gpio_pin_direction_readonly(hardware_guard, hardware_config) -> None:
    _ = hardware_guard
    with Camera.open(index=hardware_config.camera_index) as camera:
        try:
            direction = camera.get_gpio_pin_direction(0)
        except FlyCapture2Error as exc:
            pytest.skip(f"GPIO pin direction readback is not available: {exc}")

        assert direction in {0, 1}
