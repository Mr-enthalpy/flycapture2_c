# Buffer Lifetime

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
