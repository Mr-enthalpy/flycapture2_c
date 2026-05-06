# Hardware Testing

Hardware access is always opt-in, but readonly hardware validation should be
routine operational practice when the available camera is connected.

Stage 6.7 is release candidate hardening and reproducibility. Hardware
validation remains a repeatable release evidence check against the currently
available camera, not SDK feature expansion and not broad multi-model
qualification. Multi-camera and multi-model validation is deferred until
additional camera hardware is available.

The scripts in this document are developer validation tools only. They do not
provide experiment orchestration, scheduling, GUI preview, sidecar modes, IPC,
shared memory, ZMQ, `optic_system` integration, LCD/projector synchronization,
calibration, or reconstruction workflows.

Environment variables:

- `FLYCAPTURE2_HARDWARE_TEST=1`
- `FLYCAPTURE2_HARDWARE_WRITE_TEST=0|1`
- `FLYCAPTURE2_CAMERA_INDEX=0`
- `FLYCAPTURE2_FRAME_COUNT=30`
- `FLYCAPTURE2_CAPTURE_TIMEOUT_MS=...`

Default no-hardware validation:

```powershell
python -m pytest -q
python -c "import flycapture2_c; print('ok')"
python scripts/check_release.py
```

Readonly hardware validation:

```powershell
$env:FLYCAPTURE2_HARDWARE_TEST="1"
$env:FLYCAPTURE2_CAMERA_INDEX="0"
python scripts/hardware_capability_report.py --output outputs/capability_camera0.json
python scripts/run_hardware_validation.py
```

For release evidence, record the FlyCapture2 SDK version, camera model, serial
number, interface type, OS version, Python version, validation command, and
result summary. Capability report JSON should be written under `outputs/` and
must not be committed or included in release artifacts.

Run this readonly sequence routinely when the camera is connected. Unsupported
features should skip cleanly rather than failing qualification. For example,
GigE-specific tests skip when the available camera is USB or FireWire.

Write-gated validation is separate and deliberate:

```powershell
$env:FLYCAPTURE2_HARDWARE_TEST="1"
$env:FLYCAPTURE2_HARDWARE_WRITE_TEST="1"
$env:FLYCAPTURE2_CAMERA_INDEX="0"
python scripts/run_hardware_validation.py --include-write
```

Run write-gated validation only when it is acceptable to disturb camera state.
These tests are designed to restore prior state where possible, but they still
exercise real SDK write paths.

`scripts/hardware_capability_report.py` opens one camera, reads current
capabilities, records unsupported areas as JSON entries, and never writes
camera state. It prints JSON to stdout and also writes `--output` when supplied.

`scripts/run_hardware_validation.py` runs the existing pytest hardware files in
a deterministic order. It runs readonly groups by default and forces
`FLYCAPTURE2_HARDWARE_WRITE_TEST=0` for those groups even if the variable is set
in the parent shell. Write-gated groups run only with `--include-write` and
`FLYCAPTURE2_HARDWARE_WRITE_TEST=1`.

Legacy smoke examples remain useful for narrower checks:

```powershell
$env:FLYCAPTURE2_HARDWARE_TEST="1"
python scripts/hardware_smoke.py --level readonly --report-json outputs/readonly.json
python scripts/hardware_smoke.py --level grab-one --save-frame outputs/frame.npy --report-json outputs/grab_one.json
python scripts/hardware_smoke.py --level grab-sequence --report-json outputs/sequence.json
```

Trigger control hardware tests:

```powershell
$env:FLYCAPTURE2_HARDWARE_TEST="1"
python -m pytest tests/hardware/test_hardware_trigger_readonly.py

$env:FLYCAPTURE2_HARDWARE_TEST="1"
$env:FLYCAPTURE2_HARDWARE_WRITE_TEST="1"
python -m pytest tests/hardware/test_hardware_trigger_write_reversible.py
```

Format7 / ROI / SDK configuration hardware tests:

```powershell
$env:FLYCAPTURE2_HARDWARE_TEST="1"
python -m pytest tests/hardware/test_hardware_format7_readonly.py

$env:FLYCAPTURE2_HARDWARE_TEST="1"
$env:FLYCAPTURE2_HARDWARE_WRITE_TEST="1"
python -m pytest tests/hardware/test_hardware_format7_write_reversible.py

$env:FLYCAPTURE2_HARDWARE_TEST="1"
$env:FLYCAPTURE2_HARDWARE_WRITE_TEST="1"
python -m pytest tests/hardware/test_hardware_config_write_reversible.py
```

Property system hardware tests:

