# Changelog

## Unreleased - Stage 6.8 Good-Host Capture-Rate Evidence

- Adds `scripts/measure_capture_rate.py`, a hardware validation tool that
  measures real-time frame acquisition rate through the existing `Camera` API.
- Adds opt-in hardware tests for capture-rate measurement and write-gated FPS
  matrix validation.
- Records good-host capture-rate evidence showing 5, 10, 15, 24, 30, and
  40 FPS reach SDK readback rates on the new machine.
- Documents host-limited FPS troubleshooting and the old-machine `pyflycap2`
  cross-check that reproduced the 5 FPS ceiling outside this wrapper.

This stage does not add FlyCapture2 SDK bindings, expand `Camera`, or add
experiment orchestration.

## Stage 6.7 Release Candidate Hardening And Reproducibility

- Hardens release reproducibility checks for default no-hardware tests, import
  smoke, wheel/sdist builds, artifact audits, and clean venv installs from both
  wheel and sdist.
- Adds Windows no-hardware CI coverage for Python 3.8 through 3.13.
- Freezes the `0.6.x` top-level `__all__` public export baseline against
  accidental deletion or renaming.
- Moves README quick-start material earlier: installation, separate FlyCapture2
  SDK installation, SDK/DLL environment variables, minimal enumeration/capture
  examples, and common diagnostics.

This stage does not add FlyCapture2 SDK bindings, expand `Camera`, or claim full
SDK coverage.

## 0.6.0 - Stage 6.6 Release Readiness And API Hardening

- Classifies the top-level public API into stable high-level names, value
  dataclasses/enums, advanced/raw interfaces, compatibility exports, and typed
  errors.
- Aligns project metadata and documentation with the current non-GUI
  FlyCapture2 C SDK wrapper scope.
- Documents the validation matrix for default no-hardware tests, readonly
  hardware checks, and deliberate write-gated hardware validation.
- Keeps SDK feature expansion paused while hardening release notes, package
  metadata, optional-symbol behavior, and no-hardware regression coverage.

## Implemented Milestones

- Initial lifecycle and frame acquisition: lazy DLL loading, camera
  enumeration, context-managed open/close, start/stop capture, and owned NumPy
  frame output.
- Trigger control: trigger mode info, readback, enable/disable, write support,
  and reversible hardware tests.
- Format7 / ROI / SDK capture config: camera-side ROI, pixel format, Format7
  validation/configuration, grab timeout, and grab mode.
- Property system: raw property access, safe generic property writes, snapshot
  helpers, and common convenience methods.
- Raw specs registry: current wrapped function signatures are centralized in
  `flycapture2_c.raw.specs` and used by the checked binding path.
- Embedded metadata and diagnostics: embedded image info, copied frame
  metadata, camera stats, and optional stats reset.
- Strobe / GPIO: strobe info/read/write, optional strobe broadcast, and direct
  GPIO pin-direction helpers where the C SDK exposes them.
- Software trigger firing: optional SDK fire calls exposed as camera-local
  primitives without scheduling or external-device coordination.
- GigE-specific controls: camera-local GigE configuration, properties, image
  settings, binning, stream-channel readback, and conservative validation.
- Hardware validation tooling: JSON capability reports and deterministic
  readonly/write-gated hardware validation runner.
- Stage 6.5 stabilization: current validation normalized around the available
  camera, with clean skips for unsupported features.

This changelog does not claim full FlyCapture2 SDK coverage or broad
camera-model compatibility. Current hardware validation evidence is limited to
the available camera.
