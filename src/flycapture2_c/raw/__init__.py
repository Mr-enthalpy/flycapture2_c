"""Low-level FlyCapture2 C API building blocks.

This package is the migration target for raw ctypes aliases, structures,
function signatures, and checked low-level SDK calls. The current top-level
modules remain compatible while the raw layer is filled in incrementally.
"""

from .specs import FUNCTION_SPECS, FunctionSpec, bind_function_specs, get_function_spec

__all__ = [
    "FUNCTION_SPECS",
    "FunctionSpec",
    "bind_function_specs",
    "get_function_spec",
]
