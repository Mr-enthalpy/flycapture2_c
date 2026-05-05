# optic_system Integration Boundary

`flycapture2_c` does not implement an `optic_system` backend, sidecar process, IPC layer, GUI, or experiment workflow.

This repository only provides:

- a Python wrapper around the FlyCapture2 C API
- stable public APIs for camera enumeration, lifecycle, capture, trigger mode, Format7/ROI/pixel format, SDK capture configuration, and camera properties

`optic_system` integration belongs in the `optic_system` repository.

Minimal usage example for downstream integration:

```python
from flycapture2_c import Camera

with Camera.open(index=0) as camera:
    camera.start()
    frame = camera.read_frame()
    camera.stop()
```
