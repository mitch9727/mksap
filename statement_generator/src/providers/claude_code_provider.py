"""
DEPRECATED: Use src.infrastructure.llm.providers.claude_code instead.

This module provides backward compatibility during the reorganization.
All imports will be redirected to the new location.
"""

import warnings

warnings.warn(
    "src.providers.claude_code_provider is deprecated. Use src.infrastructure.llm.providers.claude_code instead.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export all classes from new location
from .infrastructure.llm.providers.claude_code import (
    ClaudeCodeProvider,
)

__all__ = [
    "ClaudeCodeProvider",
]
