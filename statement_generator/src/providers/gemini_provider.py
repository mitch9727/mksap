"""
DEPRECATED: Use src.infrastructure.llm.providers.gemini instead.

This module provides backward compatibility during the reorganization.
All imports will be redirected to the new location.
"""

import warnings

warnings.warn(
    "src.providers.gemini_provider is deprecated. Use src.infrastructure.llm.providers.gemini instead.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export all classes from new location
from .infrastructure.llm.providers.gemini import (
    GeminiProvider,
)

__all__ = [
    "GeminiProvider",
]
