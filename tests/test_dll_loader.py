from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from flycapture2_c.dll import describe_load_attempts, get_dll_search_dirs, resolve_sdk_root
from flycapture2_c.errors import SDKNotFoundError


def test_resolve_sdk_root_supports_parent_directory(tmp_path: Path) -> None:
    sdk_root = tmp_path / "third_party" / "FlyCapture2"
    (sdk_root / "include" / "C").mkdir(parents=True)
    for header in ("FlyCapture2_C.h", "FlyCapture2Defs_C.h", "FlyCapture2Platform_C.h"):
        (sdk_root / "include" / "C" / header).write_text("// test\n", encoding="utf-8")

    resolved = resolve_sdk_root(tmp_path / "third_party")
    assert resolved == sdk_root.resolve()


def test_get_dll_search_dirs_prefers_explicit_directory(tmp_path: Path) -> None:
    dll_dir = tmp_path / "dlls"
    dll_dir.mkdir()
    search_dirs = get_dll_search_dirs(dll_dir=dll_dir)
    assert search_dirs == [dll_dir.resolve()]


def test_describe_load_attempts_reports_candidates_when_missing(tmp_path: Path) -> None:
    sdk_root = tmp_path / "FlyCapture2"
    (sdk_root / "include" / "C").mkdir(parents=True)
    for header in ("FlyCapture2_C.h", "FlyCapture2Defs_C.h", "FlyCapture2Platform_C.h"):
        (sdk_root / "include" / "C" / header).write_text("// test\n", encoding="utf-8")
    attempts = describe_load_attempts(sdk_root=sdk_root)
    assert attempts
    assert any("FlyCapture2_C*.dll" in str(path) for path in attempts)


def test_resolve_sdk_root_raises_clear_error(tmp_path: Path) -> None:
    with pytest.raises(SDKNotFoundError) as exc_info:
        resolve_sdk_root(tmp_path / "missing")
    assert "FlyCapture2 SDK headers were not found" in str(exc_info.value)


def test_check_dll_load_script_reports_clear_error_when_dll_missing(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    missing_dll_dir = tmp_path / "missing_dlls"
    missing_dll_dir.mkdir()
    env = os.environ.copy()
    env["PYTHONPATH"] = str(root)
    env["FLYCAPTURE2_DLL_DIR"] = str(missing_dll_dir)
    result = subprocess.run(
        [sys.executable, str(root / "scripts" / "check_dll_load.py")],
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1
    assert "DLL load failed" in result.stdout
    assert "Attempted" in result.stdout
