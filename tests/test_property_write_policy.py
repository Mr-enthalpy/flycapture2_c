from __future__ import annotations

from flycapture2_c.camera import Camera
from flycapture2_c.ctypes_defs import fc2CameraInfo, fc2Image, fc2PGRGuid, fc2Property, fc2PropertyInfo
from flycapture2_c.errors import (
    PropertyModeError,
    PropertyNotWritableError,
    PropertyOutOfRangeError,
    UnsupportedPropertyError,
)
from flycapture2_c.properties import PropertyType, PropertyWritePolicy


def _write_c_string(struct, field_name: str, value: str) -> None:
    setattr(struct, field_name, value.encode("utf-8"))


class PropertyPolicyFakeAPI:
    def __init__(self) -> None:
        self._context = object()
        self.set_property_calls = 0
        self.last_written_property: fc2Property | None = None
        self._info_by_type: dict[int, fc2PropertyInfo] = {}
        self._value_by_type: dict[int, fc2Property] = {}

        for property_type in (
            PropertyType.AUTO_EXPOSURE,
            PropertyType.SHUTTER,
            PropertyType.GAIN,
            PropertyType.FRAME_RATE,
            PropertyType.BRIGHTNESS,
        ):
            info = fc2PropertyInfo()
            info.type = int(property_type)
            info.present = 1
            info.autoSupported = 1
            info.manualSupported = 1
            info.onOffSupported = 1
            info.onePushSupported = 0
            info.absValSupported = 1
            info.readOutSupported = 1
            info.min = 0
            info.max = 100
            info.absMin = 0.0
            info.absMax = 100.0
            _write_c_string(info, "pUnits", "unit")
            _write_c_string(info, "pUnitAbbr", "u")
            self._info_by_type[int(property_type)] = info

            prop = fc2Property()
            prop.type = int(property_type)
            prop.present = 1
            prop.absControl = 1
            prop.onOff = 1
            prop.autoManualMode = 0
            prop.absValue = 10.0
            self._value_by_type[int(property_type)] = prop

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

    def disconnect(self, context) -> None:
        assert context is self._context

    def create_image(self) -> fc2Image:
        return fc2Image()

    def destroy_image(self, image: fc2Image) -> None:
        _ = image

    def get_camera_info(self, context) -> fc2CameraInfo:
        assert context is self._context
        info = fc2CameraInfo()
        _write_c_string(info, "modelName", "TestCam")
        return info

    def get_property_info(self, context, property_type: int) -> fc2PropertyInfo:
        assert context is self._context
        return self._info_by_type[property_type]

    def get_property(self, context, property_type: int) -> fc2Property:
        assert context is self._context
        source = self._value_by_type[property_type]
        prop = fc2Property()
        prop.type = source.type
        prop.present = source.present
        prop.absControl = source.absControl
        prop.onePush = source.onePush
        prop.onOff = source.onOff
        prop.autoManualMode = source.autoManualMode
        prop.valueA = source.valueA
        prop.valueB = source.valueB
        prop.absValue = source.absValue
        return prop

    def set_property(self, context, prop: fc2Property) -> None:
        assert context is self._context
        self.set_property_calls += 1
        written = fc2Property()
        written.type = prop.type
        written.present = prop.present
        written.absControl = prop.absControl
        written.onePush = prop.onePush
        written.onOff = prop.onOff
        written.autoManualMode = prop.autoManualMode
        written.valueA = prop.valueA
        written.valueB = prop.valueB
        written.absValue = prop.absValue
        self.last_written_property = written
        self._value_by_type[int(prop.type)] = written

    def get_video_mode_and_frame_rate(self, context) -> tuple[int, int]:
        assert context is self._context
        return (0, 0)

    def start_capture(self, context) -> None:
        assert context is self._context

    def stop_capture(self, context) -> None:
        assert context is self._context


def _open_camera(api: PropertyPolicyFakeAPI) -> Camera:
    return Camera.open(api=api)


