# flycapture2_c

`flycapture2_c` is a maintainable Python wrapper around the FlyCapture2 C API.
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

## Current Project Phase

The current major non-GUI camera-control surfaces are implemented for the
project scope: lifecycle, acquisition, trigger control, software trigger firing,
Format7/ROI/pixel format, SDK capture config, properties, embedded metadata,
diagnostics, strobe/GPIO, GigE controls, raw function specs, and hardware
validation tooling.

Active work is Stage 6.5: stabilization and hardware validation normalization
on the available camera. Routine validation uses:

```powershell
python scripts/hardware_capability_report.py --output outputs/capability_camera0.json
python scripts/run_hardware_validation.py
```

Broader camera-model validation is deferred until more hardware is available.
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
- no experiment scheduling, network service, calibration workflow, or reconstruction pipeline

This repository currently carries the active FlyCapture2 wrapper, tests, docs,
and hardware smoke tooling. A future distilled repository may be created from
this work, but the current repository remains scoped to the FlyCapture2 C API
wrapper and its own validation tools.
