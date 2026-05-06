# SDK Layout

Default local SDK container:

- `third_party/`

Expected SDK root:

- `third_party/FlyCapture2/`

Required headers:

- `include/C/FlyCapture2_C.h`
- `include/C/FlyCapture2Defs_C.h`
- `include/C/FlyCapture2Platform_C.h`

Primary local library directory:

- `lib64/C/`

DLL search order:

1. `FLYCAPTURE2_DLL_DIR` if set
2. `<sdk-root>/bin64/vs2015`
3. `<sdk-root>/bin64`
4. `<sdk-root>/bin64/vs2013`

SDK root resolution:

1. `FLYCAPTURE2_SDK_DIR` if set
2. project-local `third_party/`
3. if the configured path is a parent container rather than the SDK root, the loader also checks `<path>/FlyCapture2`

Notes:

- importing `flycapture2_c` does not load any DLL
- DLL loading happens only on first SDK call
- the project does not copy SDK DLLs into `src/`
- `third_party/` is treated as a local SDK lookup location only
- `third_party/` must not be included in wheels, source distributions, or other
  release artifacts for the Python wrapper
- the MIT License applies to this Python wrapper, not to FlyCapture2 SDK files,
  runtime DLLs, drivers, vendor headers, vendor libraries, or sample binaries
