"""
Base validator interface for statement validation.

Provides consistent interface for all validator modules.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Any


class ValidationIssue:
    """
    Represents a validation issue found in a statement.
    """

    def __init__(
        self,
        severity: str,
        category: str,
        message: str,
        location: Optional[str] = None
    ):
        """
        Create a validation issue.

        Args:
            severity: "error", "warning", or "info"
            category: Issue category (e.g., "negation", "entity_completeness")
            message: Description of the issue
            location: Location string for error reporting (e.g., "statement 3")
        """
        self.severity = severity
        self.category = category
        self.message = message
        self.location = location

    def __repr__(self):
        return f"ValidationIssue({self.severity}, {self.category}, {self.message})"


class BaseValidator(ABC):
    """
    Abstract base class for validators.

    All validators must implement validate() method.
    """

    @abstractmethod
    def validate(
        self,
        statement: Any,
        location: Optional[str] = None,
        **context
    ) -> List[ValidationIssue]:
        """
        Validate a statement.

        Args:
            statement: Statement to validate
            location: Location string for error reporting
            **context: Additional context (source text, NLP docs, etc.)

        Returns:
            List of validation issues (empty if no issues)
        """
        pass

    def _create_issue(
        self,
        severity: str,
        category: str,
        message: str,
        location: Optional[str] = None
    ) -> ValidationIssue:
        """
        Helper to create validation issue.

        Args:
            severity: "error", "warning", or "info"
            category: Issue category
            message: Description of issue
            location: Location string

        Returns:
            ValidationIssue object
        """
        return ValidationIssue(
            severity=severity,
            category=category,
            message=message,
            location=location
        )
