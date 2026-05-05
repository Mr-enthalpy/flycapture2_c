from __future__ import annotations

import ctypes

from flycapture2_c.api import FlyCapture2CAPI
from flycapture2_c.camera import Camera
from flycapture2_c.config import GrabMode
from flycapture2_c.ctypes_defs import (
    fc2CameraInfo,
    fc2Config,
    fc2Context,
    fc2Error,
    fc2Format7ImageSettings,
    fc2Format7Info,
    fc2Format7PacketInfo,
    fc2Image,
    fc2PGRGuid,
)
from flycapture2_c.pixel_format import PixelFormat


def _write_c_string(struct, field_name: str, value: str) -> None:
    setattr(struct, field_name, value.encode("utf-8"))


class _FakeFunction:
    argtypes = None
    restype = None

    def __call__(self, *args):
        _ = args
        return 0


class _FakeDLL:
    def __getattr__(self, name: str) -> _FakeFunction:
        function = _FakeFunction()
        setattr(self, name, function)
        return function


class Format7ConfigFakeAPI:
    def __init__(self) -> None:
        self._context = object()
        self.last_format7_settings: fc2Format7ImageSettings | None = None
        self.last_packet_size: int | None = None
        self.set_configuration_calls = 0

        self.format7_info = fc2Format7Info()
        self.format7_info.mode = 0
        self.format7_info.maxWidth = 1024
        self.format7_info.maxHeight = 768
        self.format7_info.offsetHStepSize = 4
        self.format7_info.offsetVStepSize = 2
        self.format7_info.imageHStepSize = 4
        self.format7_info.imageVStepSize = 2
        self.format7_info.pixelFormatBitField = int(PixelFormat.MONO8) | int(PixelFormat.MONO16)
        self.format7_info.packetSize = 1200
        self.format7_info.minPacketSize = 100
        self.format7_info.maxPacketSize = 2400
        self.format7_info.percentage = 50.0

        self.format7_settings = fc2Format7ImageSettings()
        self.format7_settings.mode = 0
        self.format7_settings.offsetX = 8
        self.format7_settings.offsetY = 6
        self.format7_settings.width = 640
        self.format7_settings.height = 480
        self.format7_settings.pixelFormat = int(PixelFormat.MONO16)
        self.packet_size = 1200
        self.percentage = 50.0

        self.configuration = fc2Config()
        self.configuration.numBuffers = 8
        self.configuration.numImageNotifications = 1
        self.configuration.minNumImageNotifications = 1
        self.configuration.grabTimeout = 500
        self.configuration.grabMode = int(GrabMode.DROP_FRAMES)
        self.configuration.highPerformanceRetrieveBuffer = 0
        self.configuration.bandwidthAllocation = 1

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
        _write_c_string(info, "modelName", "Format7TestCam")
        return info

    def get_format7_info(self, context, mode: int):
        assert context is self._context
        info = _copy_format7_info(self.format7_info)
        info.mode = int(mode)
        return info, True

    def validate_format7_settings(self, context, settings: fc2Format7ImageSettings):
        assert context is self._context
        packet_info = fc2Format7PacketInfo()
        packet_info.recommendedBytesPerPacket = 1600
        packet_info.maxBytesPerPacket = 2400
        packet_info.unitBytesPerPacket = 100
        return True, packet_info

    def get_format7_configuration(self, context):
        assert context is self._context
        return _copy_format7_settings(self.format7_settings), self.packet_size, self.percentage

    def set_format7_configuration_packet(
        self,
        context,
        settings: fc2Format7ImageSettings,
        packet_size: int,
    ) -> None:
        assert context is self._context
        self.last_format7_settings = _copy_format7_settings(settings)
        self.last_packet_size = int(packet_size)
        self.format7_settings = _copy_format7_settings(settings)
        self.packet_size = int(packet_size)

    def get_configuration(self, context) -> fc2Config:
        assert context is self._context
        return _copy_config(self.configuration)

    def set_configuration(self, context, config: fc2Config) -> None:
        assert context is self._context
        self.set_configuration_calls += 1
        self.configuration = _copy_config(config)


def _copy_format7_info(source: fc2Format7Info) -> fc2Format7Info:
    target = fc2Format7Info()
    for field_name, _field_type in source._fields_:
        if field_name != "reserved":
            setattr(target, field_name, getattr(source, field_name))
    return target


def _copy_format7_settings(source: fc2Format7ImageSettings) -> fc2Format7ImageSettings:
    target = fc2Format7ImageSettings()
    for field_name, _field_type in source._fields_:
        if field_name != "reserved":
            setattr(target, field_name, getattr(source, field_name))
    return target


