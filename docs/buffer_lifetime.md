# Buffer Lifetime

## Camera lifecycle

`Camera` maintains an explicit state machine:

```
closed → opened → capturing → opened → closed
```

- `Camera.open()` connects to the camera hardware. Capture is **not** started.
- `Camera.start()` enters the capturing state only after `fc2StartCapture` succeeds.
- `Camera.read_frame()` requires the capturing state; it raises `CameraStateError` otherwise.
- `Camera.stop()` is **idempotent**: a no-op when the camera is not capturing, not connected, or has no context. Explicit `stop()` propagates real SDK errors (except known already-stopped conditions).
- `Camera.close()` is **best-effort cleanup**: each step (stop, disconnect, destroy-image, destroy-context) runs independently. A failure in one step never prevents later steps from executing. Cleanup-stage errors are collected in `camera.cleanup_errors`. `close()` may be called multiple times safely.
- Inside a `with Camera.open() as cam:` context manager, cleanup errors from `close()` never replace the active exception from the `with` block.

User documents:
```python
from flycapture2_c import Camera

with Camera.open(index=0) as cam:
    cam.start()                # enter capturing state
    frame = cam.read_frame()   # requires capturing
    cam.stop()                 # exit capturing state (also safe if redundant)
# close() runs automatically
```

---

`Camera.read_frame()` and `Camera.read_frame_with_info()` never return a view into the FlyCapture2 SDK buffer.

Behavior:

- `fc2RetrieveBuffer()` fills an SDK-managed `fc2Image`
- the wrapper reads metadata from that `fc2Image`
- pixel bytes are copied into a new `numpy.ndarray`
- the returned array has `OWNDATA=True`

This is an explicit project guarantee. Callers must not depend on SDK buffer lifetime, pointer stability, or reuse across frames.

The ordinary high-level API does not expose a zero-copy SDK-buffer view. Any
future lower-level buffer view would need an explicit advanced lifetime
contract and tests documenting invalidation behavior.

Supported first-phase pixel formats:

- `MONO8`
- `MONO16`
- `RAW8`
- `RAW16`

For `RAW8` and `RAW16`, the wrapper returns the raw sensor plane as a 2D array. It does not debayer or color-convert.

This document covers only FlyCapture2 C SDK wrapper behavior. It does not
define shared memory, ZMQ/IPC, sidecar transport, GUI preview, acquisition
workflow orchestration, calibration, or reconstruction behavior.
