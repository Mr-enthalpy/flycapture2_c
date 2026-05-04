# Buffer Lifetime

`Camera.read_frame()` and `Camera.read_frame_with_info()` never return a view into the FlyCapture2 SDK buffer.

Behavior:

- `fc2RetrieveBuffer()` fills an SDK-managed `fc2Image`
- the wrapper reads metadata from that `fc2Image`
- pixel bytes are copied into a new `numpy.ndarray`
- the returned array has `OWNDATA=True`

This is an explicit project guarantee. Callers must not depend on SDK buffer lifetime, pointer stability, or reuse across frames.

Supported first-phase pixel formats:

- `MONO8`
- `MONO16`
- `RAW8`
- `RAW16`

For `RAW8` and `RAW16`, the wrapper returns the raw sensor plane as a 2D array. It does not debayer or color-convert.
