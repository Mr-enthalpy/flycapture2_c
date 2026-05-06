from __future__ import annotations

import ctypes

import pytest

from flycapture2_c.api import FlyCapture2CAPI
from flycapture2_c.camera import Camera
from flycapture2_c.ctypes_defs import fc2CameraInfo, fc2Context, fc2Image, fc2PGRGuid
from flycapture2_c.errors import CameraStateError, FlyCapture2NotSupportedError, GigEConfigurationError
from flycapture2_c.gige import (
    GigEConfig,
    GigEImageBinningSettings,
    GigEImageSettings,
    GigEImageSettingsInfo,
    GigEProperty,
    GigEPropertyType,
    GigEStreamChannelInfo,
)
from flycapture2_c.pixel_format import PixelFormat
from flycapture2_c.raw.structs import (
    fc2GigEConfig,
    fc2GigEImageSettings,
    fc2GigEImageSettingsInfo,
    fc2GigEProperty,
    fc2GigEStreamChannel,
)


def _copy_struct(source, struct_type):
    target = struct_type()
    ctypes.memmove(ctypes.byref(target), ctypes.byref(source), ctypes.sizeof(target))
    return target


class _FakeFunction:
    def __init__(self, callback=None) -> None:
        self.callback = callback

    def __call__(self, *args):
        if self.callback is not None:
            return self.callback(*args)
        return 0


class _RawGigEDLL:
    def __init__(self) -> None:
        self.config = fc2GigEConfig()
        self.config.enablePacketResend = 1
        self.config.registerTimeoutRetries = 2
        self.config.registerTimeout = 3000
        self.fc2GetGigEConfig = _FakeFunction(self._get_config)
        self.fc2SetGigEConfig = _FakeFunction(self._set_config)

    def _get_config(self, context, config_ptr) -> int:
        _ = context
        ctypes.memmove(config_ptr, ctypes.byref(self.config), ctypes.sizeof(self.config))
        return 0

    def _set_config(self, context, config_ptr) -> int:
        _ = context
        self.config = _copy_struct(config_ptr._obj, fc2GigEConfig)
        return 0


class GigEFakeAPI:
    def __init__(self) -> None:
        self._context = object()
        self.config = fc2GigEConfig()
        self.config.enablePacketResend = 1
        self.config.registerTimeoutRetries = 1
        self.config.registerTimeout = 2000
        self.property = fc2GigEProperty()
        self.property.propType = int(GigEPropertyType.PACKET_SIZE)
        self.property.isReadable = 1
        self.property.isWritable = 1
        self.property.min = 576
        self.property.max = 9000
        self.property.value = 1500
        self.imaging_mode = 0
        self.settings_info = fc2GigEImageSettingsInfo()
        self.settings_info.maxWidth = 1920
        self.settings_info.maxHeight = 1200
        self.settings_info.offsetHStepSize = 4
        self.settings_info.offsetVStepSize = 2
        self.settings_info.imageHStepSize = 4
        self.settings_info.imageVStepSize = 2
        self.settings_info.pixelFormatBitField = int(PixelFormat.MONO8) | int(PixelFormat.MONO16)
        self.settings = fc2GigEImageSettings()
        self.settings.offsetX = 0
        self.settings.offsetY = 0
        self.settings.width = 640
        self.settings.height = 480
        self.settings.pixelFormat = int(PixelFormat.MONO8)
        self.binning = (1, 1)
        self.stream_channel = fc2GigEStreamChannel()
        self.stream_channel.networkInterfaceIndex = 3
        self.stream_channel.hostPort = 50000
        self.stream_channel.doNotFragment = 1
        self.stream_channel.packetSize = 1500
        self.stream_channel.interPacketDelay = 0
        self.stream_channel.destinationIpAddress.octets[:] = [192, 168, 1, 10]
        self.stream_channel.sourcePort = 49152

    def create_context(self):
        return self._context

    def destroy_context(self, context) -> None:
        assert context is self._context

    def get_num_cameras(self, context) -> int:
        assert context is self._context
        return 1

    def get_camera_from_index(self, context, index: int) -> fc2PGRGuid:
        assert context is self._context
        assert index == 0
        guid = fc2PGRGuid()
        guid.value[:] = [1, 2, 3, 4]
        return guid

    def connect(self, context, guid) -> None:
        assert context is self._context
        _ = guid

    def disconnect(self, context) -> None:
        assert context is self._context

    def create_image(self) -> fc2Image:
        return fc2Image()

    def destroy_image(self, image: fc2Image) -> None:
        _ = image

    def get_camera_info(self, context) -> fc2CameraInfo:
        assert context is self._context
        info = fc2CameraInfo()
        info.interfaceType = 3
        return info

    def get_gige_config(self, context) -> fc2GigEConfig:
        assert context is self._context
        return _copy_struct(self.config, fc2GigEConfig)

    def set_gige_config(self, context, config: fc2GigEConfig) -> None:
        assert context is self._context
        self.config = _copy_struct(config, fc2GigEConfig)

    def get_gige_property(self, context, property_type: int) -> fc2GigEProperty:
        assert context is self._context
        prop = _copy_struct(self.property, fc2GigEProperty)
        prop.propType = int(property_type)
        return prop

    def set_gige_property(self, context, prop: fc2GigEProperty) -> None:
        assert context is self._context
        self.property = _copy_struct(prop, fc2GigEProperty)

    def discover_gige_packet_size(self, context) -> int:
        assert context is self._context
        return 9000

    def query_gige_imaging_mode(self, context, mode: int) -> bool:
        assert context is self._context
        return int(mode) in {0, 1}

    def get_gige_imaging_mode(self, context) -> int:
        assert context is self._context
        return self.imaging_mode

    def set_gige_imaging_mode(self, context, mode: int) -> None:
        assert context is self._context
        self.imaging_mode = int(mode)

    def get_gige_image_settings_info(self, context) -> fc2GigEImageSettingsInfo:
        assert context is self._context
        return _copy_struct(self.settings_info, fc2GigEImageSettingsInfo)

    def get_gige_image_settings(self, context) -> fc2GigEImageSettings:
        assert context is self._context
        return _copy_struct(self.settings, fc2GigEImageSettings)

    def set_gige_image_settings(self, context, settings: fc2GigEImageSettings) -> None:
        assert context is self._context
        self.settings = _copy_struct(settings, fc2GigEImageSettings)

    def get_gige_image_binning_settings(self, context) -> tuple[int, int]:
        assert context is self._context
        return self.binning

    def set_gige_image_binning_settings(self, context, horizontal: int, vertical: int) -> None:
        assert context is self._context
        self.binning = (int(horizontal), int(vertical))

    def get_num_gige_stream_channels(self, context) -> int:
        assert context is self._context
        return 1

    def get_gige_stream_channel_info(self, context, channel: int) -> fc2GigEStreamChannel:
        assert context is self._context
        assert int(channel) == 0
        return _copy_struct(self.stream_channel, fc2GigEStreamChannel)


