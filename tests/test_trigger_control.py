from __future__ import annotations

import ctypes

import pytest

from flycapture2_c.api import FlyCapture2CAPI
from flycapture2_c.camera import Camera
from flycapture2_c.ctypes_defs import (
    fc2CameraInfo,
    fc2Context,
    fc2Error,
    fc2Image,
    fc2PGRGuid,
    fc2TriggerMode,
    fc2TriggerModeInfo,
)
from flycapture2_c.errors import CameraStateError, FlyCapture2NotSupportedError, TriggerModeError
from flycapture2_c.trigger import SOFTWARE_TRIGGER_SOURCE, TriggerMode, TriggerModeInfo


def _write_c_string(struct, field_name: str, value: str) -> None:
    setattr(struct, field_name, value.encode("utf-8"))


class _FakeFunction:
    argtypes = None
    restype = None

    def __call__(self, *args):
        _ = args
        return 0


class _FakeDLL:
    def __init__(self) -> None:
        self.functions: dict[str, _FakeFunction] = {}

    def __getattr__(self, name: str) -> _FakeFunction:
        function = _FakeFunction()
        self.functions[name] = function
        setattr(self, name, function)
        return function


class TriggerFakeAPI:
    def __init__(self) -> None:
        self._context = object()
        self.set_trigger_mode_calls = 0
        self.set_trigger_mode_broadcast_calls = 0
        self.fire_software_trigger_calls = 0
        self.fire_software_trigger_broadcast_calls = 0
        self.last_written_trigger_mode: fc2TriggerMode | None = None
        self.trigger_info = fc2TriggerModeInfo()
        self.trigger_info.present = 1
        self.trigger_info.readOutSupported = 1
        self.trigger_info.onOffSupported = 1
        self.trigger_info.polaritySupported = 1
        self.trigger_info.valueReadable = 1
        self.trigger_info.sourceMask = (1 << 0) | (1 << 1)
        self.trigger_info.softwareTriggerSupported = 1
        self.trigger_info.modeMask = (1 << 15) | (1 << 14)
        self.trigger_mode = fc2TriggerMode()
        self.trigger_mode.onOff = 0
        self.trigger_mode.polarity = 0
        self.trigger_mode.source = 0
        self.trigger_mode.mode = 0
        self.trigger_mode.parameter = 0

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
        _write_c_string(info, "modelName", "TriggerTestCam")
        return info

    def get_trigger_mode_info(self, context) -> fc2TriggerModeInfo:
        assert context is self._context
        return self.trigger_info

    def get_trigger_mode(self, context) -> fc2TriggerMode:
        assert context is self._context
        return _copy_trigger_mode(self.trigger_mode)

    def set_trigger_mode(self, context, trigger_mode: fc2TriggerMode) -> None:
        assert context is self._context
        self.set_trigger_mode_calls += 1
        self.last_written_trigger_mode = _copy_trigger_mode(trigger_mode)
        self.trigger_mode = _copy_trigger_mode(trigger_mode)

    def set_trigger_mode_broadcast(self, context, trigger_mode: fc2TriggerMode) -> None:
        assert context is self._context
        self.set_trigger_mode_broadcast_calls += 1
        self.last_written_trigger_mode = _copy_trigger_mode(trigger_mode)
        self.trigger_mode = _copy_trigger_mode(trigger_mode)

    def fire_software_trigger(self, context, *, broadcast: bool = False) -> None:
        assert context is self._context
        if broadcast:
            self.fire_software_trigger_broadcast_calls += 1
        else:
            self.fire_software_trigger_calls += 1


def _copy_trigger_mode(source: fc2TriggerMode) -> fc2TriggerMode:
    target = fc2TriggerMode()
    target.onOff = source.onOff
    target.polarity = source.polarity
    target.source = source.source
    target.mode = source.mode
    target.parameter = source.parameter
    return target


def _open_camera(api: TriggerFakeAPI) -> Camera:
    return Camera.open(api=api)


def test_trigger_structs_convert_to_public_dataclasses() -> None:
    info = fc2TriggerModeInfo()
    info.present = 1
    info.readOutSupported = 1
    info.onOffSupported = 1
    info.polaritySupported = 1
    info.valueReadable = 1
    info.sourceMask = 0b11
    info.softwareTriggerSupported = 1
    info.modeMask = (1 << 15) | (1 << 13)

    public_info = TriggerModeInfo.from_c(info)
    assert public_info.present is True
    assert public_info.supports_source(0)
    assert public_info.supports_source(1)
    assert public_info.supports_source(SOFTWARE_TRIGGER_SOURCE)
    assert public_info.supported_modes == (0, 2)

    mode = fc2TriggerMode()
    mode.onOff = 1
    mode.polarity = 1
    mode.source = 0
    mode.mode = 0
    mode.parameter = 4

    public_mode = TriggerMode.from_c(mode)
    assert public_mode == TriggerMode(on_off=True, polarity=1, source=0, mode=0, parameter=4)
    roundtrip = public_mode.to_c()
    assert roundtrip.onOff == 1
    assert roundtrip.polarity == 1
    assert roundtrip.parameter == 4


