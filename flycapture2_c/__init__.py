from __future__ import annotations

from pathlib import Path

_SRC_PACKAGE_DIR = Path(__file__).resolve().parents[1] / "src" / "flycapture2_c"
__file__ = str(_SRC_PACKAGE_DIR / "__init__.py")
__path__ = [str(_SRC_PACKAGE_DIR)]

with open(__file__, "r", encoding="utf-8") as handle:
    exec(compile(handle.read(), __file__, "exec"))
