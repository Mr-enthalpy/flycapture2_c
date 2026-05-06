# Project rules for flycapture2_c

This repository provides a maintainable Python wrapper around the FlyCapture2 C SDK.

The strategic goal is to replace legacy `pyflycap2` / `PyCapture2` usage with a non-GUI, scriptable, testable SDK wrapper. The wrapper must support complete camera lifecycle management, acquisition control, camera configuration, trigger control, pixel format control, and gradual expansion toward broad FlyCapture2 C API coverage.

The design target is not to reproduce the old `pyflycap2.interface.Camera + GUI` workflow. In particular, automated code must not require GUI operations to configure trigger mode, pixel format, ROI, acquisition mode, exposure, gain, frame rate, or other camera parameters that the vendor SDK exposes programmatically.

## Core design principle

Use a two-layer architecture:

1. `raw` layer:
   - close to the FlyCapture2 C API
   - broad SDK coverage
   - low policy
   - explicit ctypes structures and function signatures
   - every SDK return code checked
   - suitable for advanced users and future API expansion

2. high-level layer:
   - stable Pythonic `Camera` API
   - task-oriented methods
   - lifecycle-safe
   - no GUI
   - no hidden hardware side effects at import time
   - suitable for experiment scripts and downstream libraries

The raw layer may grow toward near-complete SDK coverage. The high-level layer should remain curated and task-oriented.

## Current phase

The active project phase is Stage 6.6: release readiness and API hardening.

Do not add new SDK feature surface unless explicitly requested. Prefer:

- auditing public API boundaries
- improving package metadata and version consistency
- updating changelog and release documentation
- fixing hardware-test failures
- improving capability reports
- updating documentation
- strengthening no-hardware regression tests
- improving skip/error semantics for unsupported camera features

Current hardware validation is limited to the available camera. Do not require
or assume additional camera models. Multi-camera and multi-model validation is
future work.

Keep the experiment orchestration boundary strong. Do not add GUI, sidecar,
shared memory, ZMQ/IPC, `optic_system`, LCD/projector synchronization,
experiment scheduling, or acquisition workflow APIs.

## Primary scope

The repository is responsible for:

1. locating and lazily loading the FlyCapture2 C DLL
2. enumerating cameras
3. opening and closing cameras safely
4. starting and stopping capture
5. retrieving frames
6. copying SDK-owned image data into owned NumPy arrays
7. reading camera metadata
8. reading and writing camera properties
9. configuring trigger mode without GUI
10. configuring pixel format, Format7, and ROI without GUI
11. configuring capture behavior, grab timeout, and buffer policy
12. exposing selected software trigger firing, GigE, strobe, GPIO, embedded metadata, and diagnostic APIs
13. maintaining hardware smoke tests and no-hardware unit tests
14. documenting API coverage and migration from legacy wrappers

This repository is not an experiment framework, GUI application, camera server, sidecar process, reconstruction pipeline, or optical system controller.

## Non-goals

Do not implement:

- GUI
- camera preview UI
- PyQt / Qt integration
- sidecar process protocol
- shared memory frame transport
- ZMQ / IPC transport
- `optic_system` backend classes
- LCD synchronization
- experiment scheduling
- calibration workflow
- neural network training
- image reconstruction
- full data acquisition pipeline orchestration

Those responsibilities belong to downstream projects.

This repository only provides the FlyCapture2 C SDK wrapper and its own tests, hardware smoke tooling, and documentation.

## SDK API preference

Prefer the FlyCapture2 C API over the FlyCapture2 C++ API.

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

Do not guess SDK structure layouts. All ctypes structures must be derived from the vendor C headers.

## Package architecture

The `raw/` package is a near-term architecture debt that must be paid down before
new SDK areas are added. Do not continue adding function signatures directly to
top-level `api.py` or expanding `ctypes_defs.py` as a monolithic binding surface.
New raw SDK work should land in the raw-layer modules below, with compatibility
bridges only where needed to preserve existing imports.

Target package structure:

