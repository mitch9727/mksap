"""
DEPRECATED: Use src.infrastructure.llm.base_provider instead.

This module provides backward compatibility during the reorganization.
All imports will be redirected to the new location.
"""

import warnings

warnings.warn(
    "src.providers.base is deprecated. Use src.infrastructure.llm.base_provider instead.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export all classes from new location
from .infrastructure.llm.base_provider import (
    BaseLLMProvider,
)

__all__ = [
    "BaseLLMProvider",
]
