from __future__ import annotations

import ctypes
from dataclasses import dataclass
from dataclasses import field as dc_field

import pytest

from flycapture2_c.camera import Camera
from flycapture2_c.ctypes_defs import (
    fc2CameraInfo,
    fc2Context,
    fc2Image,
    fc2ImageMetadata,
    fc2PGRGuid,
    fc2TimeStamp,
)
from flycapture2_c.errors import (
    CameraStateError,
    FC2ErrorCode,
    FlyCapture2Error,
)


def _make_guid() -> fc2PGRGuid:
    g = fc2PGRGuid()
    for i in range(4):
        g.value[i] = i
    return g


def _make_context() -> fc2Context:
    return fc2Context(1)


def _make_image() -> fc2Image:
    return fc2Image()


def _make_camera_info() -> fc2CameraInfo:
    info = fc2CameraInfo()
    info.serialNumber = 123456
    info.modelName = b"Flea3 FL3-U3-13E4C\x00"
    info.vendorName = b"Point Grey\x00"
    info.sensorInfo = b"e2v EV76C560\x00"
    info.sensorResolution = b"1312x1082\x00"
    info.driverName = b"FlyCapture2\x00"
    info.firmwareVersion = b"2.0.3.0\x00"
    info.firmwareBuildTime = b"Thu Jul 11 08:57:55 2019\x00"
    info.userDefinedName = b"\x00"
    info.xmlURL1 = b"\x00"
    info.xmlURL2 = b"\x00"
    return info


def _make_image_metadata() -> fc2ImageMetadata:
    return fc2ImageMetadata()


def _make_timestamp() -> fc2TimeStamp:
    return fc2TimeStamp()


def _sdk_error(code: FC2ErrorCode, operation: str = "") -> FlyCapture2Error:
    return FlyCapture2Error(
        build_error_message(code=code, operation=operation),
        code=code,
        operation=operation,
    )


def build_error_message(
    *,
    code: FC2ErrorCode,
    description: str | None = None,
    operation: str | None = None,
) -> str:
    prefix = f"{operation} failed" if operation else "FlyCapture2 call failed"
    if description:
        return f"{prefix}: {code.name} ({code.value}) - {description}"
    return f"{prefix}: {code.name} ({code.value})"


