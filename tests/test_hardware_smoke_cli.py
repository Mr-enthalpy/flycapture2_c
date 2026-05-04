from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def test_hardware_smoke_skips_without_env() -> None:
    root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env.pop("FLYCAPTURE2_HARDWARE_TEST", None)
    result = subprocess.run(
        [sys.executable, str(root / "scripts" / "hardware_smoke.py"), "--level", "readonly"],
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "Hardware smoke skipped" in result.stdout
