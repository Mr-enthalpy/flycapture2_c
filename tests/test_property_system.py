from __future__ import annotations

from flycapture2_c.camera import Camera
from flycapture2_c.ctypes_defs import fc2CameraInfo, fc2Image, fc2PGRGuid, fc2Property, fc2PropertyInfo
from flycapture2_c.errors import PropertyModeError, PropertyOutOfRangeError
from flycapture2_c.properties import (
    KNOWN_PROPERTY_TYPES,
    CameraPropertySnapshot,
    PropertyType,
    get_property_display_range,
    get_property_display_value,
    normalize_property_type,
)


def _write_c_string(struct, field_name: str, value: str) -> None:
    setattr(struct, field_name, value.encode("utf-8"))


class PropertySystemFakeAPI:
    def __init__(self) -> None:
        self._context = object()
        self.set_property_calls = 0
        self.last_written_property: fc2Property | None = None
        self._info_by_type: dict[int, fc2PropertyInfo] = {}
        self._value_by_type: dict[int, fc2Property] = {}

        for property_type in KNOWN_PROPERTY_TYPES:
            info = fc2PropertyInfo()
            info.type = int(property_type)
            info.present = 1
            info.autoSupported = 1
            info.manualSupported = 1
            info.onOffSupported = 1
            info.onePushSupported = 1
            info.absValSupported = 1
            info.readOutSupported = 1
            info.min = 0
            info.max = 1023
            info.absMin = 0.0
            info.absMax = 100.0
            _write_c_string(info, "pUnits", "unit")
            _write_c_string(info, "pUnitAbbr", "u")
            self._info_by_type[int(property_type)] = info

            value = fc2Property()
            value.type = int(property_type)
            value.present = 1
            value.absControl = 1
            value.onePush = 0
            value.onOff = 1
            value.autoManualMode = 0
            value.valueA = 10
            value.valueB = 20
            value.absValue = 5.0
            self._value_by_type[int(property_type)] = value

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
        _write_c_string(info, "modelName", "PropertySystemCam")
        return info

    def get_property_info(self, context, property_type: int) -> fc2PropertyInfo:
        assert context is self._context
        return self._info_by_type[property_type]

    def get_property(self, context, property_type: int) -> fc2Property:
        assert context is self._context
        return _copy_property(self._value_by_type[property_type])

    def set_property(self, context, prop: fc2Property) -> None:
        assert context is self._context
        self.set_property_calls += 1
        written = _copy_property(prop)
        self.last_written_property = written
        self._value_by_type[int(prop.type)] = written


def _copy_property(source: fc2Property) -> fc2Property:
    target = fc2Property()
    target.type = source.type
    target.present = source.present
    target.absControl = source.absControl
    target.onePush = source.onePush
    target.onOff = source.onOff
    target.autoManualMode = source.autoManualMode
    target.valueA = source.valueA
    target.valueB = source.valueB
    target.absValue = source.absValue
    return target


def _open_camera(api: PropertySystemFakeAPI) -> Camera:
    return Camera.open(api=api)


def test_normalize_property_type_covers_all_names_and_values() -> None:
    for property_type in PropertyType:
        assert normalize_property_type(property_type.name) == property_type
        assert normalize_property_type(property_type.name.lower()) == property_type
        assert normalize_property_type(int(property_type)) == property_type


def test_set_property_abs_validates_and_writes_absolute_value() -> None:
    api = PropertySystemFakeAPI()
    camera = _open_camera(api)
    try:
        result = camera.set_property_abs(PropertyType.SHUTTER, 7.5, auto=False)
    finally:
        camera.close()

    assert result.abs_value == 7.5
    assert api.last_written_property is not None
    assert api.last_written_property.type == int(PropertyType.SHUTTER)
    assert api.last_written_property.absControl == 1
    assert api.last_written_property.autoManualMode == 0
    assert api.last_written_property.onOff == 1


def test_set_property_abs_rejects_out_of_range_value_before_write() -> None:
    api = PropertySystemFakeAPI()
    camera = _open_camera(api)
    try:
        try:
            camera.set_property_abs(PropertyType.GAIN, 101.0)
            assert False, "expected PropertyOutOfRangeError"
        except PropertyOutOfRangeError:
            pass
    finally:
        camera.close()

    assert api.set_property_calls == 0


def test_set_property_integer_validates_and_writes_values() -> None:
    api = PropertySystemFakeAPI()
    camera = _open_camera(api)
    try:
        result = camera.set_property_integer(PropertyType.WHITE_BALANCE, value_a=100, value_b=200, auto=False)
    finally:
        camera.close()

    assert result.value_a == 100
    assert result.value_b == 200
    assert api.last_written_property is not None
    assert api.last_written_property.absControl == 0
    assert api.last_written_property.type == int(PropertyType.WHITE_BALANCE)


def test_set_property_integer_rejects_out_of_range_value_before_write() -> None:
    api = PropertySystemFakeAPI()
    camera = _open_camera(api)
    try:
        try:
            camera.set_property_integer(PropertyType.WHITE_BALANCE, value_a=2048)
            assert False, "expected PropertyOutOfRangeError"
        except PropertyOutOfRangeError:
            pass
    finally:
        camera.close()

    assert api.set_property_calls == 0


