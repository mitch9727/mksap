"""
DEPRECATED: Use src.infrastructure.llm.providers.codex instead.

This module provides backward compatibility during the reorganization.
All imports will be redirected to the new location.
"""

import warnings

warnings.warn(
    "src.providers.codex_provider is deprecated. Use src.infrastructure.llm.providers.codex instead.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export all classes from new location
from .infrastructure.llm.providers.codex import (
    CodexProvider,
)

__all__ = [
    "CodexProvider",
]
