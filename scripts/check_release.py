from __future__ import annotations

import subprocess
import sys
import tempfile
import shutil
import tarfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

FORBIDDEN_PREFIXES = (
    "third_party/",
    "outputs/",
    "include/",
    "bin/",
    "lib/",
)
FORBIDDEN_SUFFIXES = (
    ".dll",
    ".lib",
    ".exe",
    ".msi",
    ".pdb",
    ".sys",
    ".so",
    ".dylib",
)
FORBIDDEN_HEADER_PREFIXES = (
    "flycapture2",
    "fc2",
)
FORBIDDEN_VENDOR_MARKERS = (
    "flycapture2/src/",
    "flycapture2/include/",
    "flycapture2/bin/",
    "flycapture2/lib/",
)
GENERATED_PATHS = (
    ROOT / "build",
    ROOT / "src" / "flycapture2_c.egg-info",
)


def run(args: list[str], *, cwd: Path = ROOT) -> None:
    print("+ " + " ".join(args), flush=True)
    subprocess.run(args, cwd=cwd, check=True)


def remove_generated_artifacts() -> None:
    root = ROOT.resolve()
    for path in GENERATED_PATHS:
        if not path.exists():
            continue
        resolved = path.resolve()
        if root not in (resolved, *resolved.parents):
            raise RuntimeError(f"refusing to remove path outside repository: {resolved}")
        if resolved.is_dir():
            shutil.rmtree(resolved)
        else:
            resolved.unlink()


def build_distributions() -> list[Path]:
    with tempfile.TemporaryDirectory(prefix="flycapture2_c_release_") as tmp:
        out_dir = Path(tmp)
        run([sys.executable, "-m", "build", "--outdir", str(out_dir)])
        wheels = sorted(out_dir.glob("*.whl"))
        sdists = sorted(out_dir.glob("*.tar.gz"))
        if len(wheels) != 1:
            raise RuntimeError(f"expected exactly one wheel, found {len(wheels)}")
        if len(sdists) != 1:
            raise RuntimeError(f"expected exactly one sdist, found {len(sdists)}")
        wheel = ROOT / wheels[0].name
        sdist = ROOT / sdists[0].name
        wheel.write_bytes(wheels[0].read_bytes())
        sdist.write_bytes(sdists[0].read_bytes())
    remove_generated_artifacts()
    return [wheel, sdist]


def archive_names(artifact: Path) -> list[str]:
    if artifact.suffix == ".whl":
        with zipfile.ZipFile(artifact) as archive:
            return archive.namelist()
    if artifact.name.endswith(".tar.gz"):
        with tarfile.open(artifact, "r:gz") as archive:
            return archive.getnames()
    raise RuntimeError(f"unsupported artifact type: {artifact}")


def audit_artifact(artifact: Path) -> None:
    bad: list[str] = []
    names = archive_names(artifact)

    for name in names:
        normalized = name.replace("\\", "/")
        lower = normalized.lower()
        basename = Path(normalized).name.lower()
        suffix = Path(normalized).suffix.lower()
        if lower.startswith(FORBIDDEN_PREFIXES):
            bad.append(normalized)
            continue
        if any(f"/{prefix}" in lower for prefix in ("third_party/", "outputs/")):
            bad.append(normalized)
            continue
        if any(marker in lower for marker in FORBIDDEN_VENDOR_MARKERS):
            bad.append(normalized)
            continue
        if lower.endswith(FORBIDDEN_SUFFIXES):
            bad.append(normalized)
            continue
        if suffix in {".h", ".hpp"} and basename.startswith(FORBIDDEN_HEADER_PREFIXES):
            bad.append(normalized)

    if bad:
        details = "\n".join(f"- {item}" for item in sorted(bad))
        raise RuntimeError(f"{artifact.name} contains forbidden release content:\n{details}")

    print(f"audited {len(names)} entries in {artifact.name}: ok", flush=True)


def install_and_smoke(artifact: Path) -> None:
    with tempfile.TemporaryDirectory(prefix="flycapture2_c_install_") as tmp:
        venv_dir = Path(tmp) / "venv"
        run([sys.executable, "-m", "venv", str(venv_dir)])
        python = venv_dir / "Scripts" / "python.exe"
        if not python.exists():
            python = venv_dir / "bin" / "python"
        run([str(python), "-m", "pip", "install", "--upgrade", "pip"])
        run([str(python), "-m", "pip", "install", str(artifact)])
        run(
            [
                str(python),
                "-c",
                "import flycapture2_c; print(flycapture2_c.__version__)",
            ]
        )
    print(f"clean install smoke passed: {artifact.name}", flush=True)


def main() -> int:
    run([sys.executable, "-m", "pytest", "-q"])
    run(
        [
            sys.executable,
            "-c",
            "import flycapture2_c; print(flycapture2_c.__version__)",
        ]
    )
    remove_generated_artifacts()
    artifacts = build_distributions()
    try:
        for artifact in artifacts:
            audit_artifact(artifact)
            install_and_smoke(artifact)
        print(
            "artifact audit and install smoke passed: "
            + ", ".join(artifact.name for artifact in artifacts),
            flush=True,
        )
    finally:
        for artifact in artifacts:
            artifact.unlink(missing_ok=True)
        remove_generated_artifacts()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
