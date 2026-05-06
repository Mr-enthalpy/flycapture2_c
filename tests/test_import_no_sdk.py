from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def test_import_succeeds_without_touching_sdk() -> None:
    root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(root / "src")
    env["FLYCAPTURE2_SDK_DIR"] = str(root / "does_not_exist")
    env["FLYCAPTURE2_DLL_DIR"] = str(root / "does_not_exist")
    result = subprocess.run(
        [sys.executable, "-c", "import flycapture2_c"],
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_public_exports_import_without_touching_sdk() -> None:
    root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(root / "src")
    env["FLYCAPTURE2_SDK_DIR"] = str(root / "does_not_exist")
    env["FLYCAPTURE2_DLL_DIR"] = str(root / "does_not_exist")
    code = (
        "import flycapture2_c\n"
        "missing = [name for name in flycapture2_c.__all__ if not hasattr(flycapture2_c, name)]\n"
        "assert not missing, missing\n"
        "for name in flycapture2_c.__all__:\n"
        "    getattr(flycapture2_c, name)\n"
        "assert flycapture2_c.__version__ == '0.6.0'\n"
        "print('ok')\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "ok"
