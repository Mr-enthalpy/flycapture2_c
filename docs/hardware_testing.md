# Hardware Testing

Hardware access is always opt-in.

Stage 5A embedded metadata and diagnostics hardware coverage is present. The
next hardware-facing stage is Stage 5B strobe/GPIO.

Environment variables:

- `FLYCAPTURE2_HARDWARE_TEST=1`
- `FLYCAPTURE2_HARDWARE_WRITE_TEST=0|1`
- `FLYCAPTURE2_CAMERA_INDEX=0`
- `FLYCAPTURE2_FRAME_COUNT=30`
- `FLYCAPTURE2_CAPTURE_TIMEOUT_MS=...`

Examples:

```powershell
FLYCAPTURE2_HARDWARE_TEST=1 python scripts/hardware_smoke.py --level readonly --report-json outputs/readonly.json
FLYCAPTURE2_HARDWARE_TEST=1 python scripts/hardware_smoke.py --level grab-one --save-frame outputs/frame.npy --report-json outputs/grab_one.json
FLYCAPTURE2_HARDWARE_TEST=1 python scripts/hardware_smoke.py --level grab-sequence --report-json outputs/sequence.json
```

Optional reversible property write check:

```powershell
FLYCAPTURE2_HARDWARE_TEST=1
FLYCAPTURE2_HARDWARE_WRITE_TEST=1
python scripts/hardware_smoke.py --level write-property --report-json outputs/write_property.json
```

Trigger control hardware tests:

```powershell
FLYCAPTURE2_HARDWARE_TEST=1 python -m pytest tests/hardware/test_hardware_trigger_readonly.py

FLYCAPTURE2_HARDWARE_TEST=1
FLYCAPTURE2_HARDWARE_WRITE_TEST=1
python -m pytest tests/hardware/test_hardware_trigger_write_reversible.py
```

Format7 / ROI / SDK configuration hardware tests:

```powershell
FLYCAPTURE2_HARDWARE_TEST=1 python -m pytest tests/hardware/test_hardware_format7_readonly.py

FLYCAPTURE2_HARDWARE_TEST=1
FLYCAPTURE2_HARDWARE_WRITE_TEST=1
python -m pytest tests/hardware/test_hardware_format7_write_reversible.py

FLYCAPTURE2_HARDWARE_TEST=1
FLYCAPTURE2_HARDWARE_WRITE_TEST=1
python -m pytest tests/hardware/test_hardware_config_write_reversible.py
```

Property system hardware tests:

```powershell
FLYCAPTURE2_HARDWARE_TEST=1 python -m pytest tests/hardware/test_hardware_properties_readonly.py

FLYCAPTURE2_HARDWARE_TEST=1
FLYCAPTURE2_HARDWARE_WRITE_TEST=1
python -m pytest tests/hardware/test_hardware_properties_write_reversible.py
```

Embedded metadata and diagnostics hardware tests:

```powershell
FLYCAPTURE2_HARDWARE_TEST=1 python -m pytest tests/hardware/test_hardware_metadata_readonly.py

FLYCAPTURE2_HARDWARE_TEST=1
FLYCAPTURE2_HARDWARE_WRITE_TEST=1
python -m pytest tests/hardware/test_hardware_metadata_write_reversible.py
```

Notes:

- default `pytest` skips all hardware tests
- property write tests require both hardware opt-in flags
- trigger write tests also require both hardware opt-in flags and restore the original trigger state
- Format7 and SDK configuration write tests require both hardware opt-in flags and restore prior camera state
- property write tests use strict generic property helpers and restore prior property state where possible
- embedded metadata write tests restore the original embedded metadata state where possible
- camera diagnostic reset tests require `FLYCAPTURE2_HARDWARE_WRITE_TEST=1` because they reset counters
- `FLYCAPTURE2_CAPTURE_TIMEOUT_MS` is currently a wall-clock threshold around `read_frame()`
- it is not an SDK-internal grab timeout configuration
- `Camera.set_grab_timeout(ms)` configures the SDK-level `RetrieveBuffer()` timeout
- frame and sequence saves use `.npy` and do not depend on image libraries
