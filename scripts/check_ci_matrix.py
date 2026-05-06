from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PYTHON_VERSIONS = ("3.8", "3.9", "3.10", "3.11", "3.12", "3.13")


def find_python(version: str) -> list[str] | None:
    py = shutil.which("py")
    if py is not None:
        result = subprocess.run(
            [py, f"-{version}", "-c", "import sys; print(sys.version)"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            return [py, f"-{version}"]

    executable = shutil.which(f"python{version}") or shutil.which(f"python{version.replace('.', '')}")
    if executable is not None:
        return [executable]

    if version == f"{sys.version_info.major}.{sys.version_info.minor}":
        return [sys.executable]

    return None


def run(args: list[str], *, env: dict[str, str] | None = None) -> None:
    print("+ " + " ".join(args), flush=True)
    subprocess.run(args, cwd=ROOT, env=env, check=True)


def run_for_version(version: str, launcher: list[str]) -> None:
    with tempfile.TemporaryDirectory(prefix=f"flycapture2_c_py{version.replace('.', '')}_") as tmp:
        venv_dir = Path(tmp) / "venv"
        run([*launcher, "-m", "venv", str(venv_dir)])
        python = venv_dir / "Scripts" / "python.exe"
        if not python.exists():
            python = venv_dir / "bin" / "python"

        env = os.environ.copy()
        env["FLYCAPTURE2_HARDWARE_TEST"] = "0"
        env["FLYCAPTURE2_HARDWARE_WRITE_TEST"] = "0"
        env["FLYCAPTURE2_SDK_DIR"] = str(ROOT / "does_not_exist")
        env["FLYCAPTURE2_DLL_DIR"] = str(ROOT / "does_not_exist")

        run([str(python), "-m", "pip", "install", ".[dev]"], env=env)
        run([str(python), "-m", "pytest", "-q"], env=env)
        run(
            [
                str(python),
                "-c",
                "import flycapture2_c; print(flycapture2_c.__version__)",
            ],
            env=env,
        )


def main() -> int:
    passed = []
    failed = []
    missing = []
    for version in PYTHON_VERSIONS:
        launcher = find_python(version)
        if launcher is None:
            missing.append(version)
            continue
        print(f"== Python {version} ==", flush=True)
        try:
            run_for_version(version, launcher)
        except subprocess.CalledProcessError as exc:
            failed.append(f"{version} ({exc.cmd!r} exited {exc.returncode})")
            continue
        passed.append(version)

    if missing:
        print("missing local Python versions: " + ", ".join(missing), flush=True)
    if failed:
        print("failed local Python versions: " + "; ".join(failed), flush=True)
    if not passed:
        raise RuntimeError("no supported Python interpreters found")
    print("local no-hardware matrix passed: " + ", ".join(passed), flush=True)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