```text
src/flycapture2_c/
    __init__.py

    camera.py
    bus.py
    image.py
    pixel_format.py
    properties.py
    trigger.py
    format7.py
    config.py
    gige.py
    strobe.py
    metadata.py
    register.py
    errors.py
    dll.py
    typing.py

    raw/
        __init__.py
        types.py
        enums.py
        structs.py
        specs.py
        library.py
        api.py
```

Layer responsibilities:

```text
raw/types.py       primitive ctypes aliases
raw/enums.py       SDK enum values
raw/structs.py     ctypes.Structure definitions
raw/specs.py       function signature registry
raw/library.py     DLL loading and binding
raw/api.py         low-level checked API calls

camera.py          high-level Camera lifecycle and acquisition API
trigger.py         trigger mode and trigger mode info
format7.py         Format7, ROI, pixel format configuration
config.py          capture config, grab timeout, buffer policy
gige.py            GigE-specific configuration
strobe.py          strobe / GPIO control
metadata.py        embedded image info, timestamps, camera stats
register.py        low-level register access
```

Avoid turning `camera.py` or `api.py` into a monolithic binding file.

## Public API direction

The recommended high-level usage should remain simple:

```python
from flycapture2_c import Camera

with Camera.open(index=0) as cam:
    cam.start()
    frame = cam.read_frame()
```

The high-level API should also support non-GUI camera configuration:

```python
from flycapture2_c import Camera

with Camera.open(0) as cam:
    cam.set_pixel_format("MONO8")
    cam.set_roi(offset_x=0, offset_y=0, width=1024, height=768)
    cam.set_shutter(5.0, auto=False)
    cam.set_gain(0.0, auto=False)
    cam.enable_trigger(source=0, polarity=1)
    cam.start()
    frame = cam.read_frame()
```

No high-level configuration operation should require GUI fallback if the vendor SDK exposes the operation programmatically.

## Lifecycle policy

`Camera` must maintain a clear state model:

```text
closed
  -> opened
  -> capturing
  -> opened
  -> closed
```

Required behavior:

* opening hardware must not happen in `__init__`
* use `Camera.open(...)` or explicit `open(...)`
* `close()` must be safe to call multiple times
* `stop()` must be safe to call multiple times
* reading a frame before `start()` must raise a typed state error
* starting an already started camera should be idempotent unless the SDK requires otherwise
* SDK resources must be released on exceptions during open
* context manager support is required

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

## Dependency boundary

Allowed core dependencies:

* Python standard library
* ctypes
* numpy

Allowed development or optional dependencies:

* pytest
* pyyaml for optional scripts/config files

Do not require:

* PyQt
* Qt
* GUI frameworks
* OpenCV
* torch
* pyflycap2
* PyCapture2
* optic_system
* ZMQ
* shared-memory IPC libraries

Optional extras may be introduced only when they do not affect the core import path.

## Python version policy

Support Python 3.8+ unless the project explicitly raises the minimum version.

Do not use syntax or standard-library features unavailable in the configured minimum Python version.

## Error handling

Every FlyCapture2 C API return code must be checked.

Convert SDK errors into typed Python exceptions.

Do not silently ignore SDK errors except in narrowly defined cleanup paths where the operation is already known to be idempotent, such as suppressing expected “not connected” or “capture not started” errors during cleanup.

Do not crash the interpreter on recoverable SDK failures.

Prefer typed exceptions over bare `RuntimeError`.

## Buffer ownership

Never expose SDK-owned image buffers directly to ordinary high-level callers.

Any public `read_frame()` API must return data that remains valid after the next SDK call.

The default high-level frame output must be an owned NumPy array.

A lower-level zero-copy or SDK-buffer view API may be introduced only if:

* its lifetime contract is explicit
* it is clearly marked advanced or unsafe
* tests document the invalidation behavior

Document buffer lifetime assumptions in `docs/buffer_lifetime.md`.

## Pixel format policy

Initial and stable decoded formats should include:

* `MONO8`
* `MONO16`
* `RAW8`
* `RAW16`

Distinguish between:

1. SDK pixel formats that can be configured on the camera
2. pixel formats that the wrapper can decode into structured NumPy arrays

