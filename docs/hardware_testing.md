# Hardware Testing

Hardware access is always opt-in.

Stage 6B GigE-specific hardware coverage is present. Broader raw SDK coverage
is the next expansion area.

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

Strobe and GPIO hardware tests:

```powershell
FLYCAPTURE2_HARDWARE_TEST=1 python -m pytest tests/hardware/test_hardware_strobe_gpio_readonly.py

FLYCAPTURE2_HARDWARE_TEST=1
FLYCAPTURE2_HARDWARE_WRITE_TEST=1
python -m pytest tests/hardware/test_hardware_strobe_gpio_write_reversible.py
```

Software trigger firing hardware tests:

```powershell
FLYCAPTURE2_HARDWARE_TEST=1 python -m pytest tests/hardware/test_hardware_software_trigger.py::test_hardware_software_trigger_readonly

FLYCAPTURE2_HARDWARE_TEST=1
FLYCAPTURE2_HARDWARE_WRITE_TEST=1
python -m pytest tests/hardware/test_hardware_software_trigger.py
```

The write-gated tests include an API smoke test and a fire-and-grab test. They
change trigger mode, fire the SDK software trigger, restore prior state, and do
not become an experiment workflow or external-device synchronization test.

GigE-specific hardware tests:

```powershell
FLYCAPTURE2_HARDWARE_TEST=1 python -m pytest tests/hardware/test_hardware_gige_readonly.py

FLYCAPTURE2_HARDWARE_TEST=1
FLYCAPTURE2_HARDWARE_WRITE_TEST=1
python -m pytest tests/hardware/test_hardware_gige_write_reversible.py
```

GigE tests skip cleanly when the connected camera is not GigE or the SDK/DLL
does not expose the requested GigE call. Write-gated tests use same-value smoke
checks for conservative settings. They do not actively change IP address,
subnet mask, gateway, packet size, packet delay, or stream channel settings.

Notes:

- default `pytest` skips all hardware tests
- property write tests require both hardware opt-in flags
- trigger write tests also require both hardware opt-in flags and restore the original trigger state
- software trigger fire-and-grab tests require both hardware opt-in flags and restore the original trigger/config state
- Format7 and SDK configuration write tests require both hardware opt-in flags and restore prior camera state
- property write tests use strict generic property helpers and restore prior property state where possible
- embedded metadata write tests restore the original embedded metadata state where possible
- camera diagnostic reset tests require `FLYCAPTURE2_HARDWARE_WRITE_TEST=1` because they reset counters
- strobe write tests require both hardware opt-in flags, restore the original strobe state, and currently perform a same-value write smoke test
- the current strobe write test does not actively toggle external strobe output and does not require an external loopback fixture
- GPIO write tests require both hardware opt-in flags and use conservative restore patterns
- GigE write tests require both hardware opt-in flags, restore original state where possible, and avoid risky network-changing writes
- `FLYCAPTURE2_CAPTURE_TIMEOUT_MS` is currently a wall-clock threshold around `read_frame()`
- it is not an SDK-internal grab timeout configuration
- `Camera.set_grab_timeout(ms)` configures the SDK-level `RetrieveBuffer()` timeout
- frame and sequence saves use `.npy` and do not depend on image libraries
