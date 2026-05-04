from __future__ import annotations

import ctypes
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .errors import DLLLoadError, SDKNotFoundError

ENV_SDK_DIR = "FLYCAPTURE2_SDK_DIR"
ENV_DLL_DIR = "FLYCAPTURE2_DLL_DIR"
DEFAULT_SDK_CONTAINER = "third_party"
SDK_SUBDIR_NAME = "FlyCapture2"
HEADER_RELATIVE_PATHS = (
    Path("include/C/FlyCapture2_C.h"),
    Path("include/C/FlyCapture2Defs_C.h"),
    Path("include/C/FlyCapture2Platform_C.h"),
)
DEFAULT_DLL_DIRS = (
    Path("bin64/vs2015"),
    Path("bin64"),
    Path("bin64/vs2013"),
)
PRIMARY_LIB_DIR = Path("lib64/C")


@dataclass(frozen=True)
class SDKLayout:
    root: Path
    include_dir: Path
    lib_dir: Path
    dll_dirs: tuple[Path, ...]


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def default_sdk_container() -> Path:
    return project_root() / DEFAULT_SDK_CONTAINER


def _looks_like_sdk_root(path: Path) -> bool:
    return all((path / relative_path).exists() for relative_path in HEADER_RELATIVE_PATHS)


def _candidate_sdk_roots(base: Path) -> list[Path]:
    candidates = [base]
    child = base / SDK_SUBDIR_NAME
    if child not in candidates:
        candidates.append(child)
    return candidates


def resolve_sdk_root(explicit: str | os.PathLike[str] | None = None) -> Path:
    base = Path(explicit) if explicit is not None else Path(os.environ.get(ENV_SDK_DIR, default_sdk_container()))
    base = base.expanduser().resolve()
    for candidate in _candidate_sdk_roots(base):
        if _looks_like_sdk_root(candidate):
            return candidate
    searched = ", ".join(str(path) for path in _candidate_sdk_roots(base))
    raise SDKNotFoundError(
        f"FlyCapture2 SDK headers were not found. Searched: {searched}. "
        f"Set {ENV_SDK_DIR} to the SDK root or to a parent directory containing {SDK_SUBDIR_NAME}/."
    )


def get_sdk_layout(explicit: str | os.PathLike[str] | None = None) -> SDKLayout:
    root = resolve_sdk_root(explicit=explicit)
    dll_dirs = tuple((root / relative_dir).resolve() for relative_dir in DEFAULT_DLL_DIRS)
    return SDKLayout(
        root=root,
        include_dir=(root / "include").resolve(),
        lib_dir=(root / PRIMARY_LIB_DIR).resolve(),
        dll_dirs=dll_dirs,
    )


def get_dll_search_dirs(
    *,
    sdk_root: str | os.PathLike[str] | None = None,
    dll_dir: str | os.PathLike[str] | None = None,
) -> list[Path]:
    override = dll_dir if dll_dir is not None else os.environ.get(ENV_DLL_DIR)
    if override:
        path = Path(override).expanduser().resolve()
        if path.is_file():
            return [path.parent]
        return [path]

    layout = get_sdk_layout(explicit=sdk_root)
    return list(layout.dll_dirs)


def _dll_sort_key(path: Path) -> tuple[int, int, str]:
    name = path.name.lower()
    debug_rank = 1 if "_cd_" in name else 0
    if "v140" in name:
        version_rank = 0
    elif "v120" in name:
        version_rank = 1
    elif "v100" in name:
        version_rank = 2
    else:
        version_rank = 99
    return (debug_rank, version_rank, name)


def iter_candidate_dll_paths(
    *,
    sdk_root: str | os.PathLike[str] | None = None,
    dll_dir: str | os.PathLike[str] | None = None,
) -> list[Path]:
    override = dll_dir if dll_dir is not None else os.environ.get(ENV_DLL_DIR)
    if override:
        override_path = Path(override).expanduser().resolve()
        if override_path.is_file():
            return [override_path]

    candidates: list[Path] = []
    for directory in get_dll_search_dirs(sdk_root=sdk_root, dll_dir=dll_dir):
        if not directory.exists():
            continue
        matches = sorted(directory.glob("FlyCapture2_C*.dll"), key=_dll_sort_key)
        candidates.extend(path.resolve() for path in matches)
    return candidates


def describe_load_attempts(
    *,
    sdk_root: str | os.PathLike[str] | None = None,
    dll_dir: str | os.PathLike[str] | None = None,
) -> list[Path]:
    directories = get_dll_search_dirs(sdk_root=sdk_root, dll_dir=dll_dir)
    candidates = iter_candidate_dll_paths(sdk_root=sdk_root, dll_dir=dll_dir)
    if candidates:
        return candidates
    return [directory / "FlyCapture2_C*.dll" for directory in directories]


def _add_dll_directories(paths: Iterable[Path]) -> list[object]:
    handles: list[object] = []
    add_directory = getattr(os, "add_dll_directory", None)
    if add_directory is None:
        return handles

    seen: set[Path] = set()
    for path in paths:
        directory = path if path.is_dir() else path.parent
        if directory in seen or not directory.exists():
            continue
        handles.append(add_directory(str(directory)))
        seen.add(directory)
    return handles


def load_library(
    *,
    sdk_root: str | os.PathLike[str] | None = None,
    dll_dir: str | os.PathLike[str] | None = None,
) -> ctypes.CDLL:
    attempts = describe_load_attempts(sdk_root=sdk_root, dll_dir=dll_dir)
    candidates = [path for path in attempts if path.exists()]
    if not candidates:
        attempted = "\n".join(f"  - {path}" for path in attempts)
        raise DLLLoadError(
            "FlyCapture2 C DLL was not found in any candidate location.\n"
            f"Attempted:\n{attempted}"
        )

    last_error: Exception | None = None
    for candidate in candidates:
        try:
            dll_handles = _add_dll_directories([candidate.parent, *candidate.parent.glob("*.dll")])
            library = ctypes.CDLL(str(candidate))
            setattr(library, "_flycapture2_added_dll_dirs", dll_handles)
            setattr(library, "_flycapture2_path", candidate)
            return library
        except OSError as exc:
            last_error = exc

    attempted = "\n".join(f"  - {path}" for path in candidates)
    raise DLLLoadError(
        "Failed to load the FlyCapture2 C DLL from all discovered candidates.\n"
        f"Attempted:\n{attempted}\n"
        f"Last error: {last_error}"
    )
