# flycapture2_c

`flycapture2_c` is a maintainable Python wrapper around the FlyCapture2 C SDK.
It is intended to replace legacy `pyflycap2` / `PyCapture2` usage with a
scriptable, non-GUI SDK wrapper.

## Install

Install the Python wrapper from a local checkout:

```powershell
python -m pip install .
```

For development and release checks:

```powershell
python -m pip install -e ".[dev]"
python scripts/check_release.py
```

The FlyCapture2 SDK must be installed separately. This project does not bundle
vendor SDK files, DLLs, drivers, headers, libraries, or sample binaries. Point
the wrapper at the SDK with one of these environment variables when the SDK is
not in the default install location:

```powershell
$env:FLYCAPTURE2_SDK_DIR="C:\Program Files\Point Grey Research\FlyCapture2"
$env:FLYCAPTURE2_DLL_DIR="C:\Program Files\Point Grey Research\FlyCapture2\bin64"
```

Importing `flycapture2_c` does not load the vendor DLL. DLL loading happens only
when an explicit camera operation needs the FlyCapture2 C runtime.

## Quick Start

Enumerate cameras:

```python
from flycapture2_c import enumerate_cameras

for camera in enumerate_cameras():
    print(camera)
```

Open one camera and grab one frame:

```python
from flycapture2_c import Camera

with Camera.open(index=0) as cam:
    cam.start()
    frame = cam.read_frame()
    print(frame.array.shape, frame.array.dtype)
```

Configure without GUI:

```python
from flycapture2_c import Camera

with Camera.open(0) as cam:
    cam.set_pixel_format("MONO8")
    cam.set_roi(offset_x=0, offset_y=0, width=1024, height=768)
    cam.set_shutter(5.0, auto=False)
    cam.set_gain(0.0, auto=False)
    cam.disable_trigger()
    cam.start()
    frame = cam.read_frame()
```

Configure an RGB pixel format when the camera reports support:

```python
from flycapture2_c import Camera

with Camera.open(0) as cam:
    cam.set_pixel_format("RGB")
    cam.disable_trigger()
    cam.start()
    frame = cam.read_frame_with_info()
    assert frame.array.ndim == 3
    assert frame.array.shape[2] == 3
    assert frame.array.dtype.name == "uint8"
```

Pixel-format configuration support and `read_frame()` decode support are
separate. See [docs/pixel_formats.md](docs/pixel_formats.md) for the current
support matrix. Full pixel-format decoding is not complete.

## Common Diagnostics

- `SDKNotFoundError`: set `FLYCAPTURE2_SDK_DIR` or install the FlyCapture2 SDK.
- `DLLLoadError`: set `FLYCAPTURE2_DLL_DIR` to the directory containing the
  FlyCapture2 C runtime DLL, or check the system DLL search path.
- `UnsupportedPixelFormatError`: the camera may accept a pixel format that this
  wrapper does not decode into a structured NumPy array yet.
- `UnsupportedGigEError`, `UnsupportedStrobeError`, or similar typed errors:
  the connected camera or installed DLL does not expose that camera-local SDK
  capability.
- Hardware tests are skipped unless `FLYCAPTURE2_HARDWARE_TEST=1`; write tests
  also require `FLYCAPTURE2_HARDWARE_WRITE_TEST=1`.

Current capabilities:

- lazy SDK/DLL discovery and loading
- camera enumeration, open/close lifecycle, and context-manager support
- start/stop capture and frame retrieval into owned NumPy arrays
- camera metadata, video mode, and frame-rate readback
- hardware trigger mode configuration without GUI
- software trigger firing without GUI
- Format7, ROI, and camera pixel-format configuration
- explicit pixel-format support matrix, including RGB8/RGB decode to owned
  `(height, width, 3)` `uint8` arrays
- SDK capture configuration, including grab timeout and grab mode
- generic FlyCapture2 property inspection and safe property writing
- embedded image metadata inspection/configuration and frame metadata readback
- camera diagnostic statistics readback, with write-gated stats reset support when the SDK exports it
- strobe source capability/readback and reversible strobe configuration
- direct GPIO pin-direction helpers where the FlyCapture2 C API exposes them
- GigE-specific config, property, image settings, binning, stream channel readback, and conservative same-value write tests
- convenience property methods for common controls such as exposure, shutter, gain, frame rate, brightness, gamma, white balance, trigger delay, and temperature readback
- mock camera support and default no-hardware tests
- opt-in hardware smoke, JSON capability reporting, and deterministic hardware validation suites

