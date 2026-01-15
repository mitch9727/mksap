"""
DEPRECATED: Use infrastructure.io.file_handler instead.

This module provides backward compatibility during the reorganization.
All imports will be redirected to the new location.
"""

import warnings

warnings.warn(
    "file_io is deprecated. Use infrastructure.io.file_handler instead.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export all classes from new location
from .infrastructure.io.file_handler import (
    QuestionFileIO,
)

__all__ = [
    "QuestionFileIO",
]
