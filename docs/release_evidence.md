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