It is acceptable to allow setting a pixel format before the wrapper supports rich decoding for that format, but frame retrieval must then either:

* return a raw copied payload with metadata through an explicit raw API, or
* raise a clear `UnsupportedPixelFormatError`

Do not silently reinterpret unknown pixel formats.

## Property API policy

The property API must no longer be limited to only four high-level writable properties.

Use a three-level model:

1. raw property access:

   * close to `fc2Property`
   * advanced users may set SDK fields directly
   * still check SDK return codes

2. generic safe property helpers:

   * range-checked
   * capability-checked
   * supports absolute values, integer values, on/off, auto/manual, one-push where available

3. convenience methods:

   * common camera controls such as shutter, gain, frame rate, brightness, gamma, white balance, exposure

The previous high-level convenience methods should remain:

```python
cam.set_exposure(...)
cam.set_shutter(...)
cam.set_gain(...)
cam.set_frame_rate(...)
```

Additional methods may be added:

```python
cam.set_brightness(...)
cam.set_gamma(...)
cam.set_white_balance(...)
cam.set_property_abs(...)
cam.set_property_raw(...)
```

Trigger mode should not be treated primarily as a generic property when the SDK provides dedicated trigger structures and functions.

## Trigger API policy

Trigger control is a core feature.

The wrapper must expose trigger configuration without GUI.

Required high-level direction:

```python
cam.get_trigger_mode_info()
cam.get_trigger_mode()
cam.set_trigger_mode(...)
cam.enable_trigger(...)
cam.disable_trigger()
cam.fire_software_trigger()
```

The implementation should bind SDK structures and functions such as trigger mode, trigger mode info, get trigger mode, set trigger mode, and get trigger mode info according to the vendor C headers.

Software trigger firing is Stage 6A. It should expose only the FlyCapture2 C SDK
primitive needed to fire a software trigger after software trigger mode is
configured. Do not turn software trigger firing into an experiment scheduler,
external-device synchronization layer, GUI workflow, sidecar, shared-memory
transport, ZMQ/IPC workflow, or `optic_system` backend.

Trigger tests must include:

* no-hardware struct instantiation and field access
* hardware readonly trigger info smoke test
* opt-in reversible hardware write test:

  * save old trigger state
  * write new trigger state
  * read back
  * restore old state

## Format7, ROI, and pixel format policy

Format7 and ROI configuration are core features because many automated experiments need to configure image size and pixel format without GUI.

Required high-level direction:

```python
cam.get_format7_info(...)
cam.get_format7_configuration()
cam.validate_format7(...)
cam.set_format7(...)
cam.set_roi(...)
cam.set_pixel_format(...)
```

Do not implement ROI as a purely Python-side crop when the camera SDK supports sensor/stream ROI configuration.

Python-side crop may exist only as a separate image utility and must not be confused with camera ROI.

## Capture config policy

Expose SDK-level acquisition configuration where needed.

Required direction:

```python
cam.get_configuration()
cam.set_configuration(...)
cam.set_grab_timeout(ms)
cam.set_grab_mode(...)
```

Do not confuse SDK-level grab timeout with outer Python wall-clock timeout.

If scripts use Python-side timing guards, document that they are not SDK grab timeout configuration.

## GigE, strobe, GPIO, and metadata policy

These APIs are important but lower priority than lifecycle, trigger, Format7, ROI, pixel format, config, and property control.

Expose them incrementally.

Recommended high-level direction:

```python
cam.get_gige_config()
cam.set_gige_config(...)

cam.get_strobe_info(...)
cam.get_strobe(...)
cam.set_strobe(...)

cam.get_embedded_image_info()
cam.set_embedded_image_info(...)

cam.get_camera_stats()
```

All write APIs must support reversible hardware tests when possible.

## Register API policy

Register access is advanced and potentially hazardous.

Expose register access in a clearly marked low-level or advanced module.

Do not promote register operations into the ordinary high-level API unless there is a stable, documented use case.

Required direction:

```python
cam.read_register(address)
cam.write_register(address, value)
```

Write operations must be explicit and must not be hidden inside convenience methods unless the behavior is documented and tested.

## API coverage tracking