@dataclass
class FakeFlyCapture2API:
    """A fake FlyCapture2CAPI that tracks call counts and supports failure injection.

    Each method records its call count. Setting ``fail_on`` to a method name
    causes that method to raise the specified error on the *next* call.
    ``fail_on`` is consumed after one invocation.
    """

    call_counts: dict[str, int] = dc_field(default_factory=dict)
    call_order: list[str] = dc_field(default_factory=list)
    fail_on: dict[str, FlyCapture2Error] = dc_field(default_factory=dict)
    _dll: object = None  # shared instance, relevant only for lazy-load logic
    _lock: object = None  # shared instance

    def _record(self, name: str) -> None:
        self.call_counts[name] = self.call_counts.get(name, 0) + 1
        self.call_order.append(name)

    def _maybe_fail(self, name: str) -> None:
        if name in self.fail_on:
            exc = self.fail_on.pop(name)
            raise exc

    # -- lifecycle methods used by Camera --

    def create_context(self) -> fc2Context:
        self._record("create_context")
        self._maybe_fail("create_context")
        return _make_context()

    def destroy_context(self, context: fc2Context) -> None:
        self._record("destroy_context")
        self._maybe_fail("destroy_context")

    def get_num_cameras(self, context: fc2Context) -> int:
        self._record("get_num_cameras")
        self._maybe_fail("get_num_cameras")
        return 1

    def get_camera_from_index(self, context: fc2Context, index: int) -> fc2PGRGuid:
        self._record("get_camera_from_index")
        self._maybe_fail("get_camera_from_index")
        return _make_guid()

    def get_camera_info(self, context: fc2Context) -> fc2CameraInfo:
        self._record("get_camera_info")
        self._maybe_fail("get_camera_info")
        return _make_camera_info()

    def connect(self, context: fc2Context, guid: fc2PGRGuid) -> None:
        self._record("connect")
        self._maybe_fail("connect")

    def disconnect(self, context: fc2Context) -> None:
        self._record("disconnect")
        self._maybe_fail("disconnect")

    def start_capture(self, context: fc2Context) -> None:
        self._record("start_capture")
        self._maybe_fail("start_capture")

    def stop_capture(self, context: fc2Context) -> None:
        self._record("stop_capture")
        self._maybe_fail("stop_capture")

    def create_image(self) -> fc2Image:
        self._record("create_image")
        self._maybe_fail("create_image")
        return _make_image()

    def destroy_image(self, image: fc2Image) -> None:
        self._record("destroy_image")
        self._maybe_fail("destroy_image")

    def retrieve_buffer(self, context: fc2Context, image: fc2Image) -> None:
        self._record("retrieve_buffer")
        self._maybe_fail("retrieve_buffer")
        image.rows = 480
        image.cols = 640
        image.stride = 640
        image.format = ctypes.c_uint32(0x80000000)  # MONO8
        image.dataSize = 480 * 640
        image.receivedDataSize = 480 * 640
        self._retrieve_buf = (ctypes.c_ubyte * (480 * 640))()  # kept alive
        image.pData = ctypes.cast(self._retrieve_buf, ctypes.POINTER(ctypes.c_ubyte))

    def get_image_metadata(self, image: fc2Image) -> fc2ImageMetadata:
        self._record("get_image_metadata")
        self._maybe_fail("get_image_metadata")
        return _make_image_metadata()

    def get_image_timestamp(self, image: fc2Image) -> fc2TimeStamp:
        self._record("get_image_timestamp")
        self._maybe_fail("get_image_timestamp")
        return _make_timestamp()

    # -- extras (needed for type compat) --

    def is_connected(self, context: fc2Context) -> bool:
        return True

    def get_configuration(self, context: fc2Context):
        from flycapture2_c.ctypes_defs import fc2Config
        return fc2Config()

    def get_property_info(self, context: fc2Context, property_type: int):
        from flycapture2_c.ctypes_defs import fc2PropertyInfo
        return fc2PropertyInfo()

    def get_property(self, context: fc2Context, property_type: int):
        from flycapture2_c.ctypes_defs import fc2Property
        return fc2Property()

    def get_format7_info(self, context: fc2Context, mode: int):
        from flycapture2_c.ctypes_defs import fc2Format7Info
        return fc2Format7Info(), False

    def get_format7_configuration(self, context: fc2Context):
        from flycapture2_c.ctypes_defs import fc2Format7ImageSettings
        return fc2Format7ImageSettings(), 0, 0.0

    def get_trigger_mode_info(self, context: fc2Context):
        from flycapture2_c.ctypes_defs import fc2TriggerModeInfo
        return fc2TriggerModeInfo()

    def get_trigger_mode(self, context: fc2Context):
        from flycapture2_c.ctypes_defs import fc2TriggerMode
        return fc2TriggerMode()

    def get_embedded_image_info(self, context: fc2Context):
        from flycapture2_c.raw.structs import fc2EmbeddedImageInfo
        return fc2EmbeddedImageInfo()

    def set_embedded_image_info(self, context: fc2Context, info) -> None:
        pass

    def get_camera_stats(self, context: fc2Context):
        from flycapture2_c.raw.structs import fc2CameraStats
        return fc2CameraStats()

    def reset_camera_stats(self) -> None:
        pass

    def fire_software_trigger(self, context: fc2Context, *, broadcast: bool = False) -> None:
        pass

    def get_strobe_info(self, context: fc2Context, source: int):
        from flycapture2_c.raw.structs import fc2StrobeInfo
        return fc2StrobeInfo()

    def get_strobe(self, context: fc2Context, source: int):
        from flycapture2_c.raw.structs import fc2StrobeControl
        return fc2StrobeControl()

    def set_strobe(self, context: fc2Context, control, *, broadcast: bool = False) -> None:
        pass

    def get_gpio_pin_direction(self, context: fc2Context, pin: int) -> int:
        return 0

    def set_gpio_pin_direction(self, context: fc2Context, pin: int, direction: int, *, broadcast: bool = False) -> None:
        pass

    def get_gige_config(self, context: fc2Context):
        from flycapture2_c.raw.structs import fc2GigEConfig
        return fc2GigEConfig()

    def get_video_mode_and_frame_rate(self, context: fc2Context) -> tuple[int, int]:
        return 0, 0

    def get_library_version(self) -> tuple[int, int, int, int]:
        return 2, 11, 3, 425

    def _require_function(self, name: str):
        raise FlyCapture2Error("Not implemented in fake API")

    def set_configuration(self, context, config) -> None:
        pass

    def set_format7_configuration_packet(self, context, settings, packet_size) -> None:
        pass

    def set_property(self, context, prop) -> None:
        pass

    def set_trigger_mode(self, context, trigger_mode) -> None:
        pass

    def set_trigger_mode_broadcast(self, context, trigger_mode) -> None:
        pass

    def validate_format7_settings(self, context, settings):
        from flycapture2_c.ctypes_defs import fc2Format7PacketInfo
        return True, fc2Format7PacketInfo()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def fake_api() -> FakeFlyCapture2API:
    return FakeFlyCapture2API()


