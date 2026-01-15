"""
DEPRECATED: Use src.infrastructure.config.settings instead.

This module provides backward compatibility during the reorganization.
All imports will be redirected to the new location.
"""

import warnings

warnings.warn(
    "src.config is deprecated. Use src.infrastructure.config.settings instead.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export all classes from new location
from .infrastructure.config.settings import (
    LLMConfig,
    ProcessingConfig,
    PathsConfig,
    Config,
    PROJECT_ROOT,
    ENV_PATH,
)

__all__ = [
    "LLMConfig",
    "ProcessingConfig",
    "PathsConfig",
    "Config",
    "PROJECT_ROOT",
    "ENV_PATH",
]