## Package Scope

Current package version: `0.6.0`.

Core runtime dependencies are intentionally limited to Python, `ctypes`, and
NumPy. The package discovery configuration includes only modules under `src/`;
vendor SDK DLLs and sample binaries are not bundled. Importing the package does
not load the FlyCapture2 DLL, enumerate cameras, open hardware, or require an
installed SDK.

Public API boundaries are documented in [docs/public_api.md](docs/public_api.md):

- stable high-level API: `Camera`, `enumerate_cameras`
- value dataclasses and enums returned by high-level methods
- typed high-level errors
- advanced/raw interfaces under `flycapture2_c.raw` and `flycapture2_c.api`
- compatibility test helpers: `MockCamera`, `open_mock_camera`

## Current Project Phase

The current major non-GUI camera-control surfaces are implemented for the
project scope: lifecycle, acquisition, trigger control, software trigger firing,
Format7/ROI/pixel format, SDK capture config, properties, embedded metadata,
diagnostics, strobe/GPIO, GigE controls, raw function specs, and hardware
validation tooling.

Active work is Stage 6.7: release candidate hardening and reproducibility. This
milestone audits public API boundaries, documentation, version metadata,
packaging, clean installs, artifact contents, and no-hardware CI reproducibility
without adding new SDK feature surface. Current hardware validation remains
limited to the available camera. Broader camera-model and multi-camera
validation is deferred until more hardware is available.

Default no-hardware validation:

```powershell
python -m pytest -q
python -c "import flycapture2_c; print('ok')"
python scripts/check_release.py
```

Readonly hardware validation:

```powershell
$env:FLYCAPTURE2_HARDWARE_TEST="1"
$env:FLYCAPTURE2_CAMERA_INDEX="0"
python scripts/hardware_capability_report.py --output outputs/capability_camera0.json
python scripts/run_hardware_validation.py
```

Write-gated hardware validation is deliberate and may be skipped during normal
development:

```powershell
$env:FLYCAPTURE2_HARDWARE_TEST="1"
$env:FLYCAPTURE2_HARDWARE_WRITE_TEST="1"
$env:FLYCAPTURE2_CAMERA_INDEX="0"
python scripts/run_hardware_validation.py --include-write
```

The project remains a FlyCapture2 C SDK wrapper, not an experiment framework,
camera server, GUI application, or acquisition workflow engine.

The implementation is moving toward a two-layer architecture:

- `flycapture2_c.raw`: low-policy ctypes aliases, structures, function specs, DLL binding, and checked raw calls
- high-level modules such as `Camera`, `trigger`, `format7`, `config`, and `properties`: stable task-oriented APIs for automated scripts

Default import remains lightweight:

```powershell
python -c "import flycapture2_c"
```

Importing the package does not load the vendor DLL, enumerate cameras, or require
the FlyCapture2 SDK to be installed.

Hardware smoke and hardware tests are opt-in. See
[docs/hardware_testing.md](docs/hardware_testing.md).

Project boundaries:

- no GUI or preview UI
- no sidecar process, IPC/shared memory, or ZMQ transport
- no `optic_system` backend code
- no LCD/projector synchronization
- no experiment scheduling, acquisition workflow orchestration, network service,
  calibration workflow, or reconstruction pipeline

This repository currently carries the active FlyCapture2 wrapper, tests, docs,
and hardware smoke tooling. A future distilled repository may be created from
this work, but the current repository remains scoped to the FlyCapture2 C SDK
wrapper and its own validation tools.

## License and vendor SDK boundary

This project is licensed under the MIT License.

The license applies only to the Python wrapper code, tests, examples, and
documentation in this repository. It does not grant any license to the
FlyCapture2 SDK, FlyCapture2 runtime DLLs, vendor headers, vendor libraries,
drivers, or sample binaries.

Users must install the FlyCapture2 SDK separately and make the FlyCapture2 C
runtime DLL discoverable through `FLYCAPTURE2_SDK_DIR`, `FLYCAPTURE2_DLL_DIR`,
or the system DLL search path. Wheels and source distributions for this project
must not bundle vendor SDK files.