def _copy_config(source: fc2Config) -> fc2Config:
    target = fc2Config()
    for field_name, _field_type in source._fields_:
        if field_name != "reserved":
            setattr(target, field_name, getattr(source, field_name))
    return target


def _open_camera(api: Format7ConfigFakeAPI) -> Camera:
    return Camera.open(api=api)


def test_raw_format7_and_config_function_specs_are_bound() -> None:
    dll = _FakeDLL()
    api = FlyCapture2CAPI()
    api._bind(dll)

    assert dll.fc2GetFormat7Info.argtypes == [fc2Context, ctypes.POINTER(fc2Format7Info), ctypes.POINTER(ctypes.c_int)]
    assert dll.fc2GetFormat7Info.restype is fc2Error
    assert dll.fc2ValidateFormat7Settings.argtypes == [
        fc2Context,
        ctypes.POINTER(fc2Format7ImageSettings),
        ctypes.POINTER(ctypes.c_int),
        ctypes.POINTER(fc2Format7PacketInfo),
    ]
    assert dll.fc2ValidateFormat7Settings.restype is fc2Error
    assert dll.fc2GetFormat7Configuration.argtypes == [
        fc2Context,
        ctypes.POINTER(fc2Format7ImageSettings),
        ctypes.POINTER(ctypes.c_uint32),
        ctypes.POINTER(ctypes.c_float),
    ]
    assert dll.fc2GetFormat7Configuration.restype is fc2Error
    assert dll.fc2SetFormat7ConfigurationPacket.argtypes == [
        fc2Context,
        ctypes.POINTER(fc2Format7ImageSettings),
        ctypes.c_uint32,
    ]
    assert dll.fc2SetFormat7ConfigurationPacket.restype is fc2Error
    assert dll.fc2SetFormat7Configuration.argtypes == [
        fc2Context,
        ctypes.POINTER(fc2Format7ImageSettings),
        ctypes.c_float,
    ]
    assert dll.fc2SetFormat7Configuration.restype is fc2Error
    assert dll.fc2GetConfiguration.argtypes == [fc2Context, ctypes.POINTER(fc2Config)]
    assert dll.fc2GetConfiguration.restype is fc2Error
    assert dll.fc2SetConfiguration.argtypes == [fc2Context, ctypes.POINTER(fc2Config)]
    assert dll.fc2SetConfiguration.restype is fc2Error


def test_camera_get_format7_info_and_validate_settings() -> None:
    api = Format7ConfigFakeAPI()
    camera = _open_camera(api)
    try:
        info = camera.get_format7_info(mode=0)
        validation = camera.validate_format7(mode=0, pixel_format="MONO8")
    finally:
        camera.close()

    assert info.supported
    assert info.max_width == 1024
    assert info.supports_pixel_format(PixelFormat.MONO8)
    assert validation.settings_are_valid
    assert validation.settings.width == 1024
    assert validation.settings.height == 768
    assert validation.packet_info.recommended_bytes_per_packet == 1600


def test_camera_set_format7_uses_recommended_packet_size() -> None:
    api = Format7ConfigFakeAPI()
    camera = _open_camera(api)
    try:
        result = camera.set_format7(mode=0, offset_x=0, offset_y=0, width=320, height=240, pixel_format="MONO8")
    finally:
        camera.close()

    assert result.settings.width == 320
    assert result.settings.height == 240
    assert result.settings.pixel_format == PixelFormat.MONO8
    assert api.last_packet_size == 1600


def test_camera_set_roi_preserves_current_pixel_format() -> None:
    api = Format7ConfigFakeAPI()
    camera = _open_camera(api)
    try:
        result = camera.set_roi(offset_x=0, offset_y=0, width=512, height=256, mode=0)
    finally:
        camera.close()

    assert result.settings.width == 512
    assert result.settings.height == 256
    assert result.settings.pixel_format == PixelFormat.MONO16


def test_camera_set_pixel_format_preserves_current_roi() -> None:
    api = Format7ConfigFakeAPI()
    camera = _open_camera(api)
    try:
        result = camera.set_pixel_format("MONO8", mode=0)
    finally:
        camera.close()

    assert result.settings.offset_x == 8
    assert result.settings.offset_y == 6
    assert result.settings.width == 640
    assert result.settings.height == 480
    assert result.settings.pixel_format == PixelFormat.MONO8


def test_camera_get_configuration_and_set_grab_timeout() -> None:
    api = Format7ConfigFakeAPI()
    camera = _open_camera(api)
    try:
        before = camera.get_configuration()
        after = camera.set_grab_timeout(1000)
    finally:
        camera.close()

    assert before.grab_timeout == 500
    assert after.grab_timeout == 1000
    assert after.grab_mode == GrabMode.DROP_FRAMES
    assert api.set_configuration_calls == 1