@pytest.fixture
def open_camera(fake_api: FakeFlyCapture2API) -> Camera:
    """Return a Camera that has been opened with a fake API."""
    cam = Camera(api=fake_api)  # type: ignore[arg-type]
    # Force the internal _api attribute to be our fake (Camera.__init__ calls get_api
    # when api is None, but passing api=... bypasses get_api)
    cam._open(index=0)
    return cam


# ---------------------------------------------------------------------------
# Tests — stop() guards
# ---------------------------------------------------------------------------


def test_stop_without_start_does_not_call_fc2StopCapture(
    open_camera: Camera,
    fake_api: FakeFlyCapture2API,
) -> None:
    """stop() on a camera that has never been started must not call stop_capture."""
    assert not open_camera.is_capturing
    open_camera.stop()
    assert fake_api.call_counts.get("stop_capture", 0) == 0
    assert not open_camera.is_capturing


def test_repeated_stop_is_safe(
    open_camera: Camera,
    fake_api: FakeFlyCapture2API,
) -> None:
    """Calling stop() twice must not raise and must only call stop_capture once."""
    open_camera.start()
    assert fake_api.call_counts.get("start_capture", 0) == 1
    assert open_camera.is_capturing

    open_camera.stop()
    assert fake_api.call_counts.get("stop_capture", 0) == 1
    assert not open_camera.is_capturing

    open_camera.stop()
    assert fake_api.call_counts.get("stop_capture", 0) == 1
    assert not open_camera.is_capturing


# ---------------------------------------------------------------------------
# Tests — start() guards
# ---------------------------------------------------------------------------


def test_start_sets_capturing_only_after_success(
    open_camera: Camera,
    fake_api: FakeFlyCapture2API,
) -> None:
    """start() must set _capturing=True only after fc2StartCapture returns OK."""
    assert not open_camera.is_capturing
    open_camera.start()
    assert open_camera.is_capturing
    assert fake_api.call_counts.get("start_capture", 0) == 1


def test_start_failure_leaves_capturing_false(
    open_camera: Camera,
    fake_api: FakeFlyCapture2API,
) -> None:
    """If fc2StartCapture raises, _capturing must remain False."""
    fake_api.fail_on["start_capture"] = _sdk_error(FC2ErrorCode.ISOCH_START_FAILED, "fc2StartCapture")
    assert not open_camera.is_capturing
    with pytest.raises(FlyCapture2Error):
        open_camera.start()
    assert not open_camera.is_capturing


def test_start_without_open_raises_clear_error(
    fake_api: FakeFlyCapture2API,
) -> None:
    """Calling start() on a never-opened Camera must raise CameraStateError."""
    cam = Camera(api=fake_api)  # type: ignore[arg-type]
    with pytest.raises(CameraStateError, match="not open"):
        cam.start()


