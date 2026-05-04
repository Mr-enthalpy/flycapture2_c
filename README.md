# flycapture2_c

`flycapture2_c` is a narrow Python wrapper around the FlyCapture2 C API.

Scope:

- lazy DLL discovery and loading
- camera enumeration and open/close
- frame capture into owned NumPy arrays
- limited camera metadata access
- intentionally limited property access

Property writing is intentionally limited. The high-level API only provides strict convenience setters for:

- `AUTO_EXPOSURE`
- `SHUTTER`
- `GAIN`
- `FRAME_RATE`

This repository does not provide GUI code, sidecar processes, IPC/shared memory, ZMQ transport, `optic_system` backends, or experiment workflows.

Hardware smoke and hardware tests are opt-in. See [docs/hardware_testing.md](docs/hardware_testing.md).

Long-term note:

- this repository currently carries the active FlyCapture2 wrapper, tests, and hardware smoke tooling
- later we may distill the wrapper into a separate, cleaner repository
- that future migration does not change the current scope here: this project remains a FlyCapture2 C API wrapper plus its tests and smoke scripts
