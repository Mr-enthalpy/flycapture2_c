# Release Evidence

This document records release-candidate validation evidence. It is not a claim
of full FlyCapture2 SDK coverage or broad camera-model compatibility.

## Stage 6.7 / 0.6.0 RC

Date: 2026-05-06

Environment:

- OS: Microsoft Windows NT 10.0.26120.0
- Python: 3.13.5
- FlyCapture2 library version: 2.13.3.61
- Camera: Grasshopper3 GS3-U3-51S5C
- Serial: 15471217
- Interface type: 1, USB
- Driver: USB Camera Driver (PGRUsbCam.sys) - 2.7.3.235
- Firmware: 2.22.3.0
- Sensor: Sony IMX250 (2/3" Color CMOS), 2448x2048

No-hardware release checks:

- `python scripts/check_release.py`: passed
- default pytest: 146 passed, 28 skipped
- import smoke: `0.6.0`
- wheel audit: passed, no vendor DLLs, headers, drivers, sample binaries,
  `third_party/`, or `outputs/`
- sdist audit: passed, no vendor DLLs, headers, drivers, sample binaries,
  `third_party/`, or `outputs/`
- clean venv install from wheel: passed
- clean venv install from sdist: passed

Local no-hardware matrix:

- Python 3.13: passed, 146 passed and 28 skipped
- Python 3.8: local dependency install failed before tests while pip attempted
  to fetch build dependencies through the local TLS/network stack
- Python 3.9, 3.10, 3.11, 3.12: not installed locally
- GitHub Actions is configured as the authoritative Windows Python 3.8-3.13
  no-hardware matrix

Readonly hardware validation:

- Capability report command:
  `python scripts/hardware_capability_report.py --output outputs/stage_6_7_capability_camera0.json`
- Capability report result: passed
- Validation command: `python scripts/run_hardware_validation.py`
- Validation result: 9/9 readonly groups passed
- Clean skips: GigE-specific checks skipped because the connected camera is USB;
  unsupported strobe/software-trigger write-like paths skipped cleanly

Write-gated hardware validation:

- Not run for Stage 6.7 evidence because this change set did not modify hardware
  write behavior
- Write-gated validation remains available only with both
  `FLYCAPTURE2_HARDWARE_TEST=1` and `FLYCAPTURE2_HARDWARE_WRITE_TEST=1`

## Stage 6.8 / 0.6.0 Good-Host Capture-Rate Evidence

Date: 2026-05-07

Scope:

- Stage 6.8 is hardware evidence and capture-rate validation on a new host.
- It does not add FlyCapture2 SDK bindings and does not expand the high-level
  `Camera` API.
- The previous 5 FPS ceiling observed on the old host was reproduced with
  `pyflycap2`, so it is classified as a host/driver/USB environment issue, not
  a `flycapture2_c` wrapper defect.

Environment:

- OS: Windows 11 10.0.26200
- Python: 3.12.0, 64-bit
- FlyCapture2 SDK path: `D:\Program Files\Point Grey Research\FlyCapture2`
- FlyCapture2 library version: 2.13.3.61
- Camera: Grasshopper3 GS3-U3-51S5C
- Serial: 15471217
- Interface type: 2, USB
- Driver: USB Camera Driver (PGRUsbCam.sys) - 2.7.3.235
- Firmware: 2.22.3.0
- Sensor: Sony IMX250 (2/3" Color CMOS), 2448x2048
- Format7: mode 0, 2448x2048, RAW8, packet size 47728

No-hardware checks:

- `python -m pip install -e ".[dev]"`: blocked on this machine because the
  configured pip proxy could not fetch build dependencies for the default
  32-bit Python 3.8 environment.
- `py -3.12 -m pip install --no-build-isolation -e ".[dev]"`: exposed a local
  setuptools metadata validation issue for `project.license = "MIT"`.
- `py -3.12 -m pytest -q` with `PYTHONPATH=src`: passed, 146 passed and
  30 skipped.
- `py -3.12 scripts/check_release.py` with `PYTHONPATH=src`: pytest and import
  smoke passed, then failed because the local Python 3.12 environment does not
  have the optional `build` package installed.
- Import smoke: `0.6.0`.

Readonly hardware checks:

- Capability report:
  `py -3.12 scripts/hardware_capability_report.py --output outputs/stage_6_8_good_host_capability_camera0.json`
- Capability report result: passed, one camera found, no report errors.
- `scripts/run_hardware_validation.py` initially timed out because the camera
  was left in trigger-enabled mode and readonly grab tests cannot receive
  free-running frames in that state.
- Readonly validation was then run under a write-gated outer safety wrapper
  that saved trigger/config/frame-rate state, temporarily disabled trigger and
  set SDK grab timeout, ran `scripts/run_hardware_validation.py`, then restored
  the original state.
- Validation result: 9/9 readonly groups passed; GigE-only checks skipped
  cleanly for the USB camera.

Capture-rate validation:

- Baseline command:
  `py -3.12 scripts/measure_capture_rate.py --duration 10 --warmup 10 --output outputs/capture_rate_baseline_good_host.json`
- Because the original trigger mode was enabled, baseline capture-rate
  measurement was run with `FLYCAPTURE2_HARDWARE_WRITE_TEST=1`; the script
  saved state, disabled trigger for continuous capture, enabled the current
  frame-rate readback for measurement, and restored the original state.
- Baseline result: requested/readback 20.0044 FPS, actual 20.0088 FPS,
  ratio 1.0002, 201 frames in 10.0456 s, RAW8 2448x2048, about 95.67 MiB/s,
  no timeout, no stall, no SDK errors, restore verification passed.

Configured FPS matrix:

| Requested FPS | SDK readback FPS | Actual FPS | Actual/readback | Frames | MiB/s | Timeout/stall |
| ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 5 | 5 | 5.0024 | 1.0005 | 51 | 23.92 | no/no |
| 10 | 10 | 10.0046 | 1.0005 | 101 | 47.83 | no/no |
| 15 | 15 | 15.0057 | 1.0004 | 151 | 71.75 | no/no |
| 24 | 24 | 24.0072 | 1.0003 | 241 | 114.78 | no/no |
| 30 | 30 | 30.0134 | 1.0004 | 301 | 143.50 | no/no |
| 40 | 40 | 40.0205 | 1.0005 | 401 | 191.35 | no/no |

All configured rates from 5 FPS through 40 FPS were supported on the new host
and matched SDK readback within about 0.1%. This confirms that the old-machine
5 FPS ceiling was host-limited rather than a wrapper acquisition defect.