def test_start_when_already_capturing_is_idempotent(
    open_camera: Camera,
    fake_api: FakeFlyCapture2API,
) -> None:
    """Calling start() on an already-capturing camera must return safely."""
    open_camera.start()
    assert fake_api.call_counts.get("start_capture", 0) == 1
    assert open_camera.is_capturing

    open_camera.start()
    assert fake_api.call_counts.get("start_capture", 0) == 1
    assert open_camera.is_capturing


# ---------------------------------------------------------------------------
# Tests — stop() success/failure
# ---------------------------------------------------------------------------


def test_stop_success_sets_capturing_false(
    open_camera: Camera,
    fake_api: FakeFlyCapture2API,
) -> None:
    """After a successful stop, _capturing must be False."""
    open_camera.start()
    assert open_camera.is_capturing
    open_camera.stop()
    assert not open_camera.is_capturing
    assert fake_api.call_counts.get("stop_capture", 0) == 1


def test_stop_propagates_real_sdk_error(
    open_camera: Camera,
    fake_api: FakeFlyCapture2API,
) -> None:
    """Explicit stop() must propagate real SDK errors (not ISOCH_NOT_STARTED)."""
    open_camera.start()
    fake_api.fail_on["stop_capture"] = _sdk_error(FC2ErrorCode.INVALID_GENERATION, "fc2StopCapture")
    with pytest.raises(FlyCapture2Error) as exc_info:
        open_camera.stop()
    assert exc_info.value.code == FC2ErrorCode.INVALID_GENERATION
    assert open_camera.is_capturing  # still True since stop failed


# ---------------------------------------------------------------------------
# Tests — close() idempotent and order
# ---------------------------------------------------------------------------


def test_repeated_close_is_safe(
    open_camera: Camera,
    fake_api: FakeFlyCapture2API,
) -> None:
    """Calling close() twice must not raise."""
    open_camera.close()
    assert fake_api.call_counts.get("disconnect", 0) == 1
    assert fake_api.call_counts.get("destroy_context", 0) == 1
    open_camera.close()
    # second close must not call anything extra
    assert fake_api.call_counts.get("disconnect", 0) == 1
    assert fake_api.call_counts.get("destroy_context", 0) == 1


def test_close_after_start_calls_stop_then_disconnect(
    open_camera: Camera,
    fake_api: FakeFlyCapture2API,
) -> None:
    """close() after start() must call stop_capture before disconnect/destroy."""
    open_camera.start()
    open_camera.close()

    # Check order: stop before disconnect, disconnect before destroy_image, ...
    stop_idx = fake_api.call_order.index("stop_capture")
    disconnect_idx = fake_api.call_order.index("disconnect")
    destroy_image_idx = fake_api.call_order.index("destroy_image")
    destroy_ctx_idx = fake_api.call_order.index("destroy_context")

    assert stop_idx < disconnect_idx < destroy_image_idx < destroy_ctx_idx


def test_close_without_ever_starting(
    open_camera: Camera,
    fake_api: FakeFlyCapture2API,
) -> None:
    """close() on an open-but-not-started camera must not call stop_capture."""
    open_camera.close()
    assert fake_api.call_counts.get("stop_capture", 0) == 0
    assert fake_api.call_counts.get("disconnect", 0) == 1
    assert fake_api.call_counts.get("destroy_context", 0) == 1


# ---------------------------------------------------------------------------
# Tests — close() best-effort: stop failure must not block cleanup
# ---------------------------------------------------------------------------


def test_close_when_stop_fails_still_attempts_disconnect(
    open_camera: Camera,
    fake_api: FakeFlyCapture2API,
) -> None:
    """If stop_capture fails during close(), disconnect/destroy must still execute."""
    open_camera.start()
    fake_api.fail_on["stop_capture"] = _sdk_error(FC2ErrorCode.INVALID_GENERATION, "fc2StopCapture")
    open_camera.close()

    assert fake_api.call_counts.get("stop_capture", 0) == 1
    assert fake_api.call_counts.get("disconnect", 0) == 1
    assert fake_api.call_counts.get("destroy_image", 0) == 1
    assert fake_api.call_counts.get("destroy_context", 0) == 1

    # cleanup_errors should contain the stop failure
    assert len(open_camera.cleanup_errors) == 1
    assert open_camera.cleanup_errors[0].code == FC2ErrorCode.INVALID_GENERATION


