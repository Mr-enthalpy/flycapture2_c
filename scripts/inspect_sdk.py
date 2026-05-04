from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from flycapture2_c.dll import DEFAULT_DLL_DIRS, HEADER_RELATIVE_PATHS, PRIMARY_LIB_DIR, default_sdk_container, get_sdk_layout
from flycapture2_c.errors import SDKNotFoundError


def _status(path: Path) -> str:
    return "OK" if path.exists() else "MISSING"


def main() -> int:
    print(f"Default SDK container: {default_sdk_container()}")
    try:
        layout = get_sdk_layout()
    except SDKNotFoundError as exc:
        print(f"SDK root: MISSING\n{exc}")
        return 1

    print(f"SDK root: {layout.root}")
    for header in HEADER_RELATIVE_PATHS:
        full_path = layout.root / header
        print(f"[{_status(full_path)}] header {full_path}")

    for dll_dir in DEFAULT_DLL_DIRS:
        full_dir = layout.root / dll_dir
        dll_matches = sorted(path.name for path in full_dir.glob("FlyCapture2_C*.dll")) if full_dir.exists() else []
        suffix = f" ({', '.join(dll_matches)})" if dll_matches else ""
        print(f"[{_status(full_dir)}] dll dir {full_dir}{suffix}")

    lib_dir = layout.root / PRIMARY_LIB_DIR
    lib_matches = sorted(path.name for path in lib_dir.glob("FlyCapture2_C*.lib")) if lib_dir.exists() else []
    suffix = f" ({', '.join(lib_matches)})" if lib_matches else ""
    print(f"[{_status(lib_dir)}] lib dir {lib_dir}{suffix}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
