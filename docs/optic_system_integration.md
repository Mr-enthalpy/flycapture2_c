# optic_system Integration Boundary

`flycapture2_c` does not implement an `optic_system` backend, sidecar process, IPC layer, GUI, or experiment workflow.

This repository only provides:

- a Python wrapper around the FlyCapture2 C SDK
- stable public APIs for camera enumeration, lifecycle, capture, trigger mode,
  software trigger firing, Format7/ROI/pixel format, SDK capture configuration,
  properties, embedded metadata, diagnostics, strobe/GPIO, and GigE
  camera-local SDK primitives

`optic_system` integration belongs in the `optic_system` repository.

Small camera-local usage example for downstream integration:

```python
from flycapture2_c import Camera

with Camera.open(index=0) as camera:
    camera.disable_trigger()
    camera.start()
    frame = camera.read_frame()
    camera.stop()
```

## Legacy `camera_service_impl.py` Surface

The legacy `optic_system/devices/camera_service_impl.py` implementation used
`pyflycap2.interface.Camera` plus `GUI`. The GUI requirement was a workaround
for missing scriptable camera controls, not a requirement for preview.

The minimal camera-local surface needed by that service maps to
`flycapture2_c` as follows:

| Legacy need | `flycapture2_c` replacement |
| --- | --- |
| Open camera by index | `Camera.open(index=0)` |
| Disable trigger before continuous capture | `cam.disable_trigger()` |
| Start continuous capture | `cam.start()` |
| Read frames repeatedly | repeated `cam.read_frame()` or `cam.read_frame_with_info()` |
| Get width / height / stride / pixel format | `ImageFrame.width`, `height`, `stride`, `pixel_format` from `read_frame_with_info()` |
| Get serial number | `cam.get_camera_info().serial_number` |
| Enumerate adjustable property names | `cam.list_property_infos()` or `cam.snapshot_properties()` |
| Get property range/capabilities | `cam.get_property_info(PropertyType....)` |
| Get property value | `cam.get_property(PropertyType....)` |
| Set property value | `cam.set_property_abs(...)`, convenience setters, or `cam.set_white_balance(...)` |
| Configure pixel format / Format7 / ROI | `cam.set_pixel_format(...)`, `cam.set_format7(...)`, `cam.set_roi(...)` |
| Cleanup | context manager, `cam.stop()`, `cam.close()` |

`PreConfigGUI` should be replaced by explicit configuration calls. It should
not be preserved as a requirement in the new headless service.

## Hardware Validation On Available Camera

Validation date: 2026-05-06.

Camera:

- model: Grasshopper3 GS3-U3-51S5C
- serial: `15471217`
- interface type: USB (`interface_type=1`)
- current Format7 configuration: `2448x2048`, `RAW8`, packet size `6280`

Commands run:

```powershell
python -m pytest -q
python -c "import flycapture2_c; print('ok')"

$env:FLYCAPTURE2_HARDWARE_TEST="1"
$env:FLYCAPTURE2_CAMERA_INDEX="0"
python scripts/hardware_capability_report.py --output outputs/optic_system_capability_camera0.json
python scripts/run_hardware_validation.py

$env:FLYCAPTURE2_HARDWARE_TEST="1"
$env:FLYCAPTURE2_HARDWARE_WRITE_TEST="1"
$env:FLYCAPTURE2_CAMERA_INDEX="0"
python scripts/run_hardware_validation.py --include-write
```

Results:

- default no-hardware tests passed: `144 passed, 28 skipped`
- lazy import passed: `ok`
- readonly capability report wrote `outputs/optic_system_capability_camera0.json`
- readonly hardware validation passed all groups, with clean skips for
  unsupported strobe/software-trigger cases and non-GigE checks
- write-gated validation passed all groups after tightening property restore
  semantics for unsupported control flags

An additional targeted smoke matching the old service path saved the original
trigger state, called `disable_trigger()`, read 10 frames continuously, then
restored trigger state. It confirmed:

- `trigger_after_disable_on_off=False`
- `frame_count=10`
- stable frame shape, dtype, and pixel format across the sequence
- frame shape and metadata: `2448x2048`, `stride=2448`, `RAW8`, `uint8`
- returned arrays own their memory
- serial readback: `15471217`

The same targeted smoke confirmed that the connected camera reports present,
readable property capabilities for:

- `FRAME_RATE`: abs range `1.0` to `10.012516021728516`, auto/manual supported
- `AUTO_EXPOSURE`: abs range `-7.5849609375` to `2.41363525390625`, auto/manual supported
- `SHUTTER`: abs range `0.04756450653076172` to `31977.01953125`, auto/manual supported
- `GAIN`: abs range `0.0` to `47.994266510009766`, auto/manual supported
- `BRIGHTNESS`: abs range `0.0` to `12.4755859375`, manual supported
- `GAMMA`: abs range `0.5` to `3.9990234375`, manual supported
- `WHITE_BALANCE`: integer `value_a` / `value_b`, auto/manual supported, no abs-value support

## Conclusion For `optic_system`

On the currently connected Grasshopper3 camera, `flycapture2_c` is sufficient
to replace the legacy `pyflycap2 + GUI` camera-control dependency for a
headless continuous acquisition service, provided the service keeps its own
ZMQ/shared-memory transport outside this repository.

The FlyCapture2 wrapper covers the GUI replacement points that caused the old
dependency:

- trigger state can be read and disabled programmatically before capture
- continuous frame retrieval works without GUI
- width, height, stride, pixel format, and serial number are available without GUI
- Format7, ROI, and pixel format are configurable without GUI
- relevant property capabilities, ranges, current values, and writes are
  available without GUI

This is a hardware-backed conclusion for the available camera only. It is not a
claim of broad camera-model compatibility or full FlyCapture2 SDK coverage.
