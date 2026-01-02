"""
Statement quality validation for flashcard best practices.

Checks for atomicity, vague language, board relevance, and appropriate length.
"""

import re
from typing import List, Optional
from ..models import Statement
from .validator import ValidationIssue


def validate_statement_quality(statement: Statement, location: Optional[str]) -> List[ValidationIssue]:
    """
    Run all quality checks on a statement.

    Args:
        statement: Statement to validate
        location: Location string for error reporting

    Returns:
        List of validation issues
    """
    issues: List[ValidationIssue] = []

    issues.extend(check_atomicity(statement.statement, location))
    issues.extend(check_vague_language(statement.statement, location))
    issue = check_board_relevance(statement.statement, location)
    if issue:
        issues.append(issue)
    issue = check_statement_length(statement.statement, location)
    if issue:
        issues.append(issue)

    return issues


def check_atomicity(statement: str, location: Optional[str]) -> List[ValidationIssue]:
    """
    Check if statement contains multiple concepts.

    Flags statements with "and", "or", "also" that may indicate multiple concepts.

    Args:
        statement: Statement text
        location: Location string

    Returns:
        List of validation issues
    """
    issues: List[ValidationIssue] = []

    # Pattern for multi-concept indicators
    # Look for "and" or "or" connecting two clauses with verbs
    multi_concept_patterns = [
        r'\b(and|or)\b.*\b(is|are|causes|include|require|has|have|should)\b',
        r'\balso\b',
        r';\s*[A-Z]',  # Semicolon with capital letter (separate clause)
    ]

    for pattern in multi_concept_patterns:
        if re.search(pattern, statement, re.IGNORECASE):
            issues.append(ValidationIssue(
                severity="warning",
                category="quality",
                message=f"Possible multi-concept statement (contains compound structure)",
                location=location
            ))
            break  # Only flag once

    return issues


def check_vague_language(statement: str, location: Optional[str]) -> List[ValidationIssue]:
    """
    Check for vague qualifiers that reduce testability.

    Flags: "often", "usually", "may", "sometimes", "rarely", "commonly", "typically"

    Args:
        statement: Statement text
        location: Location string

    Returns:
        List of validation issues
    """
    issues: List[ValidationIssue] = []

    vague_terms = [
        "often", "usually", "may", "sometimes", "rarely",
        "commonly", "typically", "generally", "frequently",
        "occasionally", "possibly", "potentially"
    ]

    found_vague = []
    statement_lower = statement.lower()

    for term in vague_terms:
        # Use word boundaries to avoid false positives
        if re.search(rf'\b{term}\b', statement_lower):
            found_vague.append(term)

    if found_vague:
        issues.append(ValidationIssue(
            severity="info",
            category="quality",
            message=f"Vague language detected: {', '.join(found_vague)}",
            location=location
        ))

    return issues


def check_board_relevance(statement: str, location: Optional[str]) -> Optional[ValidationIssue]:
    """
    Check if statement is clinically relevant for board exams.

    Flags pure trivia without clinical context.

    Args:
        statement: Statement text
        location: Location string

    Returns:
        ValidationIssue if trivia detected, None otherwise
    """
    # Patterns that suggest pure trivia
    trivia_patterns = [
        r'is located in',
        r'is a type of',
        r'is also known as',
        r'is derived from',
        r'was discovered',
        r'is named after',
    ]

    for pattern in trivia_patterns:
        if re.search(pattern, statement, re.IGNORECASE):
            # Check if there's clinical context (treatment, diagnosis, prognosis)
            clinical_terms = [
                'treatment', 'therapy', 'diagnosis', 'management', 'prognosis',
                'indication', 'contraindication', 'complication', 'side effect',
                'symptom', 'sign', 'test', 'screening', 'prevention'
            ]

            has_clinical_context = any(
                re.search(rf'\b{term}\b', statement, re.IGNORECASE)
                for term in clinical_terms
            )

            if not has_clinical_context:
                return ValidationIssue(
                    severity="warning",
                    category="quality",
                    message="Possible trivia without clinical context",
                    location=location
                )
            break

    return None


def check_statement_length(statement: str, location: Optional[str]) -> Optional[ValidationIssue]:
    """
    Check if statement is too long for effective flashcard use.

    Warns if >200 characters (too complex for quick review).

    Args:
        statement: Statement text
        location: Location string

    Returns:
        ValidationIssue if too long, None otherwise
    """
    if len(statement) > 200:
        return ValidationIssue(
            severity="info",
            category="quality",
            message=f"Statement is long ({len(statement)} chars) - consider splitting",
            location=location
        )

    return None
