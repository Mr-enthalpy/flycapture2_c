from __future__ import annotations

import ctypes

import pytest

from flycapture2_c.camera import Camera
from flycapture2_c.ctypes_defs import fc2CameraInfo, fc2Image, fc2PGRGuid
from flycapture2_c.errors import GPIOConfigurationError, StrobeConfigurationError, UnsupportedStrobeError
from flycapture2_c.raw.structs import fc2StrobeControl, fc2StrobeInfo
from flycapture2_c.strobe import StrobeControl, StrobeInfo, normalize_gpio_direction, normalize_gpio_pin


class StrobeFakeAPI:
    def __init__(self) -> None:
        self._context = object()
        self.info = fc2StrobeInfo()
        self.info.source = 0
        self.info.present = 1
        self.info.readOutSupported = 1
        self.info.onOffSupported = 1
        self.info.polaritySupported = 1
        self.info.minValue = 0.0
        self.info.maxValue = 10.0
        self.control = fc2StrobeControl()
        self.control.source = 0
        self.control.onOff = 0
        self.control.polarity = 0
        self.control.delay = 0.0
        self.control.duration = 1.0
        self.last_strobe_broadcast = False
        self.gpio_direction = 0
        self.last_gpio_broadcast = False

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
        return fc2CameraInfo()

    def get_strobe_info(self, context, source: int) -> fc2StrobeInfo:
        assert context is self._context
        info = fc2StrobeInfo()
        ctypes.memmove(ctypes.byref(info), ctypes.byref(self.info), ctypes.sizeof(info))
        info.source = int(source)
        return info

    def get_strobe(self, context, source: int) -> fc2StrobeControl:
        assert context is self._context
        control = fc2StrobeControl()
        ctypes.memmove(ctypes.byref(control), ctypes.byref(self.control), ctypes.sizeof(control))
        control.source = int(source)
        return control

    def set_strobe(self, context, control: fc2StrobeControl, *, broadcast: bool = False) -> None:
        assert context is self._context
        self.last_strobe_broadcast = broadcast
        ctypes.memmove(ctypes.byref(self.control), ctypes.byref(control), ctypes.sizeof(control))

    def get_gpio_pin_direction(self, context, pin: int) -> int:
        assert context is self._context
        assert pin == 0
        return self.gpio_direction

    def set_gpio_pin_direction(self, context, pin: int, direction: int, *, broadcast: bool = False) -> None:
        assert context is self._context
        assert pin == 0
        self.gpio_direction = int(direction)
        self.last_gpio_broadcast = broadcast


def _open_camera(api: StrobeFakeAPI) -> Camera:
    return Camera.open(api=api)


def test_strobe_dataclass_conversion_round_trip() -> None:
    raw_info = fc2StrobeInfo()
    raw_info.source = 2
    raw_info.present = 1
    raw_info.readOutSupported = 1
    raw_info.onOffSupported = 1
    raw_info.polaritySupported = 0
    raw_info.minValue = 0.5
    raw_info.maxValue = 12.5
    info = StrobeInfo.from_c(raw_info)

    raw_control = fc2StrobeControl()
    raw_control.source = 2
    raw_control.onOff = 1
    raw_control.polarity = 1
    raw_control.delay = 2.0
    raw_control.duration = 3.0
    control = StrobeControl.from_c(raw_control)
    restored = control.to_c()

    assert info.source == 2
    assert info.present is True
    assert info.polarity_supported is False
    assert control.on_off is True
    assert restored.source == 2
    assert restored.duration == pytest.approx(3.0)


def test_camera_get_strobe_info_and_strobe_with_fake_api() -> None:
    camera = _open_camera(StrobeFakeAPI())
    try:
        info = camera.get_strobe_info(source=0)
        control = camera.get_strobe(source=0)

        assert info.present is True
        assert control.source == 0
        assert control.duration == pytest.approx(1.0)
    finally:
        camera.close()


def test_camera_set_strobe_updates_only_explicit_fields() -> None:
    api = StrobeFakeAPI()
    camera = _open_camera(api)
    try:
        updated = camera.set_strobe(source=0, on=True, polarity=1, delay=2.5, duration=3.5)

        assert updated.on_off is True
        assert updated.polarity == 1
        assert updated.delay == pytest.approx(2.5)
        assert updated.duration == pytest.approx(3.5)
        assert api.last_strobe_broadcast is False
    finally:
        camera.close()


def test_camera_set_strobe_accepts_control_for_restore() -> None:
    api = StrobeFakeAPI()
    camera = _open_camera(api)
    try:
        old = camera.get_strobe(0)
        camera.set_strobe(0, on=True)
        restored = camera.set_strobe(old)

        assert restored == old
    finally:
        camera.close()


def test_camera_set_strobe_rejects_unsupported_source_and_settings() -> None:
    api = StrobeFakeAPI()
    api.info.present = 0
    camera = _open_camera(api)
    try:
        with pytest.raises(UnsupportedStrobeError):
            camera.get_strobe(0)
        with pytest.raises(UnsupportedStrobeError):
            camera.set_strobe(0, on=True)
    finally:
        camera.close()

    api = StrobeFakeAPI()
    api.info.polaritySupported = 0
    camera = _open_camera(api)
    try:
        with pytest.raises(StrobeConfigurationError):
            camera.set_strobe(0, polarity=1)
        with pytest.raises(StrobeConfigurationError):
            camera.set_strobe(0, duration=11.0)
    finally:
        camera.close()


def test_gpio_direction_helpers_with_fake_api() -> None:
    api = StrobeFakeAPI()
    camera = _open_camera(api)
    try:
        assert camera.get_gpio_pin_direction(0) == 0
        assert camera.set_gpio_pin_direction(0, "output", broadcast=True) == 1
        assert api.last_gpio_broadcast is True
        assert camera.set_gpio_pin_direction(0, False) == 0
    finally:
        camera.close()


def test_normalize_gpio_direction_rejects_invalid_values() -> None:
    assert normalize_gpio_direction("input") == 0
    assert normalize_gpio_direction("out") == 1
    with pytest.raises(GPIOConfigurationError):
        normalize_gpio_direction("sideways")
    with pytest.raises(GPIOConfigurationError):
        normalize_gpio_direction(2)


def test_gpio_pin_validation_rejects_negative_and_non_integer_values() -> None:
    assert normalize_gpio_pin(0) == 0
    assert normalize_gpio_pin(3) == 3
    for value in (-1, True, 1.5, "0"):
        with pytest.raises(GPIOConfigurationError):
            normalize_gpio_pin(value)  # type: ignore[arg-type]


def test_camera_gpio_direction_rejects_invalid_pin_before_api_call() -> None:
    api = StrobeFakeAPI()
    camera = _open_camera(api)
    try:
        with pytest.raises(GPIOConfigurationError):
            camera.get_gpio_pin_direction(-1)
        with pytest.raises(GPIOConfigurationError):
            camera.set_gpio_pin_direction(-1, "input")
    finally:
        camera.close()
