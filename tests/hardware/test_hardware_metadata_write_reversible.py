from __future__ import annotations

import pytest

from flycapture2_c import Camera
from flycapture2_c.errors import FC2ErrorCode, FlyCapture2Error, FlyCapture2NotSupportedError


def test_hardware_embedded_image_info_write_reversible(hardware_write_guard, hardware_config) -> None:
    _ = hardware_write_guard
    with Camera.open(index=hardware_config.camera_index) as camera:
        old_info = camera.get_embedded_image_info()
        field_name = next(
            (
                name
                for name in ("timestamp", "frame_counter")
                if getattr(old_info, name).available
            ),
            None,
        )
        if field_name is None:
            pytest.skip("camera does not report timestamp or frame counter embedded metadata support")

        try:
            updated = camera.set_embedded_image_info(**{field_name: True})
            assert getattr(updated, field_name).on_off is True

            camera.start()
            frame = camera.read_frame_with_info()
            assert frame.metadata is not None
            assert isinstance(getattr(frame.metadata, field_name), int)
        finally:
            camera.stop()
            camera.set_embedded_image_info(old_info)

        restored = camera.get_embedded_image_info()
        assert getattr(restored, field_name).on_off == getattr(old_info, field_name).on_off


def test_hardware_reset_camera_stats_write_gated(hardware_write_guard, hardware_config) -> None:
    _ = hardware_write_guard
    with Camera.open(index=hardware_config.camera_index) as camera:
        try:
            camera.get_camera_stats()
        except FlyCapture2Error as exc:
            pytest.skip(f"camera stats not available on this camera/driver: {exc}")

        try:
            camera.reset_camera_stats()
        except FlyCapture2NotSupportedError as exc:
            pytest.skip(str(exc))
        except FlyCapture2Error as exc:
            if exc.code in {FC2ErrorCode.NOT_IMPLEMENTED, FC2ErrorCode.NOT_SUPPORTED}:
                pytest.skip(f"ResetStats is not supported by this SDK/camera: {exc}")
            raise

        stats = camera.get_camera_stats()
        assert stats.image_dropped >= 0
