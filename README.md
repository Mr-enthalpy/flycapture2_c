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

Current stage: Stage 6.5 systematic testing and hardware qualification is
complete for the current project stage. SDK feature expansion is paused for this
stabilization milestone.

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
