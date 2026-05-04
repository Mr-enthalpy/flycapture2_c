# Project rules for flycapture2_c

This repository provides a Python wrapper around the FlyCapture2 C API.

The goal is to replace legacy `pyflycap2` / `PyCapture2` usage with a maintainable SDK wrapper that can later be used by `optic_system`.

## Primary scope

Implement a small, stable Python wrapper for the FlyCapture2 C API.

The first supported workflow is:

1. locate and load FlyCapture2 C DLL
2. enumerate cameras
3. open one camera
4. start capture
5. retrieve one or more frames
6. copy image data into owned NumPy arrays
7. stop capture
8. close camera safely

Do not attempt to bind the full SDK in the first implementation stage.

## API priority

Prefer the FlyCapture2 C API over the C++ API.

Use headers under:

```text
include/C/
````

especially:

```text
FlyCapture2_C.h
FlyCapture2Defs_C.h
FlyCapture2Platform_C.h
```

Do not bind the C++ API directly unless explicitly requested.

## Dependency boundary

This project must not depend on:

* optic_system
* PyQt / GUI frameworks
* torch
* OpenCV as a required dependency
* pyflycap2
* PyCapture2

Allowed core dependencies:

* Python standard library
* ctypes
* numpy
* pytest for tests
* pyyaml only for optional scripts/configs

## DLL handling

Do not commit vendor DLLs into this repository unless explicitly requested.

The SDK location must be provided by environment variable, normally:

```text
FLYCAPTURE2_SDK_DIR
```

Optional override:

```text
FLYCAPTURE2_DLL_DIR
```

DLL loading must be lazy.

Importing `flycapture2_c` must not require the FlyCapture2 SDK to be installed.

If the DLL cannot be found or loaded, raise a clear Python exception with actionable information.

## Hardware testing policy

Default tests must run without:

* camera hardware
* vendor DLL
* installed FlyCapture2 SDK

Hardware tests must be opt-in.

Use environment variables such as:

```text
FLYCAPTURE2_HARDWARE_TEST=1
FLYCAPTURE2_CAMERA_INDEX=0
```

No test may access real hardware unless explicitly enabled.

## Buffer ownership

Never expose SDK-owned image buffers directly to high-level callers.

Any public `read_frame()` API must return data that is safe after the next SDK call.

The default high-level frame output should be an owned NumPy array.

Document buffer lifetime assumptions in `docs/buffer_lifetime.md`.

## Threading and streaming

This wrapper is not responsible for GUI threading, shared memory, ZMQ, or experiment scheduling.

Continuous acquisition may be exposed as a simple iterator or repeated `read_frame()` loop, but this project must not implement the `optic_system` sidecar protocol.

The future `optic_system` integration should wrap this library inside its own camera service or sidecar.

## Public API design

Keep the high-level API narrow.

Recommended high-level usage:

```python
from flycapture2_c import Camera

cam = Camera.open(index=0)
cam.start()
frame = cam.read_frame()
cam.stop()
cam.close()
```

`close()` and `stop()` should be safe to call multiple times.

Avoid hidden global state.

Avoid opening hardware in constructors.

## Error handling

Every FlyCapture2 C API return code must be checked.

Convert SDK errors into typed Python exceptions.

Do not silently ignore SDK errors.

Do not crash the interpreter on recoverable SDK failures.

## Pixel format policy

Initial support should prioritize:

* mono8
* mono16
* raw8
* raw16

Bayer conversion, RGB conversion, debayering, and advanced image processing are out of scope for the first stage.

## Property API policy

Do not expand the property API into a full FlyCapture2 SDK surface unless the user explicitly requests that work.

The high-level property write API must stay intentionally limited and safety-checked.

Supported high-level property writes are restricted to:

- `AUTO_EXPOSURE`
- `SHUTTER`
- `GAIN`
- `FRAME_RATE`

Other property writes belong in the advanced low-level API only.

## Struct and ABI policy

All ctypes structures must be defined conservatively.

Do not guess complex SDK structures if they are not needed for the minimal acquisition path.

When a struct is added, include at least one no-hardware test that instantiates it and checks basic field accessibility.

Prefer incremental binding over broad automatic translation.

## Integration with optic_system

This repository should not import or modify `optic_system`.

Future integration should happen from the `optic_system` side through a backend such as:

```text
FlyCapture2CBackend
```

This project only provides the wrapper.

Do not implement GUI, control/session controller logic, shared memory, or experiment workflows here.

## Out of scope

Do not implement:

* full FlyCapture2 SDK coverage
* GUI preview
* camera sidecar protocol
* shared memory frame server
* ZMQ transport
* calibration workflow
* LCD synchronization
* neural network training
* image reconstruction
* hardware experiment scheduler

## Permanent out of scope

This project must never implement:

- GUI
- camera preview UI
- sidecar process protocol
- shared memory frame transport
- ZMQ / IPC transport
- optic_system backend classes
- experiment scheduling
- calibration workflow
- LCD / TLS synchronization
- neural network training
- data acquisition pipelines

Those responsibilities belong to downstream applications such as `optic_system`.

This repository only provides a FlyCapture2 C API Python wrapper and a narrow high-level Camera API.

## Long-term repository note

This repository may later be distilled into a separate, cleaner wrapper-only repository.

Until that migration explicitly happens, keep treating this repository as the active home for:

- the FlyCapture2 C API wrapper
- its tests
- its hardware smoke and verification scripts

That long-term plan does not authorize adding GUI, sidecar, IPC, `optic_system` backend code, or experiment workflow logic here.

## Coding style

Keep modules small.

Use explicit shape and dtype comments for frame arrays.

Prefer dataclasses for public data containers.

Prefer typed exceptions over bare `RuntimeError`.

Use clear function names mirroring SDK concepts where appropriate.

Do not hide expensive or hardware-touching operations behind import-time side effects.



suggestion `pyproject.toml` ：

```toml
[build-system]
requires = ["setuptools>=61", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "flycapture2-c"
version = "0.1.0"
description = "Minimal Python wrapper for the FlyCapture2 C API"
readme = "README.md"
requires-python = ">=3.9"
dependencies = [
    "numpy",
]

[project.optional-dependencies]
dev = [
    "pytest",
    "pyyaml",
]

[tool.setuptools]
package-dir = {"" = "src"}

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-q"
````

suggestion `.gitignore`：

```gitignore
__pycache__/
*.py[cod]
*.pyd
*.so
*.dll
*.lib
*.exp

.venv/
venv/
.env

.pytest_cache/
.mypy_cache/
.ruff_cache/

build/
dist/
*.egg-info/

outputs/
data/
hardware_logs/
frames/

.DS_Store
Thumbs.db
```
