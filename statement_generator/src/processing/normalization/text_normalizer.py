"""
Text normalization utilities for medical statements.

Converts verbose mathematical expressions to symbolic notation.
"""

import re
from typing import List

from ...infrastructure.models.data_models import Statement


class TextNormalizer:
    """Normalize medical text for better readability"""

    # Mathematical operator replacements
    OPERATORS = {
        # Inequalities
        r'\bless than\b': '<',
        r'\bgreater than\b': '>',
        r'\bless than or equal to\b': '≤',
        r'\bgreater than or equal to\b': '≥',
        r'\bequal to\b(?! the)': '=',  # Negative lookahead to avoid "equal to the"
        r'\bnot equal to\b': '≠',

        # Approximate
        r'\bapproximately\b': '~',

        # Plus/minus
        r'\bplus or minus\b': '±',
        r'\bplus-minus\b': '±',

        # Multiplication/division (less common in medical text)
        r'\bmultiplied by\b': '×',
        r'\bdivided by\b': '÷',
    }

    def __init__(self):
        """Initialize normalizer with compiled patterns"""
        self.patterns = {
            re.compile(pattern, re.IGNORECASE): replacement
            for pattern, replacement in self.OPERATORS.items()
        }

    def normalize_statement(self, statement: Statement) -> Statement:
        """
        Normalize mathematical expressions in a statement.

        Args:
            statement: Statement to normalize

        Returns:
            New Statement with normalized text
        """
        normalized_text = self._normalize_text(statement.statement)

        # Also normalize extra_field if present
        normalized_extra = None
        if statement.extra_field:
            normalized_extra = self._normalize_text(statement.extra_field)

        # Return new statement with normalized text
        return Statement(
            statement=normalized_text,
            extra_field=normalized_extra,
            cloze_candidates=statement.cloze_candidates,  # Keep original candidates
        )

    def normalize_statements(self, statements: List[Statement]) -> List[Statement]:
        """
        Normalize a list of statements.

        Args:
            statements: List of statements to normalize

        Returns:
            List of normalized statements
        """
        return [self.normalize_statement(stmt) for stmt in statements]

    def _normalize_text(self, text: str) -> str:
        """
        Apply all normalization patterns to text.

        Args:
            text: Text to normalize

        Returns:
            Normalized text
        """
        normalized = text

        for pattern, replacement in self.patterns.items():
            normalized = pattern.sub(replacement, normalized)

        return normalized
