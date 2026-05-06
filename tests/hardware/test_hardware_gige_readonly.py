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


def test_hardware_gige_readonly_queries(hardware_guard, hardware_config) -> None:
    _ = hardware_guard
    with Camera.open(index=hardware_config.camera_index) as camera:
        _require_gige_camera(camera)

        try:
            config = camera.get_gige_config()
        except FlyCapture2Error as exc:
            pytest.skip(f"GigE config readback is not available: {exc}")
        assert config.register_timeout >= 0

        try:
            settings_info = camera.get_gige_image_settings_info()
            settings = camera.get_gige_image_settings()
        except FlyCapture2Error as exc:
            pytest.skip(f"GigE image settings readback is not available: {exc}")
        assert settings_info.max_width >= settings.width
        assert settings_info.max_height >= settings.height

        try:
            channels = camera.get_num_gige_stream_channels()
        except FlyCapture2Error as exc:
            pytest.skip(f"GigE stream channel count is not available: {exc}")
        assert channels >= 0
        if channels:
            channel = camera.get_gige_stream_channel_info(0)
            assert channel.packet_size >= 0

        for property_type in GigEPropertyType:
            try:
                prop = camera.get_gige_property(property_type)
            except FlyCapture2Error:
                continue
            assert prop.property_type is property_type
            if prop.readable:
                assert prop.min_value <= prop.value <= prop.max_value


def test_hardware_gige_optional_readonly_helpers(hardware_guard, hardware_config) -> None:
    _ = hardware_guard
    with Camera.open(index=hardware_config.camera_index) as camera:
        _require_gige_camera(camera)

        try:
            mode = camera.get_gige_imaging_mode()
        except FlyCapture2Error as exc:
            pytest.skip(f"GigE imaging mode readback is not available: {exc}")

        try:
            assert isinstance(camera.query_gige_imaging_mode(mode), bool)
        except FlyCapture2Error as exc:
            pytest.skip(f"GigE imaging mode query is not available: {exc}")

        try:
            packet_size = camera.discover_gige_packet_size()
        except FlyCapture2Error:
            packet_size = None
        if packet_size is not None:
            assert packet_size > 0
