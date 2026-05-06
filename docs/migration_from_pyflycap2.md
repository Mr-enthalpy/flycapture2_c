# Migration From pyflycap2 / PyCapture2

This project replaces GUI-dependent camera setup with direct FlyCapture2 C API calls through Python.

Current status: Stage 6A software trigger firing is implemented. GPIO scope is
limited to direct FlyCapture2 C API pin-direction helpers and embedded metadata
readback; register-level GPIO control is not wrapped.

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

## Replace GUI-Based Software Trigger Firing

Legacy workflows sometimes configured software trigger mode in a GUI and then
relied on GUI controls or C++ wrapper calls to fire. Use the SDK primitive
directly:

```python
from flycapture2_c import Camera
from flycapture2_c.trigger import SOFTWARE_TRIGGER_SOURCE

with Camera.open(0) as cam:
    info = cam.get_trigger_mode_info()
    if not info.software_trigger_supported:
        raise RuntimeError("This camera does not report software trigger support.")

    old = cam.get_trigger_mode()
    try:
        cam.enable_trigger(source=SOFTWARE_TRIGGER_SOURCE, mode=0)
        cam.start()
        cam.fire_software_trigger()
        frame = cam.read_frame_with_info()
    finally:
        cam.stop()
        cam.set_trigger_mode(old)
```

`Camera.fire_software_trigger()` is only the SDK firing call. It does not start
capture, retrieve frames, schedule repeated triggers, or synchronize external
devices.

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

## Replace GUI-Based Property Inspection and Configuration

```python
from flycapture2_c import Camera, PropertyType

with Camera.open(0) as cam:
    for item in cam.snapshot_properties():
        print(item)

    cam.set_property_abs(PropertyType.SHUTTER, 5.0, auto=False)
    cam.set_property_abs(PropertyType.GAIN, 0.0, auto=False)
```

Use convenience setters for common controls:

```python
from flycapture2_c import Camera

with Camera.open(0) as cam:
    cam.set_shutter(5.0, auto=False)
    cam.set_gain(0.0, auto=False)
    cam.set_brightness(1.0, auto=False)
    cam.set_gamma(1.0, auto=False)
    cam.set_white_balance(value_a=512, value_b=512, auto=False)
```

Property API layers:

- `get_property_raw()` / `set_property_raw()` are close to `fc2Property` and intended for advanced callers.
- `set_property_abs()`, `set_property_integer()`, `set_property_on_off()`, `set_property_auto()`, and `set_property_one_push()` validate camera support and ranges before writing.
- `set_shutter()`, `set_gain()`, `set_brightness()`, and similar methods are convenience wrappers over the safe generic API.
- Trigger source/mode/polarity use the dedicated trigger mode API.
- Trigger delay uses the property API as `PropertyType.TRIGGER_DELAY`.

## Replace GUI-Based Embedded Metadata Inspection

Legacy GUI workflows often showed embedded timestamp or frame-counter controls.
Use the SDK wrapper directly:

```python
from flycapture2_c import Camera

with Camera.open(0) as cam:
    info = cam.get_embedded_image_info()
    print(info)
```

For a reversible scripted change:

```python
from flycapture2_c import Camera

with Camera.open(0) as cam:
    old = cam.get_embedded_image_info()
    try:
        cam.set_embedded_image_info(timestamp=True, frame_counter=True)
        cam.start()
        frame = cam.read_frame_with_info()
        print(frame.metadata)
    finally:
        cam.stop()
        cam.set_embedded_image_info(old)
```

Embedded metadata support is camera-model-dependent. `Camera.set_embedded_image_info()`
will raise a typed error if a script explicitly requests an unavailable field.

## Replace GUI-Based Diagnostics Inspection

```python
from flycapture2_c import Camera

with Camera.open(0) as cam:
    stats = cam.get_camera_stats()
    print(stats)
```

`Camera.reset_camera_stats()` resets diagnostic counters. Treat it as a
write-like operation and reserve it for explicit diagnostic workflows.

## Replace GUI-Based Strobe Inspection and Configuration

Legacy GUI workflows often inspected strobe source support and wrote strobe
settings manually. Use the wrapper directly:

```python
from flycapture2_c import Camera

with Camera.open(0) as cam:
    info = cam.get_strobe_info(source=0)
    print(info)
```

For reversible scripted changes:

```python
from flycapture2_c import Camera

with Camera.open(0) as cam:
    old = cam.get_strobe(source=0)
    try:
        cam.set_strobe(source=0, on=True, polarity=1, delay=0.0, duration=1.0)
        print(cam.get_strobe(source=0))
    finally:
        cam.set_strobe(old)
```

Strobe support and safe values are camera-model-dependent and wiring-dependent.
`Camera.set_strobe()` validates the reported source capabilities before writing.

## Replace GUI-Based GPIO Direction Inspection

The FlyCapture2 C API exposes pin-direction helpers. This wrapper exposes those
directly and does not emulate additional GPIO behavior through register writes.

```python
from flycapture2_c import Camera

with Camera.open(0) as cam:
    direction = cam.get_gpio_pin_direction(pin=0)
    print("output" if direction else "input")
```

## Notes

- `Camera.enable_trigger()` and `Camera.disable_trigger()` use FlyCapture2's dedicated trigger mode API, not GUI APIs.
- `Camera.set_trigger_mode()` accepts and returns a `TriggerMode` dataclass so scripts can save and restore camera state.
- `Camera.set_format7()`, `Camera.set_roi()`, and `Camera.set_pixel_format()` use camera-side Format7 configuration, not Python-side crop logic.
- `Camera.snapshot_properties()` replaces GUI-based camera property inspection.
- `Camera.get_embedded_image_info()` and `Camera.read_frame_with_info().metadata` replace GUI-based embedded metadata inspection.
- `Camera.get_strobe_info()`, `Camera.get_strobe()`, and `Camera.set_strobe()` replace GUI-based strobe source inspection and configuration.
- Software trigger firing is implemented as an SDK-level camera operation, not an experiment scheduler.
- GigE-specific controls are the next focused stage. Callbacks, register access, and broader GPIO control are still deferred.
