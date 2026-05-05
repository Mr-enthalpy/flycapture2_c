"""Compatibility entry point for the checked raw API wrapper.

The checked implementation still lives in ``flycapture2_c.api`` for public
compatibility. New raw-layer work should migrate implementation details here
incrementally while preserving imports from the existing module.
"""

from ..api import FlyCapture2CAPI, get_api

__all__ = ["FlyCapture2CAPI", "get_api"]
