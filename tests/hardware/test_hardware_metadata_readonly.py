from __future__ import annotations

import pytest

from flycapture2_c import Camera
from flycapture2_c.errors import FlyCapture2Error


def test_hardware_embedded_image_info_and_stats_readonly(hardware_guard, hardware_config) -> None:
    _ = hardware_guard
    with Camera.open(index=hardware_config.camera_index) as camera:
        embedded_info = camera.get_embedded_image_info()
        assert len(embedded_info.iter_fields()) == 10
        if not any(field.available for _, field in embedded_info.iter_fields()):
            pytest.skip("camera does not report embedded image metadata support")

        try:
            stats = camera.get_camera_stats()
        except FlyCapture2Error as exc:
            pytest.skip(f"camera stats not available on this camera/driver: {exc}")

        assert stats.image_dropped >= 0
        assert stats.image_corrupt >= 0
        assert stats.num_resend_packets_requested >= 0
        assert stats.num_resend_packets_received >= 0
