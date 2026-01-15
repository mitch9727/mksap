"""
DEPRECATED: Use infrastructure.llm.provider_manager instead.

This module provides backward compatibility during the reorganization.
All imports will be redirected to the new location.
"""

import warnings

warnings.warn(
    "provider_manager is deprecated. Use infrastructure.llm.provider_manager instead.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export all classes from new location
from .infrastructure.llm.provider_manager import (
    ProviderManager,
)

__all__ = [
    "ProviderManager",
]
