# Headless Camera Readiness Validation — 6.9.1

This document records hardware evidence for camera-local FlyCapture2 SDK wrapper
behavior implemented by `flycapture2_c`.

This validation exercises headless FlyCapture2 camera-control primitives against
real hardware: lifecycle determinism, cleanup fidelity, trigger disable/restore,
frame ownership, property read/write, and pixel-format configuration.

This project remains a FlyCapture2 C SDK wrapper only. It does not implement GUI,
preview UI, sidecar processes, shared memory transport, ZMQ/IPC, optic_system
adapters, LCD/projector synchronization, experiment scheduling, acquisition
workflow orchestration, calibration, or reconstruction logic.

Issues discovered by downstream usage should be translated into general wrapper
requirements before being addressed here.

### Write gating

Readonly hardware validation may open, start, read, stop, and close the camera,
but does not persistently modify camera configuration.

Persistent configuration-changing operations (trigger enable/disable, Format7
configuration, property writes, pixel format changes) require both `--write`
and `FLYCAPTURE2_HARDWARE_WRITE_TEST=1`.

Readonly mode validates pixel formats via `validate_format7()` without applying
them. Trigger disable/enable/configuration is write-gated. Format7 / pixel-format
changes are write-gated. Property writes are write-gated.

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

## Headless Capture Flow

```text
Camera.open
disable_trigger
Camera.start
read_frame_with_info
Camera.stop
Camera.close
```

Result: **passed**.

## Trigger Behavior

The hardware initially booted in external trigger mode. `disable_trigger()`
(write-gated) successfully switched the camera into free-running capture.
Original trigger state was restored via `set_trigger_mode()` after testing.
No fallback to `source=0`/`mode=0` is performed if restore fails.

`TriggerModeInfo` capability fields (`supported_sources`, `supported_modes`)
are derived from SDK bitmasks (`source_mask`, `mode_mask`). Current trigger
state is read via `get_trigger_mode()` and restored via `set_trigger_mode()`.

Result: **passed** (write-gated).

## Pixel Format Configuration

Readonly mode validates pixel formats via `validate_format7()` without applying
them. Write mode configures, captures, and restores.

The following formats were validated and, in write mode, configured and decoded
successfully:

| Format  | Result |
|---------|--------|
| MONO8   | pass   |
| RAW8    | pass   |
| MONO16  | pass   |
| RAW16   | pass   |

Note: The camera is a color sensor. RAW formats return Bayer/raw data,
not RGB/BGR.

## Properties

The following properties were readable and writable on the tested camera:

| Property       | Abs Supported | Current Value                |
|----------------|---------------|------------------------------|
| SHUTTER        | yes           | 49.93 ms                     |
| GAIN           | yes           | 0.00 dB                      |
| FRAME_RATE     | yes           | 20.00 fps                    |
| AUTO_EXPOSURE  | yes           | 1.25 EV                      |
| BRIGHTNESS     | yes           | 10.01 %                      |
| GAMMA          | yes           | 1.25                         |
| WHITE_BALANCE  | no (value_a/b)| 668 / 831                    |
| TRIGGER_DELAY  | yes           | 0.00 ms                      |

WHITE_BALANCE uses `value_a` / `value_b` semantics, not `absValue`.

## ROI

ROI was not fully hardware-validated in this run. Format7 support exists,
but ROI remains optional/experimental until separately hardware-validated.

## Error Fidelity

`INVALID_GENERATION` was not observed in this validation run. Camera lifecycle
hardening ensures that cleanup-path stop failures cannot mask primary errors.
`cleanup_errors` are accessible after `close()` for inspection.

## Readiness Matrix

| Requirement                                      | API                    | Result | Conclusion                              |
|--------------------------------------------------|------------------------|--------|-----------------------------------------|
| headless open                                    | Camera.open            | pass   | fully supported and hardware-validated  |
| disable trigger                                  | disable_trigger        | pass   | fully supported and hardware-validated  |
| continuous capture                               | start/read/stop        | pass   | fully supported and hardware-validated  |
| frame layout                                     | ImageFrame             | pass   | fully supported and hardware-validated  |
| property snapshot                                | snapshot_properties    | pass   | fully supported and hardware-validated  |
| property read/write                              | property APIs          | pass   | fully supported and hardware-validated  |
| pixel format                                     | set_pixel_format/Format7 | pass | MONO8/RAW8/MONO16/RAW16 validated       |
| ROI                                              | set_roi/set_format7    | skip   | wrapper supports Format7, ROI not validated |
| cleanup fidelity                                 | close/cleanup_errors   | pass   | fully supported and hardware-validated  |

## Summary

The wrapper's lifecycle, trigger, property, and pixel-format behavior is
deterministic and documented. Headless operation (open, configure, capture,
close) was validated on the tested camera. ROI remains experimental until
separately hardware-validated.
