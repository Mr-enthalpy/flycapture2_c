from __future__ import annotations

import ctypes
import os
import subprocess
import sys
from pathlib import Path

import pytest

from flycapture2_c.api import FlyCapture2CAPI
from flycapture2_c.ctypes_defs import (
    fc2Config,
    fc2Context,
    fc2Error,
    fc2ImageMetadata,
    fc2Format7ImageSettings,
    fc2Format7Info,
    fc2Format7PacketInfo,
    fc2Image,
    fc2PGRGuid,
    fc2Property,
    fc2PropertyInfo,
    fc2TriggerMode,
    fc2TriggerModeInfo,
)
from flycapture2_c.errors import FlyCapture2NotSupportedError
from flycapture2_c.raw.structs import fc2CameraStats, fc2EmbeddedImageInfo, fc2StrobeControl, fc2StrobeInfo
from flycapture2_c.raw.specs import FUNCTION_SPECS, FunctionSpec, bind_function_specs


class _FakeFunction:
    argtypes = None
    restype = None


class _FakeDLL:
    def __init__(self) -> None:
        self.functions: dict[str, _FakeFunction] = {}

    def __getattr__(self, name: str) -> _FakeFunction:
        function = _FakeFunction()
        self.functions[name] = function
        setattr(self, name, function)
        return function


def test_raw_specs_cover_current_binding_surface() -> None:
    expected_names = {
        "fc2CreateContext",
        "fc2DestroyContext",
        "fc2GetNumOfCameras",
        "fc2GetCameraFromIndex",
        "fc2GetCameraInfo",
        "fc2GetPropertyInfo",
        "fc2GetProperty",
        "fc2SetProperty",
        "fc2GetEmbeddedImageInfo",
        "fc2SetEmbeddedImageInfo",
        "fc2GetConfiguration",
        "fc2SetConfiguration",
        "fc2GetStats",
        "ResetStats",
        "fc2GetGPIOPinDirection",
        "fc2SetGPIOPinDirection",
        "fc2SetGPIOPinDirectionBroadcast",
        "fc2GetFormat7Info",
        "fc2ValidateFormat7Settings",
        "fc2GetFormat7Configuration",
        "fc2SetFormat7ConfigurationPacket",
        "fc2SetFormat7Configuration",
        "fc2GetTriggerModeInfo",
        "fc2GetTriggerMode",
        "fc2SetTriggerMode",
        "fc2SetTriggerModeBroadcast",
        "fc2GetStrobeInfo",
        "fc2GetStrobe",
        "fc2SetStrobe",
        "fc2SetStrobeBroadcast",
        "fc2Connect",
        "fc2Disconnect",
        "fc2IsConnected",
        "fc2StartCapture",
        "fc2StopCapture",
        "fc2RetrieveBuffer",
        "fc2CreateImage",
        "fc2DestroyImage",
        "fc2GetImageDimensions",
        "fc2GetImageData",
        "fc2GetImageMetadata",
        "fc2GetImageTimeStamp",
        "fc2GetVideoModeAndFrameRate",
        "fc2GetLibraryVersion",
        "fc2ErrorToDescription",
    }

    assert expected_names <= set(FUNCTION_SPECS)
    assert all(isinstance(spec, FunctionSpec) for spec in FUNCTION_SPECS.values())


