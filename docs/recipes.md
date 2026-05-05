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
