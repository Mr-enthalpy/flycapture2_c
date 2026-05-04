from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from flycapture2_c.api import get_api
from flycapture2_c.dll import describe_load_attempts
from flycapture2_c.errors import DLLLoadError, SDKNotFoundError


def main() -> int:
    print("Candidate DLL paths:")
    for path in describe_load_attempts():
        print(f"  - {path}")

    try:
        version = get_api().get_library_version()
    except (SDKNotFoundError, DLLLoadError) as exc:
        print(f"DLL load failed:\n{exc}")
        return 1

    print(f"DLL load succeeded. Library version: {version[0]}.{version[1]}.{version[2]}.{version[3]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