Maintain `docs/api_coverage.md`.

The coverage table should classify SDK functions by category and status:

```text
Category
Function
Structs required
Raw binding status
High-level API status
No-hardware test status
Hardware readonly test status
Hardware write test status
Notes
```

Suggested statuses:

```text
uninvestigated
structs-defined
raw-bound
raw-tested
high-level-planned
high-level-implemented
hardware-readonly-tested
hardware-write-tested
deferred
not-applicable
```

Adding a new SDK function should normally update this document.

## Roadmap

Maintain `docs/roadmap.md`.

Recommended staged roadmap:

```text
Stage 0  project direction, documentation, API coverage table
Stage 1  raw binding infrastructure
Stage 2  lifecycle and acquisition stability
Stage 3  trigger, Format7, ROI, pixel format, capture config
Stage 4  full property system
Stage 4.5 architecture/documentation stabilization:
          README sync, docs/roadmap.md, raw binding infrastructure,
          API coverage consistency, no new hardware feature surface
Stage 5A embedded metadata and diagnostics
Stage 5B strobe / GPIO
Stage 6A software trigger firing
Stage 6B GigE-specific controls
Stage 6.5 stabilization and hardware validation normalization
Stage 6.6 release readiness and API hardening, current active phase
Stage 7+ future SDK expansion only when explicitly re-scoped
```

Prioritize APIs that remove GUI dependency from automated scripts.

During Stage 6.6, SDK expansion is paused unless explicitly requested. Roadmap
work should focus on release readiness, API consistency, packaging/version
metadata, documentation, no-hardware regression coverage, and validation
workflow clarity.

Priority order:

1. lifecycle and frame acquisition
2. trigger control
3. pixel format and Format7 / ROI
4. SDK capture config and grab timeout
5. complete property access
6. embedded metadata
7. strobe / GPIO
8. software trigger firing
9. GigE-specific controls
10. register access
11. callbacks and advanced event mechanisms

## Hardware testing policy

Default tests must run without:

* camera hardware
* vendor DLL
* installed FlyCapture2 SDK

Hardware tests must be opt-in.

Hardware is available for long-term validation, but default tests must remain
no-hardware and no-SDK. Readonly hardware tests should be run for
hardware-facing PRs when available. Write hardware tests remain gated by
`FLYCAPTURE2_HARDWARE_WRITE_TEST=1`.

Use environment variables such as:

```text
FLYCAPTURE2_HARDWARE_TEST=1
FLYCAPTURE2_HARDWARE_WRITE_TEST=0|1
FLYCAPTURE2_CAMERA_INDEX=0
FLYCAPTURE2_FRAME_COUNT=30
FLYCAPTURE2_CAPTURE_TIMEOUT_MS=...
```

No test may access real hardware unless explicitly enabled.

No test may write camera state unless write testing is explicitly enabled.

Writable hardware tests must normally:

1. read original state
2. apply test state
3. verify readback
4. restore original state
5. verify restoration where possible

## No-hardware testing policy

For every new ctypes structure:

* instantiate it
* check basic field access
* check array fields where relevant
* check pointer fields where relevant
* avoid relying on camera hardware

For every new function binding:

* verify the function spec exists
* verify `argtypes` and `restype` are assigned
* verify wrapper code checks SDK return values

Use fake DLL or mock callable objects where useful.

## ABI and ctypes policy

All ctypes structures must be defined conservatively.

Do not guess complex SDK structures.

When adding a structure:

* copy field names from the vendor C header
* preserve field order
* use correct integer widths
* include reserved fields
* add a no-hardware test
* document uncertainty if the SDK version differs

When a structure is SDK-version-sensitive, isolate it and document the SDK version used.

Do not use broad automatic translation unless the generated output is reviewed and tested.

## Threading and streaming

The wrapper is not responsible for GUI threading, shared memory, ZMQ, or experiment scheduling.

Continuous acquisition should remain explicit repeated `read_frame()` calls
unless a future milestone deliberately scopes a camera-local helper.

Do not implement a background acquisition daemon unless explicitly requested.

