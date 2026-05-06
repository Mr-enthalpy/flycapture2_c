# Release Checklist

This checklist is for the `0.6.0` Stage 6.7 release candidate. Stage 6.7 is
release candidate hardening and reproducibility only; it is not full
FlyCapture2 SDK coverage, broad camera-model qualification, a GUI workflow, or
an experiment framework.

## Clean Checkout

Start from a clean checkout of the release branch:

```powershell
git status --short --branch
git fetch origin
git rev-parse HEAD
```

The working tree should be clean before building release artifacts.

## Clean Venv

Create a fresh virtual environment and install the package with development
tools:

```powershell
py -3.8 -m venv .venv-release
.\.venv-release\Scripts\python.exe -m pip install --upgrade pip
.\.venv-release\Scripts\python.exe -m pip install -e ".[dev]"
```

The core runtime dependency boundary remains Python, `ctypes`, and NumPy.
`pytest`, `build`, and `pyyaml` are development or validation dependencies only.

## License Boundary

The Python wrapper source code, tests, examples, documentation, and package
artifacts are released under the MIT License. The MIT License does not apply to
the FlyCapture2 SDK, FlyCapture2 runtime DLLs, vendor drivers, vendor headers,
vendor libraries, vendor sample binaries, or files under `third_party/`.

Release artifacts for this repository must contain only the Python wrapper and
project metadata. Users install the vendor SDK separately.

## Default No-Hardware Tests

Default tests must not require the FlyCapture2 SDK, a vendor DLL, or camera
hardware:

```powershell
.\.venv-release\Scripts\python.exe -m pytest -q
```

Hardware tests must remain skipped unless explicitly enabled.

## Import Smoke

Import must remain lightweight:

```powershell
.\.venv-release\Scripts\python.exe -c "import flycapture2_c; print(flycapture2_c.__version__)"
```

Expected output for this release candidate is `0.6.0`.

## SDK-Free Import Guarantee

Run the import tests with invalid SDK paths:

```powershell
$env:FLYCAPTURE2_SDK_DIR="$PWD\does_not_exist"
$env:FLYCAPTURE2_DLL_DIR="$PWD\does_not_exist"
.\.venv-release\Scripts\python.exe -m pytest tests\test_import_no_sdk.py tests\test_public_api_docs.py -q
Remove-Item Env:\FLYCAPTURE2_SDK_DIR
Remove-Item Env:\FLYCAPTURE2_DLL_DIR
```

The package import path must not load the vendor DLL, enumerate cameras, open
hardware, or require SDK installation.

## Wheel Build

Build the wheel from the clean checkout:

```powershell
.\.venv-release\Scripts\python.exe -m build --wheel
```

For a one-command local release gate, run:

```powershell
.\.venv-release\Scripts\python.exe scripts\check_release.py
```

The script runs default tests, import smoke, an isolated wheel build, and a
wheel/sdist content audit, then installs both artifacts into clean virtual
environments and imports the package from each install.

## Local No-Hardware Matrix

When multiple Python versions are installed locally, run the CI-equivalent
matrix script:

```powershell
py -3.13 scripts\check_ci_matrix.py
```

The script probes Python 3.8 through 3.13 with the Windows `py` launcher where
available, creates a clean venv per interpreter, installs `.[dev]`, runs
default pytest, and verifies import smoke with invalid SDK/DLL paths. Missing
local interpreters are reported rather than treated as release failures; GitHub
Actions is the authoritative full Windows matrix.

## Artifact Content Audit

Audit built artifacts before publishing or sharing. Wheels and source
distributions must not contain:

- `third_party/`
- `outputs/`
- FlyCapture2 vendor DLLs
- vendor `.lib` files
- vendor SDK headers
- vendor drivers
- vendor sample binaries or projects
- generated capability reports or smoke-test outputs

Only package code from `src/flycapture2_c` and distribution metadata should be
inside wheels. Source distributions may include tracked Python wrapper source,
tests, examples, scripts, docs, and project metadata, but not vendor SDK files.

## Readonly Hardware Validation

Readonly hardware validation is recommended when the available camera is
connected, but it is not part of the default no-hardware gate:

```powershell
$env:FLYCAPTURE2_HARDWARE_TEST="1"
$env:FLYCAPTURE2_CAMERA_INDEX="0"
.\.venv-release\Scripts\python.exe scripts\hardware_capability_report.py --output outputs\capability_camera0.json
.\.venv-release\Scripts\python.exe scripts\run_hardware_validation.py
```

Current hardware evidence is limited to the available camera. Multi-camera and
multi-model validation is deferred.

## Optional Write-Gated Hardware Validation

Write-gated validation is deliberate and may disturb camera state, even though
tests are designed to save and restore previous settings:

```powershell
$env:FLYCAPTURE2_HARDWARE_TEST="1"
$env:FLYCAPTURE2_HARDWARE_WRITE_TEST="1"
$env:FLYCAPTURE2_CAMERA_INDEX="0"
.\.venv-release\Scripts\python.exe scripts\run_hardware_validation.py --include-write
```

Do not run write-gated tests unless both opt-in flags are set and camera state
changes are acceptable.

## Capability Report Output Rules

Capability reports must be written under `outputs/` or another ignored local
directory. They may be attached to internal validation notes, but generated JSON
reports are not release source files and must not be included in wheels or
source distributions.

Summarize release-candidate evidence in `docs/release_evidence.md`; keep raw
generated reports under ignored local output directories.

## Release Boundary

The `0.6.0` release candidate is a FlyCapture2 C SDK wrapper release. It does
not include GUI, preview UI, sidecar/server modes, IPC/shared memory, ZMQ,
`optic_system` backend code, experiment scheduling, LCD/projector sync,
calibration, reconstruction, or acquisition workflow orchestration.
