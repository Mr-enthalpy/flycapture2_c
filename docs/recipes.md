# Recipes

These examples use only the FlyCapture2 C API wrapper. They do not require any GUI path.

## Configure External Hardware Trigger

Trigger source `0` is the common GPIO external trigger source used by FlyCapture2 examples. Polarity is camera and wiring dependent; pass it explicitly when needed.

```python
from flycapture2_c import Camera

with Camera.open(index=0) as cam:
    info = cam.get_trigger_mode_info()
    if not info.present:
        raise RuntimeError("This camera does not report trigger mode support.")

    old_trigger = cam.get_trigger_mode()
    try:
        cam.enable_trigger(source=0, mode=0, parameter=0, polarity=1)
        cam.start()
        frame = cam.read_frame()
    finally:
        cam.stop()
        cam.set_trigger_mode(old_trigger)
```

## Configure Software Trigger Mode

FlyCapture2 conventionally uses source `7` for software trigger mode. This wrapper currently configures the trigger mode; firing a software trigger is a separate SDK call and is not part of this milestone.

```python
from flycapture2_c import Camera
from flycapture2_c.trigger import SOFTWARE_TRIGGER_SOURCE

with Camera.open(index=0) as cam:
    info = cam.get_trigger_mode_info()
    if not info.software_trigger_supported:
        raise RuntimeError("This camera does not report software trigger support.")

    old_trigger = cam.get_trigger_mode()
    try:
        cam.enable_trigger(source=SOFTWARE_TRIGGER_SOURCE, mode=0, parameter=0)
        current = cam.get_trigger_mode()
        assert current.on_off
        assert current.source == SOFTWARE_TRIGGER_SOURCE
    finally:
        cam.set_trigger_mode(old_trigger)
```

## Disable Trigger Mode

```python
from flycapture2_c import Camera

with Camera.open(index=0) as cam:
    cam.disable_trigger()
```

## Reversible Trigger Configuration Pattern

Automated scripts should save the original trigger state before writing, then restore it in `finally`.

```python
from flycapture2_c import Camera

with Camera.open(index=0) as cam:
    old_trigger = cam.get_trigger_mode()
    try:
        cam.enable_trigger(source=0, mode=0)
        # Run the acquisition that expects trigger mode here.
    finally:
        cam.set_trigger_mode(old_trigger)
```

## Configure Pixel Format and ROI

This configures camera-side Format7 ROI. It is not a Python-side crop.

```python
from flycapture2_c import Camera

with Camera.open(0) as cam:
    cam.set_pixel_format("MONO8")
    cam.set_roi(offset_x=0, offset_y=0, width=1024, height=768)
    cam.start()
    frame = cam.read_frame()
```

`read_frame()` currently decodes copied NumPy arrays for `MONO8`, `MONO16`, `RAW8`, and `RAW16`. Other SDK pixel formats may be configurable, but frame retrieval will raise `UnsupportedPixelFormatError` until an explicit decode or raw-frame path is implemented.

## Validate Format7 Before Writing

```python
from flycapture2_c import Camera

with Camera.open(0) as cam:
    validation = cam.validate_format7(
        mode=0,
        offset_x=0,
        offset_y=0,
        width=1024,
        height=768,
        pixel_format="MONO8",
    )
    if not validation.settings_are_valid:
        raise RuntimeError("Format7 settings were rejected by the camera.")
```

## Set SDK-Level Grab Timeout

This sets FlyCapture2's SDK-level `RetrieveBuffer()` timeout. It is separate from the Python-side `FLYCAPTURE2_CAPTURE_TIMEOUT_MS` smoke-test wall-clock guard.

```python
from flycapture2_c import Camera

with Camera.open(0) as cam:
    cam.set_grab_timeout(1000)
```

## Reversible Format7 Configuration Pattern

```python
from flycapture2_c import Camera

with Camera.open(0) as cam:
    old_format7 = cam.get_format7_configuration()
    try:
        cam.set_format7(
            mode=old_format7.settings.mode,
            offset_x=0,
            offset_y=0,
            width=1024,
            height=768,
            pixel_format="MONO8",
        )
        cam.start()
        frame = cam.read_frame()
    finally:
        cam.stop()
        cam.set_format7(
            mode=old_format7.settings.mode,
            offset_x=old_format7.settings.offset_x,
            offset_y=old_format7.settings.offset_y,
            width=old_format7.settings.width,
            height=old_format7.settings.height,
            pixel_format=old_format7.settings.pixel_format,
            packet_size=old_format7.packet_size,
        )
```
