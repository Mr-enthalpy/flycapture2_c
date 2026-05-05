from __future__ import annotations

import ctypes
import os
import subprocess
import sys
from pathlib import Path

from flycapture2_c.api import FlyCapture2CAPI
from flycapture2_c.ctypes_defs import (
    fc2Config,
    fc2Context,
    fc2Error,
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
        "fc2GetConfiguration",
        "fc2SetConfiguration",
        "fc2GetFormat7Info",
        "fc2ValidateFormat7Settings",
        "fc2GetFormat7Configuration",
        "fc2SetFormat7ConfigurationPacket",
        "fc2SetFormat7Configuration",
        "fc2GetTriggerModeInfo",
        "fc2GetTriggerMode",
        "fc2SetTriggerMode",
        "fc2SetTriggerModeBroadcast",
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


def test_flycapture2capi_bind_uses_raw_specs_registry() -> None:
    dll = _FakeDLL()

    FlyCapture2CAPI()._bind(dll)

    assert dll.fc2GetTriggerMode.argtypes == FUNCTION_SPECS["fc2GetTriggerMode"].argtypes
    assert dll.fc2SetFormat7ConfigurationPacket.argtypes == FUNCTION_SPECS[
        "fc2SetFormat7ConfigurationPacket"
    ].argtypes
    assert dll.fc2SetConfiguration.argtypes == FUNCTION_SPECS["fc2SetConfiguration"].argtypes


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
