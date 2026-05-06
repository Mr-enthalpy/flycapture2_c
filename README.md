# flycapture2_c

`flycapture2_c` is a maintainable Python wrapper around the FlyCapture2 C SDK.
It is intended to replace legacy `pyflycap2` / `PyCapture2` usage with a
scriptable, non-GUI SDK wrapper.

Current capabilities:

- lazy SDK/DLL discovery and loading
- camera enumeration, open/close lifecycle, and context-manager support
- start/stop capture and frame retrieval into owned NumPy arrays
- camera metadata, video mode, and frame-rate readback
- hardware trigger mode configuration without GUI
- software trigger firing without GUI
- Format7, ROI, and camera pixel-format configuration
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

Active work is Stage 6.6: release readiness and API hardening. This milestone
audits public API boundaries, documentation, version metadata, packaging, and
validation workflows without adding new SDK feature surface. Current hardware
validation remains limited to the available camera. Broader camera-model and
multi-camera validation is deferred until more hardware is available.

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