```powershell
$env:FLYCAPTURE2_HARDWARE_TEST="1"
python -m pytest tests/hardware/test_hardware_properties_readonly.py

$env:FLYCAPTURE2_HARDWARE_TEST="1"
$env:FLYCAPTURE2_HARDWARE_WRITE_TEST="1"
python -m pytest tests/hardware/test_hardware_properties_write_reversible.py
```

Embedded metadata and diagnostics hardware tests:

```powershell
$env:FLYCAPTURE2_HARDWARE_TEST="1"
python -m pytest tests/hardware/test_hardware_metadata_readonly.py

$env:FLYCAPTURE2_HARDWARE_TEST="1"
$env:FLYCAPTURE2_HARDWARE_WRITE_TEST="1"
python -m pytest tests/hardware/test_hardware_metadata_write_reversible.py
```

Strobe and GPIO hardware tests:

```powershell
$env:FLYCAPTURE2_HARDWARE_TEST="1"
python -m pytest tests/hardware/test_hardware_strobe_gpio_readonly.py

$env:FLYCAPTURE2_HARDWARE_TEST="1"
$env:FLYCAPTURE2_HARDWARE_WRITE_TEST="1"
python -m pytest tests/hardware/test_hardware_strobe_gpio_write_reversible.py
```

Software trigger firing hardware tests:

```powershell
$env:FLYCAPTURE2_HARDWARE_TEST="1"
python -m pytest tests/hardware/test_hardware_software_trigger.py::test_hardware_software_trigger_readonly

$env:FLYCAPTURE2_HARDWARE_TEST="1"
$env:FLYCAPTURE2_HARDWARE_WRITE_TEST="1"
python -m pytest tests/hardware/test_hardware_software_trigger.py
```

The write-gated tests include an API smoke test and a fire-and-grab test. They
change trigger mode, fire the SDK software trigger, restore prior state, and do
not become an experiment workflow or external-device synchronization test.

GigE-specific hardware tests:

```powershell
$env:FLYCAPTURE2_HARDWARE_TEST="1"
python -m pytest tests/hardware/test_hardware_gige_readonly.py

$env:FLYCAPTURE2_HARDWARE_TEST="1"
$env:FLYCAPTURE2_HARDWARE_WRITE_TEST="1"
python -m pytest tests/hardware/test_hardware_gige_write_reversible.py
```

GigE tests skip cleanly when the connected camera is not GigE or the SDK/DLL
does not expose the requested GigE call. Write-gated tests use same-value smoke
checks for conservative settings. They do not actively change IP address,
subnet mask, gateway, packet size, packet delay, or stream channel settings.

Notes:

- default `pytest` skips all hardware tests
- after `FLYCAPTURE2_HARDWARE_TEST=1`, readonly tests are intended to be safe by default
- readonly hardware validation should be routine for the currently available camera
- current validation evidence is limited to the available camera only
- multi-camera and multi-model validation is deferred
- unsupported camera capabilities skip cleanly rather than failing qualification
- property write tests require both hardware opt-in flags
- trigger write tests also require both hardware opt-in flags and restore the original trigger state
- software trigger fire-and-grab tests require both hardware opt-in flags and restore the original trigger/config state
- Format7 and SDK configuration write tests require both hardware opt-in flags and restore prior camera state
- property write tests use strict generic property helpers and restore prior property state where possible
- embedded metadata write tests restore the original embedded metadata state where possible
- camera diagnostic reset tests require `FLYCAPTURE2_HARDWARE_WRITE_TEST=1` because they reset counters
- strobe write tests require both hardware opt-in flags, restore the original strobe state, and currently perform a same-value write smoke test
- same-value write tests validate wrapper and SDK write/readback paths; they do not prove active external electrical behavior
- the current strobe/GPIO tests do not actively toggle external output and do not require external loopback wiring
- GPIO write tests require both hardware opt-in flags and use conservative restore patterns
- GigE write tests require both hardware opt-in flags, restore original state where possible, and avoid risky network-changing writes
- GigE tests do not assume the connected camera is GigE; non-GigE cameras skip GigE-specific checks
- GigE write tests avoid IP address, gateway, subnet mask, stream channel, packet size, and packet delay changes that could disconnect the camera
- `FLYCAPTURE2_CAPTURE_TIMEOUT_MS` is currently a wall-clock threshold around `read_frame()`
- it is not an SDK-internal grab timeout configuration
- `Camera.set_grab_timeout(ms)` configures the SDK-level `RetrieveBuffer()` timeout
- frame and sequence saves use `.npy` and do not depend on image libraries
