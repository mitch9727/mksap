"""
DEPRECATED: Use infrastructure.llm.client instead.

This module provides backward compatibility during the reorganization.
All imports will be redirected to the new location.
"""

import warnings

warnings.warn(
    "llm_client is deprecated. Use infrastructure.llm.client instead.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export all classes from new location
from .infrastructure.llm.client import (
    ClaudeClient,
    LLMClient,
)

__all__ = [
    "ClaudeClient",
    "LLMClient",
]
