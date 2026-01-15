"""
DEPRECATED: Use infrastructure.llm.exceptions instead.

This module provides backward compatibility during the reorganization.
All imports will be redirected to the new location.
"""

import warnings

warnings.warn(
    "provider_exceptions is deprecated. Use infrastructure.llm.exceptions instead.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export all classes from new location
from .infrastructure.llm.exceptions import (
    ProviderException,
    ProviderRateLimitError,
    ProviderAuthError,
)

__all__ = [
    "ProviderException",
    "ProviderRateLimitError",
    "ProviderAuthError",
]
