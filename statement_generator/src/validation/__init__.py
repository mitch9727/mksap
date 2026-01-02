"""
Validation framework for statement extraction quality.

Provides validators for JSON structure, statement quality, cloze candidates,
and source fidelity (anti-hallucination detection).
"""

from .validator import StatementValidator, ValidationResult, ValidationIssue

__all__ = ["StatementValidator", "ValidationResult", "ValidationIssue"]