If background acquisition is added later, it must be optional, documented, and independent from the core synchronous API.

## Import behavior

Importing `flycapture2_c` must be lightweight.

Import must not:

* load the vendor DLL
* enumerate cameras
* open hardware
* start capture
* require SDK installation

Hardware-touching behavior must happen only through explicit calls.

## Compatibility and migration

Maintain `docs/migration_from_pyflycap2.md`.

The migration guide should show how to replace legacy patterns such as:

```python
from pyflycap2.interface import Camera, GUI
```

with direct non-GUI configuration:

```python
from flycapture2_c import Camera

with Camera.open(0) as cam:
    cam.set_pixel_format("MONO8")
    cam.enable_trigger(source=0)
    cam.start()
    frame = cam.read_frame()
```

Do not preserve legacy API defects for compatibility.

A thin compatibility layer may be added later, but it must not reintroduce GUI dependency.

## Documentation requirements

Maintain documentation for:

```text
docs/roadmap.md
docs/api_coverage.md
docs/hardware_testing.md
docs/buffer_lifetime.md
docs/migration_from_pyflycap2.md
docs/recipes.md
```

`docs/recipes.md` should eventually include:

* enumerate cameras
* open camera
* grab one frame
* grab short sequence
* fixed shutter/gain acquisition
* disable auto exposure
* configure hardware trigger
* configure software trigger
* fire software trigger
* configure MONO8 / MONO16 / RAW8 / RAW16
* configure ROI
* configure grab timeout
* restore original camera state

## Coding style

Keep modules small.

Prefer dataclasses for public value containers.

Prefer enums for SDK enum values.

Use explicit names mirroring SDK concepts where appropriate.

Avoid hidden global state.

Avoid hardware side effects in constructors.

Avoid expensive side effects at import time.

Use type annotations.

Keep high-level methods readable and task-oriented.

Do not hide SDK-level failure modes behind vague exceptions.

## Versioning direction

Suggested version milestones:

```text
0.1.x  minimal lifecycle and frame acquisition
0.2.x  raw binding infrastructure, trigger, Format7, ROI, pixel format, capture config
0.3.x  complete property system
0.4.x  embedded metadata, strobe, GPIO, GigE basics
0.5.x  software trigger, GigE controls, hardware validation tooling, migration documentation
0.6.0  current Stage 6.6 release-readiness and API-hardening snapshot
1.0.0  stable high-level API, documented migration path, tested hardware workflows
```

Do not claim full SDK coverage until `docs/api_coverage.md` supports that claim.

## Review checklist for new PRs

Before accepting changes, check:

1. Does import still avoid loading the SDK DLL?
2. Are all SDK error codes checked?
3. Are new ctypes structures derived from vendor headers?
4. Are new structures covered by no-hardware tests?
5. Does any hardware test remain opt-in?
6. Does any write test save and restore prior camera state?
7. Does the change avoid GUI dependency?
8. Does the change avoid downstream experiment logic?
9. Is buffer ownership clear?
10. Is `docs/api_coverage.md` updated for new SDK functions?
11. Is the high-level API task-oriented rather than a blind SDK dump?
12. Does raw coverage grow without destabilizing `Camera`?
13. Does the change help remove legacy `pyflycap2` / GUI workflow dependency?

## Permanent rule

Never require GUI interaction for a camera configuration task that the FlyCapture2 C SDK exposes programmatically.

The wrapper exists specifically to make FlyCapture2 camera control scriptable, inspectable, testable, and maintainable from Python.

## Experiment orchestration boundary

Do not add task-level acquisition orchestration to this repository.

Allowed:
- direct SDK-level camera operations
- camera-local getters/setters
- frame retrieval primitives
- explicit state read/write primitives
- hardware smoke tests for those primitives

Not allowed:
- experiment sessions
- workflow runners
- multi-device synchronization
- LCD/projector coordination
- GUI preview workflows
- sidecar/server modes
- shared memory or ZMQ transports
- `optic_system` adapters
- automatic acquisition pipelines

State-save/restore logic may appear inside tests to keep hardware safe, but it should not become a public experiment orchestration API unless explicitly re-scoped.