def test_raw_specs_have_expected_representative_signatures() -> None:
    assert FUNCTION_SPECS["fc2GetPropertyInfo"].argtypes == [fc2Context, ctypes.POINTER(fc2PropertyInfo)]
    assert FUNCTION_SPECS["fc2GetPropertyInfo"].restype is fc2Error
    assert FUNCTION_SPECS["fc2SetProperty"].argtypes == [fc2Context, ctypes.POINTER(fc2Property)]
    assert FUNCTION_SPECS["fc2GetTriggerModeInfo"].argtypes == [fc2Context, ctypes.POINTER(fc2TriggerModeInfo)]
    assert FUNCTION_SPECS["fc2SetTriggerMode"].argtypes == [fc2Context, ctypes.POINTER(fc2TriggerMode)]
    assert FUNCTION_SPECS["fc2GetFormat7Info"].argtypes == [
        fc2Context,
        ctypes.POINTER(fc2Format7Info),
        ctypes.POINTER(ctypes.c_int),
    ]
    assert FUNCTION_SPECS["fc2ValidateFormat7Settings"].argtypes == [
        fc2Context,
        ctypes.POINTER(fc2Format7ImageSettings),
        ctypes.POINTER(ctypes.c_int),
        ctypes.POINTER(fc2Format7PacketInfo),
    ]
    assert FUNCTION_SPECS["fc2GetConfiguration"].argtypes == [fc2Context, ctypes.POINTER(fc2Config)]
    assert FUNCTION_SPECS["fc2GetEmbeddedImageInfo"].argtypes == [
        fc2Context,
        ctypes.POINTER(fc2EmbeddedImageInfo),
    ]
    assert FUNCTION_SPECS["fc2SetEmbeddedImageInfo"].argtypes == [
        fc2Context,
        ctypes.POINTER(fc2EmbeddedImageInfo),
    ]
    assert FUNCTION_SPECS["fc2GetStats"].argtypes == [fc2Context, ctypes.POINTER(fc2CameraStats)]
    assert FUNCTION_SPECS["ResetStats"].argtypes == []
    assert FUNCTION_SPECS["ResetStats"].required is False
    assert FUNCTION_SPECS["fc2GetGPIOPinDirection"].required is False
    assert FUNCTION_SPECS["fc2SetGPIOPinDirection"].required is False
    assert FUNCTION_SPECS["fc2SetGPIOPinDirectionBroadcast"].required is False
    assert FUNCTION_SPECS["fc2SetStrobeBroadcast"].required is False
    assert FUNCTION_SPECS["fc2GetImageMetadata"].argtypes == [
        ctypes.POINTER(fc2Image),
        ctypes.POINTER(fc2ImageMetadata),
    ]
    assert FUNCTION_SPECS["fc2GetGPIOPinDirection"].argtypes == [
        fc2Context,
        ctypes.c_uint32,
        ctypes.POINTER(ctypes.c_uint32),
    ]
    assert FUNCTION_SPECS["fc2SetGPIOPinDirection"].argtypes == [
        fc2Context,
        ctypes.c_uint32,
        ctypes.c_uint32,
    ]
    assert FUNCTION_SPECS["fc2GetStrobeInfo"].argtypes == [fc2Context, ctypes.POINTER(fc2StrobeInfo)]
    assert FUNCTION_SPECS["fc2GetStrobe"].argtypes == [fc2Context, ctypes.POINTER(fc2StrobeControl)]
    assert FUNCTION_SPECS["fc2SetStrobe"].argtypes == [fc2Context, ctypes.POINTER(fc2StrobeControl)]
    assert FUNCTION_SPECS["fc2RetrieveBuffer"].argtypes == [fc2Context, ctypes.POINTER(fc2Image)]
    assert FUNCTION_SPECS["fc2Connect"].argtypes == [fc2Context, ctypes.POINTER(fc2PGRGuid)]


def test_bind_function_specs_assigns_argtypes_and_restype() -> None:
    dll = _FakeDLL()

    bind_function_specs(dll)

    assert dll.fc2GetProperty.argtypes == [fc2Context, ctypes.POINTER(fc2Property)]
    assert dll.fc2GetProperty.restype is fc2Error
    assert dll.fc2GetImageData.argtypes == [
        ctypes.POINTER(fc2Image),
        ctypes.POINTER(ctypes.POINTER(ctypes.c_ubyte)),
    ]
    assert dll.fc2ErrorToDescription.restype is ctypes.c_char_p
    assert set(FUNCTION_SPECS) <= set(dll.functions)


