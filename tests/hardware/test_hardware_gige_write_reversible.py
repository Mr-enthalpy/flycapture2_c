from __future__ import annotations

import pytest

from flycapture2_c import Camera
from flycapture2_c.errors import FlyCapture2Error
from flycapture2_c.gige import GigEPropertyType

FC2_INTERFACE_GIGE = 3


def _require_gige_camera(camera: Camera) -> None:
    info = camera.get_camera_info(refresh=True)
    if info.interface_type != FC2_INTERFACE_GIGE:
        pytest.skip(f"connected camera interface_type={info.interface_type}; GigE-specific tests require GigE")


def test_hardware_gige_config_write_same_value(hardware_write_guard, hardware_config) -> None:
    _ = hardware_write_guard
    with Camera.open(index=hardware_config.camera_index) as camera:
        _require_gige_camera(camera)
        try:
            old = camera.get_gige_config()
        except FlyCapture2Error as exc:
            pytest.skip(f"GigE config readback is not available: {exc}")

        try:
            written = camera.set_gige_config(old)
        except FlyCapture2Error as exc:
            pytest.skip(f"GigE same-value config write is not available: {exc}")
        finally:
            try:
                restored = camera.set_gige_config(old)
            except FlyCapture2Error:
                restored = None

        assert written == old
        assert restored == old


def test_hardware_gige_property_write_same_value(hardware_write_guard, hardware_config) -> None:
    _ = hardware_write_guard
    with Camera.open(index=hardware_config.camera_index) as camera:
        _require_gige_camera(camera)

        selected = None
        for property_type in (GigEPropertyType.HEARTBEAT, GigEPropertyType.HEARTBEAT_TIMEOUT):
            try:
                prop = camera.get_gige_property(property_type)
            except FlyCapture2Error:
                continue
            if prop.readable and prop.writable:
                selected = prop
                break
        if selected is None:
            pytest.skip("no readable and writable conservative GigE property is available")

        try:
            written = camera.set_gige_property(selected)
        except FlyCapture2Error as exc:
            pytest.skip(f"GigE same-value property write is not available: {exc}")
        finally:
            try:
                restored = camera.set_gige_property(selected)
            except FlyCapture2Error:
                restored = None

        assert written.property_type is selected.property_type
        assert written.value == selected.value
        assert restored is not None
        assert restored.value == selected.value


def test_hardware_gige_image_settings_write_same_value(hardware_write_guard, hardware_config) -> None:
    _ = hardware_write_guard
    with Camera.open(index=hardware_config.camera_index) as camera:
        _require_gige_camera(camera)
        try:
            old = camera.get_gige_image_settings()
        except FlyCapture2Error as exc:
            pytest.skip(f"GigE image settings readback is not available: {exc}")

        try:
            written = camera.set_gige_image_settings(old)
        except FlyCapture2Error as exc:
            pytest.skip(f"GigE same-value image settings write is not available: {exc}")
        finally:
            try:
                restored = camera.set_gige_image_settings(old)
            except FlyCapture2Error:
                restored = None

        assert written == old
        assert restored == old


def test_hardware_gige_binning_write_same_value(hardware_write_guard, hardware_config) -> None:
    _ = hardware_write_guard
    with Camera.open(index=hardware_config.camera_index) as camera:
        _require_gige_camera(camera)
        try:
            old = camera.get_gige_image_binning_settings()
        except FlyCapture2Error as exc:
            pytest.skip(f"GigE binning readback is not available: {exc}")

        try:
            written = camera.set_gige_image_binning_settings(old)
        except FlyCapture2Error as exc:
            pytest.skip(f"GigE same-value binning write is not available: {exc}")
        finally:
            try:
                restored = camera.set_gige_image_binning_settings(old)
            except FlyCapture2Error:
                restored = None

        assert written == old
        assert restored == old
