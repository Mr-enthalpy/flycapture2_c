"""Raw-layer DLL loading and signature binding helpers."""

from __future__ import annotations

import ctypes

from ..dll import load_library
from .specs import bind_function_specs


def bind_library(dll: ctypes.CDLL) -> ctypes.CDLL:
    """Assign registered FlyCapture2 C signatures to an already-loaded DLL."""

    bind_function_specs(dll)
    return dll


def load_bound_library() -> ctypes.CDLL:
    """Lazily load the vendor DLL and bind all registered signatures."""

    dll = load_library()
    return bind_library(dll)


__all__ = ["bind_library", "load_bound_library"]
