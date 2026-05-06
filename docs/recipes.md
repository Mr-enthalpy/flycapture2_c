# Recipes

These examples use only the FlyCapture2 C API wrapper. They do not require any GUI path.

Status note: Stage 6B GigE-specific controls are implemented. Strobe, GPIO, and
GigE availability are camera-model-dependent and wiring-dependent.

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

FlyCapture2 commonly uses source `7` for software trigger mode, and this
wrapper exposes that value as `SOFTWARE_TRIGGER_SOURCE`. Confirm support with
`get_trigger_mode_info()` on the connected camera before writing.

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

## Fire a Software Trigger

This is a no-GUI SDK-level sequence. `fire_software_trigger()` only fires the
SDK software trigger; it does not configure trigger mode, start capture, retrieve
a frame, sleep, poll, or schedule repeated triggers.

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
        cam.start()
        cam.fire_software_trigger()
        frame = cam.read_frame_with_info()
    finally:
        cam.stop()
        cam.set_trigger_mode(old_trigger)
```

Timing policies, repeated trigger schedules, and external-device coordination
belong outside this project.

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

## Set Common Properties Without GUI

```python
from flycapture2_c import Camera, PropertyType

with Camera.open(0) as cam:
    cam.set_property_abs(PropertyType.SHUTTER, 5.0, auto=False)
    cam.set_property_abs(PropertyType.GAIN, 0.0, auto=False)
```

Convenience methods remain available:

```python
from flycapture2_c import Camera

with Camera.open(0) as cam:
    cam.set_shutter(5.0, auto=False)
    cam.set_gain(0.0, auto=False)
    cam.set_brightness(1.0, auto=False)
    cam.set_gamma(1.0, auto=False)
```

## Set White Balance

White balance uses the SDK integer `valueA` and `valueB` fields, not `absValue`.

```python
from flycapture2_c import Camera

with Camera.open(0) as cam:
    cam.set_white_balance(value_a=512, value_b=512, auto=False)
```

## Inspect Properties Without GUI

```python
from flycapture2_c import Camera

with Camera.open(0) as cam:
    for item in cam.snapshot_properties():
        print(item)
```

`snapshot_properties()` returns dataclasses containing the property type, property info, current value when readable, and any per-property error.

## Trigger Mode vs Trigger Delay

Use the dedicated trigger mode API for trigger source, mode, polarity, and enable/disable:

```python
cam.enable_trigger(source=0, mode=0)
cam.disable_trigger()
```

Use the property API for trigger delay:

```python
cam.set_trigger_delay(0.5, auto=False)
```

## Inspect Embedded Image Metadata Support

Embedded metadata support is camera-model-dependent. Availability and enabled
state are separate values.

```python
from flycapture2_c import Camera

with Camera.open(0) as cam:
    info = cam.get_embedded_image_info()
    print(info)
```

## Capture a Frame With Embedded Metadata

Save the original embedded metadata state before changing it, then restore it in
`finally`.

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

`frame.metadata` is an `ImageMetadata` dataclass copied from the SDK image
metadata structure. If a field is not enabled or unsupported by the camera, its
raw SDK metadata value may remain zero. If the SDK reports image metadata as not
supported, `frame.metadata` is `None`.

## Inspect Camera Diagnostic Stats

```python
from flycapture2_c import Camera

with Camera.open(0) as cam:
    stats = cam.get_camera_stats()
    print(stats)
```

`Camera.reset_camera_stats()` resets diagnostic counters and should be treated as
a write-like operation. Hardware tests for it require
`FLYCAPTURE2_HARDWARE_WRITE_TEST=1`.

## Inspect Strobe Source Support

```python
from flycapture2_c import Camera

with Camera.open(0) as cam:
    info = cam.get_strobe_info(source=0)
    print(info)
```

`source` is the FlyCapture2 strobe source/channel. Do not assume every camera
exposes every source.

## Reversible Strobe Configuration

Save the current strobe state before writing and restore it in `finally`.

```python
from flycapture2_c import Camera

with Camera.open(0) as cam:
    old = cam.get_strobe(source=0)
    try:
        cam.set_strobe(source=0, on=True, polarity=1, delay=0.0, duration=1.0)
        current = cam.get_strobe(source=0)
        print(current)
    finally:
        cam.set_strobe(old)
```

`Camera.set_strobe()` validates source support, on/off support, polarity
support, and delay/duration range before writing. It does not require frame
capture or embedded metadata.

## GPIO Pin Direction

This wrapper only exposes GPIO functions that are directly present in the
FlyCapture2 C API.

```python
from flycapture2_c import Camera

with Camera.open(0) as cam:
    direction = cam.get_gpio_pin_direction(pin=0)
    print("output" if direction else "input")
```

Changing GPIO direction is an explicit hardware write:

```python
from flycapture2_c import Camera

with Camera.open(0) as cam:
    old = cam.get_gpio_pin_direction(pin=0)
    try:
        cam.set_gpio_pin_direction(pin=0, direction="input")
    finally:
        cam.set_gpio_pin_direction(pin=0, direction=old)
```

## Optional Strobe/GPIO Metadata Observation

Embedded metadata can optionally be used to observe strobe and GPIO state after
configuration. It is not required for strobe control.

```python
from flycapture2_c import Camera

with Camera.open(0) as cam:
    old_metadata = cam.get_embedded_image_info()
    try:
        cam.set_embedded_image_info(strobe_pattern=True, gpio_pin_state=True)
        cam.start()
        frame = cam.read_frame_with_info()
        print(frame.metadata.strobe_pattern if frame.metadata else None)
        print(frame.metadata.gpio_pin_state if frame.metadata else None)
    finally:
        cam.stop()
        cam.set_embedded_image_info(old_metadata)
```

## Inspect GigE Configuration

GigE support is camera-model-dependent. These methods are SDK-level camera-local
operations; they do not provide a network service or packet streaming transport.

```python
from flycapture2_c import Camera

with Camera.open(0) as cam:
    info = cam.get_camera_info()
    print(info.interface_type)

    config = cam.get_gige_config()
    print(config)

    settings = cam.get_gige_image_settings()
    print(settings)
```

GigE writes are explicit. Avoid changing packet size, packet delay, IP address,
subnet mask, gateway, or stream channel values unless you have a camera-specific
recovery plan.