def test_raw_trigger_function_specs_are_bound() -> None:
    dll = _FakeDLL()
    api = FlyCapture2CAPI()
    api._bind(dll)

    assert dll.fc2GetTriggerModeInfo.argtypes == [fc2Context, ctypes.POINTER(fc2TriggerModeInfo)]
    assert dll.fc2GetTriggerModeInfo.restype is fc2Error
    assert dll.fc2GetTriggerMode.argtypes == [fc2Context, ctypes.POINTER(fc2TriggerMode)]
    assert dll.fc2GetTriggerMode.restype is fc2Error
    assert dll.fc2SetTriggerMode.argtypes == [fc2Context, ctypes.POINTER(fc2TriggerMode)]
    assert dll.fc2SetTriggerMode.restype is fc2Error
    assert dll.fc2SetTriggerModeBroadcast.argtypes == [fc2Context, ctypes.POINTER(fc2TriggerMode)]
    assert dll.fc2SetTriggerModeBroadcast.restype is fc2Error
    assert dll.fc2FireSoftwareTrigger.argtypes == [fc2Context]
    assert dll.fc2FireSoftwareTrigger.restype is fc2Error
    assert dll.fc2FireSoftwareTriggerBroadcast.argtypes == [fc2Context]
    assert dll.fc2FireSoftwareTriggerBroadcast.restype is fc2Error


def test_camera_get_trigger_mode_info_and_mode() -> None:
    api = TriggerFakeAPI()
    camera = _open_camera(api)
    try:
        info = camera.get_trigger_mode_info()
        mode = camera.get_trigger_mode()
    finally:
        camera.close()

    assert info.present is True
    assert info.supports_mode(0)
    assert mode.on_off is False
    assert mode.source == 0


def test_flycapture2capi_fire_software_trigger_calls_sdk_function() -> None:
    dll = _FakeDLL()
    api = FlyCapture2CAPI()
    api._dll = dll  # type: ignore[assignment]

    api.fire_software_trigger(fc2Context())
    api.fire_software_trigger(fc2Context(), broadcast=True)

    assert "fc2FireSoftwareTrigger" in dll.functions
    assert "fc2FireSoftwareTriggerBroadcast" in dll.functions


def test_flycapture2capi_missing_software_trigger_symbol_raises_not_supported() -> None:
    class MissingSoftwareTriggerDLL(_FakeDLL):
        def __getattr__(self, name: str) -> _FakeFunction:
            if name in {"fc2FireSoftwareTrigger", "fc2FireSoftwareTriggerBroadcast"}:
                raise AttributeError(name)
            return super().__getattr__(name)

    api = FlyCapture2CAPI()
    api._dll = MissingSoftwareTriggerDLL()  # type: ignore[assignment]

    with pytest.raises(FlyCapture2NotSupportedError, match="fc2FireSoftwareTrigger"):
        api.fire_software_trigger(fc2Context())
    with pytest.raises(FlyCapture2NotSupportedError, match="fc2FireSoftwareTriggerBroadcast"):
        api.fire_software_trigger(fc2Context(), broadcast=True)


def test_camera_fire_software_trigger_with_fake_api() -> None:
    api = TriggerFakeAPI()
    camera = _open_camera(api)
    try:
        camera.fire_software_trigger()
        camera.fire_software_trigger(broadcast=True)
    finally:
        camera.close()

    assert api.fire_software_trigger_calls == 1
    assert api.fire_software_trigger_broadcast_calls == 1


def test_camera_fire_software_trigger_requires_open_camera() -> None:
    camera = Camera(api=TriggerFakeAPI())

    with pytest.raises(CameraStateError):
        camera.fire_software_trigger()


def test_camera_enable_trigger_validates_and_writes_mode() -> None:
    api = TriggerFakeAPI()
    camera = _open_camera(api)
    try:
        result = camera.enable_trigger(source=1, mode=1, parameter=3, polarity=1)
    finally:
        camera.close()

    assert result == TriggerMode(on_off=True, polarity=1, source=1, mode=1, parameter=3)
    assert api.set_trigger_mode_calls == 1
    assert api.set_trigger_mode_broadcast_calls == 0
    assert api.last_written_trigger_mode is not None
    assert api.last_written_trigger_mode.onOff == 1
    assert api.last_written_trigger_mode.source == 1
    assert api.last_written_trigger_mode.mode == 1


def test_camera_disable_trigger_preserves_existing_fields() -> None:
    api = TriggerFakeAPI()
    api.trigger_mode.onOff = 1
    api.trigger_mode.source = 1
    api.trigger_mode.mode = 1
    api.trigger_mode.parameter = 9
    camera = _open_camera(api)
    try:
        result = camera.disable_trigger()
    finally:
        camera.close()

    assert result == TriggerMode(on_off=False, polarity=0, source=1, mode=1, parameter=9)
    assert api.set_trigger_mode_calls == 1


def test_camera_enable_trigger_rejects_unsupported_source_without_write() -> None:
    api = TriggerFakeAPI()
    camera = _open_camera(api)
    try:
        try:
            camera.enable_trigger(source=4)
            assert False, "expected TriggerModeError"
        except TriggerModeError:
            pass
    finally:
        camera.close()

    assert api.set_trigger_mode_calls == 0
    assert api.set_trigger_mode_broadcast_calls == 0


def test_camera_set_trigger_mode_can_use_broadcast_binding() -> None:
    api = TriggerFakeAPI()
    camera = _open_camera(api)
    try:
        result = camera.set_trigger_mode(
            TriggerMode(on_off=True, polarity=0, source=0, mode=0, parameter=0),
            broadcast=True,
        )
    finally:
        camera.close()

    assert result.on_off is True
    assert api.set_trigger_mode_calls == 0
    assert api.set_trigger_mode_broadcast_calls == 1


def test_camera_set_trigger_mode_dataclass_can_restore_sdk_state_with_incomplete_masks() -> None:
    api = TriggerFakeAPI()
    api.trigger_info.sourceMask = 0
    api.trigger_info.modeMask = 0
    camera = _open_camera(api)
    try:
        result = camera.set_trigger_mode(TriggerMode(on_off=True, polarity=0, source=9, mode=9, parameter=2))
    finally:
        camera.close()

    assert result == TriggerMode(on_off=True, polarity=0, source=9, mode=9, parameter=2)
    assert api.set_trigger_mode_calls == 1
