from __future__ import annotations

from flycapture2_c.camera import Camera
from flycapture2_c.ctypes_defs import fc2CameraInfo, fc2Image, fc2PGRGuid, fc2Property, fc2PropertyInfo
from flycapture2_c.properties import PropertyType


def _write_c_string(struct, field_name: str, value: str) -> None:
    setattr(struct, field_name, value.encode("utf-8"))


class FakeAPI:
    def __init__(self) -> None:
        self._context = object()
        self._connected = False
        self._property = fc2Property()
        self._property.type = int(PropertyType.GAIN)
        self._property.present = 1
        self._property.absControl = 1
        self._property.onOff = 1
        self._property.autoManualMode = 0
        self._property.valueA = 12
        self._property.absValue = 6.5

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
        self._connected = True

    def disconnect(self, context) -> None:
        assert context is self._context
        self._connected = False

    def create_image(self) -> fc2Image:
        return fc2Image()

    def destroy_image(self, image: fc2Image) -> None:
        _ = image

    def get_camera_info(self, context) -> fc2CameraInfo:
        assert context is self._context
        info = fc2CameraInfo()
        info.serialNumber = 123456
        info.interfaceType = 2
        info.driverType = 1
        info.isColorCamera = 0
        _write_c_string(info, "modelName", "BFLY")
        _write_c_string(info, "vendorName", "FLIR")
        _write_c_string(info, "sensorInfo", "Sony IMX")
        _write_c_string(info, "sensorResolution", "1920x1200")
        _write_c_string(info, "driverName", "PGRUSBCamera")
        _write_c_string(info, "firmwareVersion", "2.0.0")
        _write_c_string(info, "firmwareBuildTime", "2026-05-05")
        _write_c_string(info.configROM, "pszKeyword", "IIDC")
        info.macAddress.octets[:] = [0, 1, 2, 3, 4, 5]
        info.ipAddress.octets[:] = [192, 168, 0, 2]
        info.subnetMask.octets[:] = [255, 255, 255, 0]
        info.defaultGateway.octets[:] = [192, 168, 0, 1]
        return info

    def get_property_info(self, context, property_type: int) -> fc2PropertyInfo:
        assert context is self._context
        assert property_type == int(PropertyType.GAIN)
        info = fc2PropertyInfo()
        info.type = property_type
        info.present = 1
        info.autoSupported = 1
        info.manualSupported = 1
        info.onOffSupported = 1
        info.onePushSupported = 0
        info.absValSupported = 1
        info.readOutSupported = 1
        info.min = 0
        info.max = 24
        info.absMin = 0.0
        info.absMax = 24.0
        _write_c_string(info, "pUnits", "decibels")
        _write_c_string(info, "pUnitAbbr", "dB")
        return info

    def get_property(self, context, property_type: int) -> fc2Property:
        assert context is self._context
        assert property_type == int(PropertyType.GAIN)
        prop = fc2Property()
        prop.type = self._property.type
        prop.present = self._property.present
        prop.absControl = self._property.absControl
        prop.onePush = self._property.onePush
        prop.onOff = self._property.onOff
        prop.autoManualMode = self._property.autoManualMode
        prop.valueA = self._property.valueA
        prop.valueB = self._property.valueB
        prop.absValue = self._property.absValue
        return prop

    def set_property(self, context, prop: fc2Property) -> None:
        assert context is self._context
        self._property.type = prop.type
        self._property.present = prop.present
        self._property.absControl = prop.absControl
        self._property.onePush = prop.onePush
        self._property.onOff = prop.onOff
        self._property.autoManualMode = prop.autoManualMode
        self._property.valueA = prop.valueA
        self._property.valueB = prop.valueB
        self._property.absValue = prop.absValue

    def get_video_mode_and_frame_rate(self, context) -> tuple[int, int]:
        assert context is self._context
        return (22, 4)

    def start_capture(self, context) -> None:
        assert context is self._context

    def stop_capture(self, context) -> None:
        assert context is self._context


def test_camera_open_populates_camera_info_from_fake_api() -> None:
    camera = Camera.open(api=FakeAPI())
    try:
        info = camera.get_camera_info()
        assert info.serial_number == 123456
        assert info.model_name == "BFLY"
        assert info.vendor_name == "FLIR"
        assert info.ip_address == (192, 168, 0, 2)
        assert camera.descriptor is not None
        assert camera.descriptor.guid == (1, 2, 3, 4)
    finally:
        camera.close()


def test_camera_property_round_trip_with_fake_api() -> None:
    camera = Camera.open(api=FakeAPI())
    try:
        info = camera.get_property_info(PropertyType.GAIN)
        assert info.present is True
        assert info.abs_val_supported is True
        value = camera.get_property("gain")
        assert value.abs_value == 6.5

        updated = camera.set_property(PropertyType.GAIN, abs_value=7.25, auto_manual_mode=False)
        assert updated.abs_control is True
        assert updated.abs_value == 7.25
        assert camera.get_video_mode_and_frame_rate() == (22, 4)
    finally:
        camera.close()
