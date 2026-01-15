"""
DEPRECATED: Use src.infrastructure.llm.providers.anthropic instead.

This module provides backward compatibility during the reorganization.
All imports will be redirected to the new location.
"""

import warnings

warnings.warn(
    "src.providers.anthropic_provider is deprecated. Use src.infrastructure.llm.providers.anthropic instead.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export all classes from new location
from .infrastructure.llm.providers.anthropic import (
    AnthropicProvider,
)

__all__ = [
    "AnthropicProvider",
]