def test_set_property_on_off_auto_and_one_push() -> None:
    api = PropertySystemFakeAPI()
    camera = _open_camera(api)
    try:
        off_result = camera.set_property_on_off(PropertyType.BRIGHTNESS, on=False)
        auto_result = camera.set_property_auto(PropertyType.BRIGHTNESS, auto=True)
        one_push_result = camera.set_property_one_push(PropertyType.BRIGHTNESS)
    finally:
        camera.close()

    assert off_result.on_off is False
    assert auto_result.auto_manual_mode is True
    assert one_push_result.one_push is True
    assert api.set_property_calls == 3


def test_set_property_on_off_rejects_unsupported_mode() -> None:
    api = PropertySystemFakeAPI()
    api._info_by_type[int(PropertyType.GAMMA)].onOffSupported = 0
    camera = _open_camera(api)
    try:
        try:
            camera.set_property_on_off(PropertyType.GAMMA, on=False)
            assert False, "expected PropertyModeError"
        except PropertyModeError:
            pass
    finally:
        camera.close()

    assert api.set_property_calls == 0


def test_property_discovery_helpers_return_dataclasses() -> None:
    api = PropertySystemFakeAPI()
    api._info_by_type[int(PropertyType.TEMPERATURE)].present = 0
    camera = _open_camera(api)
    try:
        infos = camera.list_property_infos()
        values = camera.list_properties()
        snapshots = camera.snapshot_properties()
    finally:
        camera.close()

    assert len(infos) == len(KNOWN_PROPERTY_TYPES)
    assert len(values) == len(KNOWN_PROPERTY_TYPES) - 1
    assert len(snapshots) == len(KNOWN_PROPERTY_TYPES)
    assert all(isinstance(item, CameraPropertySnapshot) for item in snapshots)
    temperature = next(item for item in snapshots if item.property_type == PropertyType.TEMPERATURE)
    assert temperature.info is not None
    assert temperature.info.present is False
    assert temperature.value is None


def test_property_display_value_prefers_absolute_readback_even_when_abs_control_is_off() -> None:
    api = PropertySystemFakeAPI()
    frame_rate_type = int(PropertyType.FRAME_RATE)
    api._info_by_type[frame_rate_type].min = 1
    api._info_by_type[frame_rate_type].max = 4095
    api._info_by_type[frame_rate_type].absMin = 1.0
    api._info_by_type[frame_rate_type].absMax = 75.47
    _write_c_string(api._info_by_type[frame_rate_type], "pUnits", "frames per second")
    _write_c_string(api._info_by_type[frame_rate_type], "pUnitAbbr", "fps")
    api._value_by_type[frame_rate_type].absControl = 0
    api._value_by_type[frame_rate_type].valueA = 1811
    api._value_by_type[frame_rate_type].absValue = 20.0

    camera = _open_camera(api)
    try:
        info = camera.get_property_info(PropertyType.FRAME_RATE)
        value = camera.get_property(PropertyType.FRAME_RATE)
        snapshot = next(item for item in camera.snapshot_properties() if item.property_type == PropertyType.FRAME_RATE)
        display_value = camera.get_property_display_value(PropertyType.FRAME_RATE)
        display_range = camera.get_property_display_range(PropertyType.FRAME_RATE)
        abs_readback = camera.get_property_abs_readback(PropertyType.FRAME_RATE)
    finally:
        camera.close()

    assert value.abs_control is False
    assert value.value_a == 1811
    assert value.abs_value == 20.0
    assert get_property_display_value(info, value) == 20.0
    assert get_property_display_range(info) == (1.0, 75.47000122070312)
    assert display_value == 20.0
    assert display_range == (1.0, 75.47000122070312)
    assert abs_readback == 20.0
    assert snapshot.display_value == 20.0
    assert snapshot.display_range == (1.0, 75.47000122070312)


def test_property_display_value_falls_back_to_raw_value_when_absolute_values_are_unsupported() -> None:
    api = PropertySystemFakeAPI()
    sharpness_type = int(PropertyType.SHARPNESS)
    api._info_by_type[sharpness_type].absValSupported = 0
    api._info_by_type[sharpness_type].min = 0
    api._info_by_type[sharpness_type].max = 4095
    api._value_by_type[sharpness_type].valueA = 1811
    api._value_by_type[sharpness_type].absValue = 0.0

    camera = _open_camera(api)
    try:
        info = camera.get_property_info(PropertyType.SHARPNESS)
        value = camera.get_property(PropertyType.SHARPNESS)
        display_value = camera.get_property_display_value(PropertyType.SHARPNESS)
        display_range = camera.get_property_display_range(PropertyType.SHARPNESS)
        abs_readback = camera.get_property_abs_readback(PropertyType.SHARPNESS)
    finally:
        camera.close()

    assert get_property_display_value(info, value) == 1811
    assert get_property_display_range(info) == (0, 4095)
    assert display_value == 1811
    assert display_range == (0, 4095)
    assert abs_readback is None


def test_new_convenience_methods_delegate_to_generic_property_api() -> None:
    api = PropertySystemFakeAPI()
    camera = _open_camera(api)
    try:
        brightness = camera.set_brightness(12.5)
        gamma = camera.set_gamma(1.25)
        white_balance = camera.set_white_balance(320, 640)
        trigger_delay = camera.set_trigger_delay(2.5)
        temperature = camera.get_temperature()
    finally:
        camera.close()

    assert brightness.property_type == PropertyType.BRIGHTNESS
    assert gamma.property_type == PropertyType.GAMMA
    assert white_balance.property_type == PropertyType.WHITE_BALANCE
    assert white_balance.value_a == 320
    assert white_balance.value_b == 640
    assert trigger_delay.property_type == PropertyType.TRIGGER_DELAY
    assert temperature.property_type == PropertyType.TEMPERATURE
