# API Coverage

This table tracks the FlyCapture2 C API surface wrapped by this project. It is not a full SDK coverage claim.

| Category | Function | Structs required | Raw binding status | High-level API status | No-hardware test status | Hardware readonly test status | Hardware write test status | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Context | `fc2CreateContext` | `fc2Context` | raw-bound | internal lifecycle | covered | covered through opt-in enumerate/open tests | not-applicable | Lazy loaded. |
| Context | `fc2DestroyContext` | `fc2Context` | raw-bound | internal lifecycle | covered | covered through opt-in enumerate/open tests | not-applicable | Cleanup path. |
| Bus | `fc2GetNumOfCameras` | `fc2Context` | raw-bound | `enumerate_cameras`, `Camera.open` | covered | covered | not-applicable | Hardware tests remain opt-in. |
| Bus | `fc2GetCameraFromIndex` | `fc2PGRGuid` | raw-bound | `enumerate_cameras`, `Camera.open` | covered | covered | not-applicable | GUID is copied into `CameraDescriptor`. |
| Camera | `fc2Connect` | `fc2PGRGuid` | raw-bound | `Camera.open` | covered with fake API | covered | not-applicable | No constructor-side hardware access. |
| Camera | `fc2Disconnect` | `fc2Context` | raw-bound | `Camera.close` | covered with fake API | covered | not-applicable | Idempotent high-level cleanup. |
| Camera | `fc2GetCameraInfo` | `fc2CameraInfo` | raw-bound | `Camera.get_camera_info` | covered | covered | not-applicable | Metadata only. |
| Camera | `fc2GetVideoModeAndFrameRate` | `fc2VideoMode`, `fc2FrameRate` | raw-bound | `Camera.get_video_mode_and_frame_rate` | covered | covered | not-applicable | Metadata only. |
| Capture | `fc2StartCapture` | `fc2Context` | raw-bound | `Camera.start` | covered with mock/fake API | covered | not-applicable | No default hardware access. |
| Capture | `fc2RetrieveBuffer` | `fc2Image` | raw-bound | `Camera.read_frame`, `Camera.read_frame_with_info` | covered with mock/image tests | covered | not-applicable | Public array is owned NumPy memory. |
| Capture | `fc2StopCapture` | `fc2Context` | raw-bound | `Camera.stop` | covered with mock/fake API | covered | not-applicable | Idempotent high-level cleanup. |
| Image | `fc2GetImageDimensions` | `fc2Image` | raw-bound | internal frame conversion | covered | covered through opt-in capture tests | not-applicable | Supports initial mono/raw formats. |
| Image | `fc2GetImageData` | `fc2Image` | raw-bound | internal frame copy | covered | covered through opt-in capture tests | not-applicable | Does not expose SDK pointer. |
| Properties | `fc2GetPropertyInfo` | `fc2PropertyInfo` | raw-bound | `Camera.get_property_info` | covered | covered | covered through opt-in reversible property test | High-level writes are intentionally curated. |
| Properties | `fc2GetProperty` | `fc2Property` | raw-bound | `Camera.get_property`, convenience getters | covered | covered | covered through opt-in reversible property test | Typed dataclass result. |
| Properties | `fc2SetProperty` | `fc2Property` | raw-bound | advanced `Camera.set_property`, curated convenience setters | covered | not-applicable | covered through opt-in reversible property test | Strict high-level policy by default. |
| Trigger | `fc2GetTriggerModeInfo` | `fc2TriggerModeInfo` | raw-bound | `Camera.get_trigger_mode_info` | covered | covered by opt-in trigger readonly test | not-applicable | Dedicated trigger API, no GUI. |
| Trigger | `fc2GetTriggerMode` | `fc2TriggerMode` | raw-bound | `Camera.get_trigger_mode` | covered | covered by opt-in trigger readonly test | covered by opt-in reversible trigger write test | Dedicated trigger API, no GUI. |
| Trigger | `fc2SetTriggerMode` | `fc2TriggerMode` | raw-bound | `Camera.set_trigger_mode`, `Camera.enable_trigger`, `Camera.disable_trigger` | covered with fake API | not-applicable | covered by opt-in reversible trigger write test | Writes save and restore old trigger state in hardware test. |
| Trigger | `fc2SetTriggerModeBroadcast` | `fc2TriggerMode` | raw-bound | explicit `broadcast=True` | covered with fake API | not-applicable | not-run-by-default | Bound because the C header exposes it and the signature is straightforward. |

Deferred in this milestone:

- Format7
- ROI
- GigE
- strobe / GPIO
- register access
- trigger delay
- software trigger firing