def test_close_when_stop_and_disconnect_fail_still_destroys(
    open_camera: Camera,
    fake_api: FakeFlyCapture2API,
) -> None:
    """Every cleanup step is independent: stop + disconnect failures must not block destroy."""
    open_camera.start()
    fake_api.fail_on["stop_capture"] = _sdk_error(FC2ErrorCode.INVALID_GENERATION, "fc2StopCapture")
    fake_api.fail_on["disconnect"] = _sdk_error(FC2ErrorCode.NOT_CONNECTED, "fc2Disconnect")
    open_camera.close()

    assert fake_api.call_counts.get("stop_capture", 0) == 1
    assert fake_api.call_counts.get("disconnect", 0) == 1
    assert fake_api.call_counts.get("destroy_image", 0) == 1
    assert fake_api.call_counts.get("destroy_context", 0) == 1
    assert len(open_camera.cleanup_errors) == 2


def test_close_when_already_closed_does_nothing(
    fake_api: FakeFlyCapture2API,
) -> None:
    """close() on an already-closed camera must be a no-op (no API calls)."""
    cam = Camera(api=fake_api)  # type: ignore[arg-type]
    # Camera is born _closed=True
    cam.close()
    assert fake_api.call_counts.get("disconnect", 0) == 0
    assert fake_api.call_counts.get("destroy_context", 0) == 0
    assert fake_api.call_counts.get("stop_capture", 0) == 0


# ---------------------------------------------------------------------------
# Tests — read_frame() without start
# ---------------------------------------------------------------------------


def test_read_frame_without_start_raises_clear_error(
    open_camera: Camera,
    fake_api: FakeFlyCapture2API,
) -> None:
    """read_frame() before start() must raise CameraStateError with a clear message."""
    with pytest.raises(CameraStateError, match="not been started"):
        open_camera.read_frame()


def test_read_frame_after_stop_raises_clear_error(
    open_camera: Camera,
    fake_api: FakeFlyCapture2API,
) -> None:
    """read_frame() after stop() must raise CameraStateError."""
    open_camera.start()
    open_camera.stop()
    with pytest.raises(CameraStateError, match="not been started"):
        open_camera.read_frame()


# ---------------------------------------------------------------------------
# Tests — __exit__ / context manager
# ---------------------------------------------------------------------------


def test_context_manager_cleanup_errors_do_not_replace_primary_exception(
    open_camera: Camera,
    fake_api: FakeFlyCapture2API,
) -> None:
    """When a with-block body raises, close() failures must NOT overwrite the original exception."""

    class TestError(Exception):
        pass

    open_camera.start()
    fake_api.fail_on["stop_capture"] = _sdk_error(FC2ErrorCode.INVALID_GENERATION, "fc2StopCapture")

    with pytest.raises(TestError):  # must see the original error, not a cleanup error
        with open_camera as cam:
            raise TestError("primary failure")

    # Verify cleanup still happened
    assert fake_api.call_counts.get("stop_capture", 0) == 1
    assert fake_api.call_counts.get("disconnect", 0) == 1
    assert len(open_camera.cleanup_errors) == 1
    assert open_camera.cleanup_errors[0].code == FC2ErrorCode.INVALID_GENERATION


def test_context_manager_no_exception_empty_cleanup(
    open_camera: Camera,
    fake_api: FakeFlyCapture2API,
) -> None:
    """When no exception occurs in the with-block, close() runs normally."""
    open_camera.start()
    with open_camera as cam:
        cam.read_frame()
    assert fake_api.call_counts.get("stop_capture", 0) == 1
    assert fake_api.call_counts.get("disconnect", 0) == 1
    assert len(open_camera.cleanup_errors) == 0
