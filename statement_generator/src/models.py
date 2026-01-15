"""
DEPRECATED: Use src.infrastructure.models.data_models instead.

This module provides backward compatibility during the reorganization.
All imports will be redirected to the new location.
"""

import warnings

warnings.warn(
    "src.models is deprecated. Use src.infrastructure.models.data_models instead.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export all classes from new location
from .infrastructure.models.data_models import (
    Statement,
    TrueStatements,
    TableStatement,
    TableStatements,
    QuestionData,
    ProcessingResult,
    CheckpointData,
)

__all__ = [
    "Statement",
    "TrueStatements",
    "TableStatement",
    "TableStatements",
    "QuestionData",
    "ProcessingResult",
    "CheckpointData",
]
