# Pixel Format Support

Pixel format support has separate layers. A format can be known to the SDK
wrapper, accepted by a camera configuration path, and still not be decoded by
`read_frame()`.

## Support Layers

- SDK enum known: the enum value exists in `flycapture2_c.pixel_format.PixelFormat`.
- Camera-configurable: the connected camera reports the format through Format7
  or GigE pixel-format bitfields, and the wrapper can request it through the
  existing camera-local configuration APIs.
- `read_frame()` decodable: `read_frame()` or `read_frame_with_info()` converts
  the SDK image buffer into a structured owned NumPy array.
- Raw-copy-only: the SDK may produce bytes for the format, but the high-level
  structured decoder does not interpret the layout yet.
- Unsupported / compressed: the wrapper should not reinterpret the buffer
  silently. Compressed formats require an explicit decompression implementation,
  which is outside the current scope.

Configuration support and decode support are intentionally separate. For
example, a camera may report a Format7 pixel format bit as configurable even
when `read_frame()` still raises `UnsupportedPixelFormatError` for that format.

## Current Decode Matrix

The machine-readable matrix lives in
`flycapture2_c.pixel_format.PIXEL_FORMAT_SUPPORT`. Every `PixelFormat` member,
including aliases such as `RGB`, is classified.

Current `read_frame()` decoded formats:

| Pixel format | NumPy shape | dtype | Notes |
| --- | --- | --- | --- |
| `MONO8` | `(height, width)` | `uint8` | 8-bit mono |
| `MONO16` | `(height, width)` | `uint16` | 16-bit mono |
| `RAW8` | `(height, width)` | `uint8` | 8-bit raw sensor bytes |
| `RAW16` | `(height, width)` | `uint16` | 16-bit raw sensor words |
| `RGB8` / `RGB` | `(height, width, 3)` | `uint8` | 24-bit interleaved RGB |

Known but not decoded formats are classified as either raw-copy-only or
unsupported/compressed in the matrix. Examples include YUV formats, 12-bit
packed-like formats, 16-bit interleaved color formats, BGR/BGRU variants, and
the JPEG-compressed stream format.

## RGB Decode Scope

`RGB8` is confirmed in the FlyCapture2 C headers as 24-bit RGB. The wrapper
copies it into an owned NumPy array with shape `(height, width, 3)` and dtype
`uint8`, respecting SDK-reported row stride and dropping row padding.

This is not a color-management pipeline. The wrapper does not implement Bayer
demosaic, YUV conversion, BGR conversion, compressed image decoding, white
balance correction, gamma correction, or color-space conversion.

## Failure Policy

Unsupported formats continue to raise `UnsupportedPixelFormatError`. Error
messages include the SDK pixel-format value and, when known, the enum name and
whether the format is known but not decodable.

Unknown SDK integer values are also rejected. The wrapper must not silently
reinterpret unknown buffers as mono or RGB data.

## Capability Reports

`scripts/hardware_capability_report.py` interprets Format7 and GigE
pixel-format bitfields when they are available. FlyCapture2 pixel-format
constants include overlapping composite values, such as `BGR = 0x80000008`
and `RGBU = 0x40000002`. A naive bitwise subset check would over-report
formats such as `MONO8` or `YUV411` when only the composite value is present.

Capability-report interpretation is therefore conservative. More-specific
composite/modifier values are matched first, and overlapping one-hot base
formats are suppressed when the integer bitfield cannot distinguish a true
base-format flag from the composite value. This can under-report an ambiguous
base+composite combination, but it avoids silently overstating camera support.

The report separates:

- `supported_by_camera`
- `read_frame_decodable`
- `raw_copy_only`
- `unsupported_or_compressed`

These summaries describe the connected camera's reported configuration support
against the wrapper's decode matrix. They are not a claim that all known SDK
formats are supported by every camera.