def test_high_level_write_fails_when_property_not_present() -> None:
    api = PropertyPolicyFakeAPI()
    api._info_by_type[int(PropertyType.GAIN)].present = 0
    camera = _open_camera(api)
    try:
        try:
            camera.set_gain(5.0)
            assert False, "expected UnsupportedPropertyError"
        except UnsupportedPropertyError:
            pass
        assert api.set_property_calls == 0
    finally:
        camera.close()


def test_high_level_write_fails_when_property_present_but_not_writable() -> None:
    api = PropertyPolicyFakeAPI()
    info = api._info_by_type[int(PropertyType.SHUTTER)]
    info.manualSupported = 0
    info.autoSupported = 0
    info.onOffSupported = 0
    info.onePushSupported = 0
    info.absValSupported = 0
    camera = _open_camera(api)
    try:
        try:
            camera.set_shutter(2.0)
            assert False, "expected PropertyNotWritableError"
        except PropertyNotWritableError:
            pass
        assert api.set_property_calls == 0
    finally:
        camera.close()


def test_high_level_write_fails_when_value_out_of_range() -> None:
    api = PropertyPolicyFakeAPI()
    info = api._info_by_type[int(PropertyType.FRAME_RATE)]
    info.absMin = 1.0
    info.absMax = 30.0
    camera = _open_camera(api)
    try:
        try:
            camera.set_frame_rate(120.0)
            assert False, "expected PropertyOutOfRangeError"
        except PropertyOutOfRangeError:
            pass
        assert api.set_property_calls == 0
    finally:
        camera.close()


def test_high_level_write_fails_when_absolute_control_not_supported() -> None:
    api = PropertyPolicyFakeAPI()
    api._info_by_type[int(PropertyType.AUTO_EXPOSURE)].absValSupported = 0
    camera = _open_camera(api)
    try:
        try:
            camera.set_exposure(10.0)
            assert False, "expected PropertyModeError"
        except PropertyModeError:
            pass
        assert api.set_property_calls == 0
    finally:
        camera.close()


def test_strict_low_level_policy_does_not_call_sdk_write_on_failure() -> None:
    api = PropertyPolicyFakeAPI()
    api._info_by_type[int(PropertyType.GAIN)].absMax = 5.0
    camera = _open_camera(api)
    try:
        try:
            camera.set_property(PropertyType.GAIN, abs_value=6.0, policy=PropertyWritePolicy.STRICT)
            assert False, "expected PropertyOutOfRangeError"
        except PropertyOutOfRangeError:
            pass
        assert api.set_property_calls == 0
    finally:
        camera.close()


def test_high_level_write_constructs_expected_property_and_calls_sdk_write() -> None:
    api = PropertyPolicyFakeAPI()
    camera = _open_camera(api)
    try:
        result = camera.set_gain(7.25, auto=False)
        assert result.abs_value == 7.25
        assert api.set_property_calls == 1
        assert api.last_written_property is not None
        assert api.last_written_property.type == int(PropertyType.GAIN)
        assert api.last_written_property.absControl == 1
        assert api.last_written_property.autoManualMode == 0
        assert api.last_written_property.absValue == 7.25
    finally:
        camera.close()


def test_unsupported_property_is_blocked_by_high_level_write_api() -> None:
    api = PropertyPolicyFakeAPI()
    camera = _open_camera(api)
    try:
        try:
            camera._set_supported_absolute_property(PropertyType.BRIGHTNESS, 3.0, auto=False)
            assert False, "expected UnsupportedPropertyError"
        except UnsupportedPropertyError:
            pass
        assert api.set_property_calls == 0
    finally:
        camera.close()


def test_raw_policy_remains_available_for_advanced_low_level_calls() -> None:
    api = PropertyPolicyFakeAPI()
    api._info_by_type[int(PropertyType.BRIGHTNESS)].absValSupported = 0
    camera = _open_camera(api)
    try:
        camera.set_property(
            PropertyType.BRIGHTNESS,
            value_a=11,
            abs_control=False,
            policy=PropertyWritePolicy.RAW,
        )
        assert api.set_property_calls == 1
        assert api.last_written_property is not None
        assert api.last_written_property.type == int(PropertyType.BRIGHTNESS)
        assert api.last_written_property.valueA == 11
    finally:
        camera.close()
