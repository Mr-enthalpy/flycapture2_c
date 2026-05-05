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

## Notes

- `Camera.enable_trigger()` and `Camera.disable_trigger()` use FlyCapture2's dedicated trigger mode API, not GUI APIs.
- `Camera.set_trigger_mode()` accepts and returns a `TriggerMode` dataclass so scripts can save and restore camera state.
- Software trigger firing is not implemented in this milestone; only trigger mode configuration is covered.
- Format7, ROI, GigE, strobe, and register access are still deferred.
