# Migration From pyflycap2 / PyCapture2

This project replaces GUI-dependent camera setup with direct FlyCapture2 C API calls through Python.

## Replace GUI-Based Trigger Configuration

Legacy code often depended on a GUI object to put the camera into trigger mode:

```python
from pyflycap2.interface import Camera, GUI

cam = Camera()
gui = GUI(cam)
gui.show()
# Trigger source, trigger mode, polarity, and parameter were configured by hand.
```

Use `flycapture2_c.Camera` trigger methods instead:

```python
from flycapture2_c import Camera

with Camera.open(index=0) as cam:
    previous = cam.get_trigger_mode()
    try:
        cam.enable_trigger(source=0, mode=0, parameter=0, polarity=1)
        cam.start()
        frame = cam.read_frame()
    finally:
        cam.stop()
        cam.set_trigger_mode(previous)
```

## Read Trigger Capabilities Before Writing

```python
from flycapture2_c import Camera

with Camera.open(index=0) as cam:
    info = cam.get_trigger_mode_info()
    print(info.present)
    print(info.supported_sources)
    print(info.supported_modes)
    print(info.software_trigger_supported)
```

## Replace GUI-Based Pixel Format and ROI Configuration

Legacy GUI workflows often configured Format7 mode, pixel format, and ROI manually. Use the wrapper directly:

```python
from flycapture2_c import Camera

with Camera.open(0) as cam:
    cam.set_pixel_format("MONO8")
    cam.set_roi(offset_x=0, offset_y=0, width=1024, height=768)
    cam.start()
    frame = cam.read_frame()
```

For scripts that must restore the previous camera state:

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
    finally:
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

## Replace GUI-Based Grab Timeout Configuration

```python
from flycapture2_c import Camera

with Camera.open(0) as cam:
    cam.set_grab_timeout(1000)
```

This is the SDK-level `RetrieveBuffer()` timeout. It is separate from smoke-test timing guards such as `FLYCAPTURE2_CAPTURE_TIMEOUT_MS`.

## Notes

- `Camera.enable_trigger()` and `Camera.disable_trigger()` use FlyCapture2's dedicated trigger mode API, not GUI APIs.
- `Camera.set_trigger_mode()` accepts and returns a `TriggerMode` dataclass so scripts can save and restore camera state.
- `Camera.set_format7()`, `Camera.set_roi()`, and `Camera.set_pixel_format()` use camera-side Format7 configuration, not Python-side crop logic.
- Software trigger firing is not implemented yet; only trigger mode configuration is covered.
- GigE, strobe, GPIO, callbacks, and register access are still deferred.