def _open_camera(api: GigEFakeAPI) -> Camera:
    return Camera.open(api=api)


def test_gige_dataclass_conversions() -> None:
    api = GigEFakeAPI()

    config = GigEConfig.from_c(api.config)
    prop = GigEProperty.from_c(api.property)
    info = GigEImageSettingsInfo.from_c(api.settings_info)
    settings = GigEImageSettings.from_c(api.settings)
    binning = GigEImageBinningSettings(horizontal=1, vertical=2)
    channel = GigEStreamChannelInfo.from_c(api.stream_channel)

    assert config.enable_packet_resend is True
    assert config.to_c().registerTimeout == 2000
    assert prop.property_type is GigEPropertyType.PACKET_SIZE
    assert prop.to_c().value == 1500
    assert info.supports_pixel_format(PixelFormat.MONO8)
    assert settings.pixel_format is PixelFormat.MONO8
    assert settings.to_c().width == 640
    assert binning.with_updates(vertical=4).vertical == 4
    assert channel.destination_ip_address == (192, 168, 1, 10)
    assert channel.to_c().destinationIpAddress.octets[3] == 10


def test_camera_gige_methods_with_fake_api() -> None:
    api = GigEFakeAPI()
    camera = _open_camera(api)
    try:
        assert camera.get_camera_info().interface_type == 3
        assert camera.get_gige_config().register_timeout == 2000
        assert camera.set_gige_config(register_timeout=4000).register_timeout == 4000
        assert camera.get_gige_property("packet_size").value == 1500
        assert camera.set_gige_property(GigEPropertyType.PACKET_SIZE, value=1600).value == 1600
        assert camera.discover_gige_packet_size() == 9000
        assert camera.query_gige_imaging_mode(1) is True
        assert camera.set_gige_imaging_mode(1) == 1
        assert camera.get_gige_image_settings_info().max_width == 1920
        assert camera.set_gige_image_settings(width=800).width == 800
        assert camera.get_gige_image_binning_settings() == GigEImageBinningSettings(horizontal=1, vertical=1)
        assert camera.set_gige_image_binning_settings(vertical=2).vertical == 2
        assert camera.get_num_gige_stream_channels() == 1
        assert camera.get_gige_stream_channel_info(0).packet_size == 1500
    finally:
        camera.close()


def test_camera_gige_methods_require_open_camera() -> None:
    camera = Camera(api=GigEFakeAPI())

    with pytest.raises(CameraStateError):
        camera.get_gige_config()


def test_gige_property_write_validation() -> None:
    api = GigEFakeAPI()
    camera = _open_camera(api)
    try:
        with pytest.raises(GigEConfigurationError):
            camera.set_gige_property(GigEPropertyType.PACKET_SIZE, value=100)
        api.property.isWritable = 0
        with pytest.raises(GigEConfigurationError):
            camera.set_gige_property(GigEPropertyType.PACKET_SIZE, value=1600)
    finally:
        camera.close()


def test_flycapture2capi_gige_config_wrapper_checks_sdk_call() -> None:
    dll = _RawGigEDLL()
    api = FlyCapture2CAPI()
    api._dll = dll  # type: ignore[assignment]

    assert GigEConfig.from_c(api.get_gige_config(fc2Context())).register_timeout == 3000
    api.set_gige_config(fc2Context(), GigEConfig(False, 3, 4000).to_c())
    assert dll.config.registerTimeout == 4000


def test_flycapture2capi_missing_optional_gige_symbol_raises_not_supported() -> None:
    class MissingGigEDLL:
        def __getattr__(self, name: str):
            if name == "fc2GetGigEConfig":
                raise AttributeError(name)
            return _FakeFunction()

    api = FlyCapture2CAPI()
    api._dll = MissingGigEDLL()  # type: ignore[assignment]

    with pytest.raises(FlyCapture2NotSupportedError, match="fc2GetGigEConfig"):
        api.get_gige_config(fc2Context())
