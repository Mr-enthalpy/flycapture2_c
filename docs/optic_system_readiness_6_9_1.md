# optic_system Readiness Validation — 6.9.1

## Scope

This validation checks whether `flycapture2_c` can replace the old `pyflycap2 + GUI`
dependency for the upstream `optic_system` camera sidecar.

This project remains a FlyCapture2 C API Python wrapper only. It does not implement
GUI, sidecar, shared memory, ZMQ, or experiment workflows.

## Hardware

- Camera: Grasshopper3 GS3-U3-51S5C
- Sensor: Sony IMX250, 2448×2048 color CMOS
- FlyCapture2 SDK: 2.13.3.61
- Platform: Windows 11
- Python: 3.12.0

## Lifecycle Validation

- `Camera.open()` connects only and does not start capture.
- `Camera.stop()` is a no-op when not capturing.
- `Camera.start()` enters capturing only after SDK success.
- `Camera.read_frame()` requires capturing state.
- `Camera.close()` is idempotent and best-effort.
- Cleanup-stage errors are collected in `cleanup_errors`.

Result: **passed**.

## optic_system Critical Flow

Validated flow:

```text
Camera.open
disable_trigger
Camera.start
read_frame_with_info
Camera.stop
Camera.close
```

Result: **passed**.

## Trigger

The hardware initially booted in external trigger mode. `disable_trigger()` successfully
switched the camera into free-running capture. Original trigger state was restored
after testing.

Result: **passed**.

## Pixel Formats

The following formats were configured and decoded successfully:

| Format  | Result |
|---------|--------|
| MONO8   | pass   |
| RAW8    | pass   |
| MONO16  | pass   |
| RAW16   | pass   |

Note: The camera is a color sensor. RAW formats return Bayer/raw data, not RGB/BGR.

## Properties

The following properties were readable and writable on the tested camera:

- SHUTTER
- GAIN
- FRAME_RATE
- AUTO_EXPOSURE
- BRIGHTNESS
- GAMMA
- WHITE_BALANCE
- TRIGGER_DELAY

WHITE_BALANCE uses `value_a` / `value_b` semantics, not `absValue`.

## ROI

ROI was not fully hardware-validated in this run. Format7 support exists, but ROI
should remain optional/experimental for upstream integration until explicitly tested.

## Error Fidelity

`INVALID_GENERATION` was not observed in this validation run. Lifecycle hardening
ensures that cleanup-path stop failures cannot mask primary errors.

## Readiness Matrix

| Requirement | Result | Conclusion |
|---|---|---|
| headless open | pass | fully supported and hardware-validated |
| disable trigger | pass | fully supported and hardware-validated |
| continuous capture | pass | fully supported and hardware-validated |
| frame layout | pass | fully supported and hardware-validated |
| property snapshot | pass | fully supported and hardware-validated |
| property read/write | pass | fully supported and hardware-validated |
| pixel format | pass | MONO8/RAW8/MONO16/RAW16 validated |
| ROI | skip | wrapper supports Format7, ROI not validated |
| cleanup fidelity | pass | fully supported and hardware-validated |

## Recommendation

`flycapture2_c` 6.9.1 is ready to be used as the hardware backend for the next
`optic_system` sidecar integration phase, with ROI kept out of the default path.
