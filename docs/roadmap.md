# Roadmap

This roadmap describes the current implementation state and the next expansion
order. It is not a claim of full FlyCapture2 SDK coverage.

## Stage 0: Documentation and API Coverage

Status: partially complete.

- `docs/api_coverage.md` tracks currently wrapped functions.
- `docs/api_mapping.md`, `docs/recipes.md`, `docs/hardware_testing.md`, and
  migration notes exist and are maintained.
- Coverage still needs to become more systematic as raw SDK coverage grows.

## Stage 1: Raw Binding Infrastructure

Status: incomplete and now prioritized.

The repository historically grew through top-level `ctypes_defs.py` and
`api.py`. The intended direction is a dedicated raw package:

- `raw/types.py`: primitive ctypes aliases
- `raw/structs.py`: SDK ctypes structures
- `raw/specs.py`: function signature registry
- `raw/library.py`: DLL loading and signature binding
- `raw/api.py`: checked low-level calls

Stage 4.5 started this work by adding the package skeleton and moving current
function signatures into `raw/specs.py`. Future SDK expansion should continue
using this registry instead of extending monolithic binding blocks.

## Stage 2: Lifecycle and Acquisition

Status: complete for the current project stage.

- lazy DLL loading
- camera enumeration
- open/close lifecycle
- context manager support
- start/stop capture
- single-frame and repeated `read_frame()` usage
- owned NumPy frame output
- mock backend and default no-hardware tests

## Stage 3: Trigger, Format7, ROI, Pixel Format, and Capture Config

Status: complete for the current project stage.

- trigger mode info/read/write
- trigger enable/disable
- Format7 info, validation, current configuration, and write path
- camera-side ROI and pixel-format configuration
- SDK capture configuration, grab timeout, and grab mode
- opt-in reversible hardware tests for write paths

Software trigger firing is intentionally not included yet.

## Stage 4: Property System

Status: complete for the current project stage.

- all known `PropertyType` values are queryable through discovery helpers
- raw property access remains available for advanced callers
- generic safe helpers validate support, writability, modes, and ranges
- convenience methods cover common camera controls
- trigger delay is part of the property API
- trigger mode remains a dedicated trigger API

## Stage 4.5: Architecture and Documentation Stabilization

Status: complete for the current project stage.

Implemented:

- align README and docs with actual capabilities
- add the raw package skeleton
- centralize current function signatures in `raw/specs.py`
- keep existing public imports compatible
- avoid new SDK feature surface while preparing for future raw expansion

## Stage 5A: Embedded Metadata and Diagnostics

Status: complete.

- embedded image info availability and enabled-state readback
- reversible embedded metadata enable/disable API
- copied frame metadata on `ImageFrame.metadata`
- camera diagnostic stats readback
- write-gated diagnostic stats reset when the SDK exports `ResetStats()`
- opt-in readonly and write-gated hardware tests

Reading embedded strobe/GPIO metadata values is part of image metadata only; it
does not implement strobe/GPIO control.

## Stage 5B: Strobe and GPIO

Status: complete for the current project stage.

Implemented:

- strobe info/read/write wrappers from the FlyCapture2 C headers
- GPIO pin-direction read/write helpers where the C API exposes them directly
- reversible, opt-in hardware write tests for any write path
- no GUI, sidecar, IPC, or experiment workflow code

GPIO pin-state observation remains part of embedded image metadata. Broader GPIO
behavior through register access is intentionally deferred.

## Stage 6+: Future Expansion

Prioritized future areas:

- GigE-specific controls
- task-level acquisition helpers, such as bounded frame iterators and restore-state patterns
- register access as an advanced API
- callbacks and events
- broader raw FlyCapture2 C SDK coverage
- release stabilization and migration documentation

Deferred areas remain outside this project:

- GUI or preview UI
- sidecar process, shared memory, ZMQ, or IPC transport
- `optic_system` backend implementation
- experiment scheduling
- calibration workflow
- image reconstruction