def test_bind_function_specs_allows_missing_optional_functions() -> None:
    optional_names = {
        "ResetStats",
        "fc2GetGPIOPinDirection",
        "fc2SetGPIOPinDirection",
        "fc2SetGPIOPinDirectionBroadcast",
        "fc2SetStrobeBroadcast",
    }

    class OptionalMissingDLL(_FakeDLL):
        def __getattr__(self, name: str) -> _FakeFunction:
            if name in optional_names:
                raise AttributeError(name)
            return super().__getattr__(name)

    dll = OptionalMissingDLL()

    bind_function_specs(dll)

    assert optional_names.isdisjoint(dll.functions)
    assert dll.fc2GetStats.argtypes == [fc2Context, ctypes.POINTER(fc2CameraStats)]


def test_flycapture2capi_bind_uses_raw_specs_registry() -> None:
    dll = _FakeDLL()

    FlyCapture2CAPI()._bind(dll)

    assert dll.fc2GetTriggerMode.argtypes == FUNCTION_SPECS["fc2GetTriggerMode"].argtypes
    assert dll.fc2SetFormat7ConfigurationPacket.argtypes == FUNCTION_SPECS[
        "fc2SetFormat7ConfigurationPacket"
    ].argtypes
    assert dll.fc2SetConfiguration.argtypes == FUNCTION_SPECS["fc2SetConfiguration"].argtypes


def test_flycapture2capi_missing_optional_strobe_broadcast_raises_not_supported() -> None:
    class MissingBroadcastDLL:
        def __getattr__(self, name: str):
            if name == "fc2SetStrobeBroadcast":
                raise AttributeError(name)
            return _FakeFunction()

    api = FlyCapture2CAPI()
    api._dll = MissingBroadcastDLL()  # type: ignore[assignment]

    with pytest.raises(FlyCapture2NotSupportedError, match="fc2SetStrobeBroadcast"):
        api.set_strobe(fc2Context(), fc2StrobeControl(), broadcast=True)


def test_flycapture2capi_missing_optional_gpio_getter_raises_not_supported() -> None:
    class MissingGPIOGetterDLL:
        def __getattr__(self, name: str):
            if name == "fc2GetGPIOPinDirection":
                raise AttributeError(name)
            return _FakeFunction()

    api = FlyCapture2CAPI()
    api._dll = MissingGPIOGetterDLL()  # type: ignore[assignment]

    with pytest.raises(FlyCapture2NotSupportedError, match="fc2GetGPIOPinDirection"):
        api.get_gpio_pin_direction(fc2Context(), 0)


def test_flycapture2capi_missing_optional_gpio_setter_raises_not_supported() -> None:
    class MissingGPIOSetterDLL:
        def __getattr__(self, name: str):
            if name == "fc2SetGPIOPinDirection":
                raise AttributeError(name)
            return _FakeFunction()

    api = FlyCapture2CAPI()
    api._dll = MissingGPIOSetterDLL()  # type: ignore[assignment]

    with pytest.raises(FlyCapture2NotSupportedError, match="fc2SetGPIOPinDirection"):
        api.set_gpio_pin_direction(fc2Context(), 0, 1)


def test_flycapture2capi_missing_optional_gpio_broadcast_setter_raises_not_supported() -> None:
    class MissingGPIOBroadcastSetterDLL:
        def __getattr__(self, name: str):
            if name == "fc2SetGPIOPinDirectionBroadcast":
                raise AttributeError(name)
            return _FakeFunction()

    api = FlyCapture2CAPI()
    api._dll = MissingGPIOBroadcastSetterDLL()  # type: ignore[assignment]

    with pytest.raises(FlyCapture2NotSupportedError, match="fc2SetGPIOPinDirectionBroadcast"):
        api.set_gpio_pin_direction(fc2Context(), 0, 1, broadcast=True)


def test_import_raw_package_is_sdk_free() -> None:
    root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(root / "src")
    env["FLYCAPTURE2_SDK_DIR"] = str(root / "does_not_exist")
    env["FLYCAPTURE2_DLL_DIR"] = str(root / "does_not_exist")

    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import flycapture2_c.raw; import flycapture2_c.raw.specs; import flycapture2_c.raw.api",
        ],
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
