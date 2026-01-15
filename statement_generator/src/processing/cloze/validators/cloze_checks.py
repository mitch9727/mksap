"""
Cloze candidate validation for flashcard creation.

Validates count, existence in statement, uniqueness, and quality of cloze candidates.
"""

import re
from typing import List, Optional, Set
from ..models import Statement
from .validator import ValidationIssue


def validate_statement_clozes(statement: Statement, location: Optional[str]) -> List[ValidationIssue]:
    """
    Run all cloze validation checks on a statement.

    Args:
        statement: Statement to validate
        location: Location string for error reporting

    Returns:
        List of validation issues
    """
    issues: List[ValidationIssue] = []

    issues.extend(validate_cloze_count(statement, location))
    issues.extend(validate_cloze_candidates_exist_in_statement(statement, location))
    issues.extend(validate_cloze_uniqueness(statement, location))
    issues.extend(check_trivial_clozes(statement.cloze_candidates, location))

    return issues


def validate_cloze_count(statement: Statement, location: Optional[str]) -> List[ValidationIssue]:
    """
    Validate that statement has 2-5 cloze candidates.

    Args:
        statement: Statement to validate
        location: Location string

    Returns:
        List of validation issues
    """
    issues: List[ValidationIssue] = []
    count = len(statement.cloze_candidates)

    if count < 2:
        issues.append(ValidationIssue(
            severity="warning",
            category="cloze",
            message=f"Too few cloze candidates ({count}) - should have 2-5",
            location=location
        ))
    elif count > 5:
        issues.append(ValidationIssue(
            severity="info",
            category="cloze",
            message=f"Many cloze candidates ({count}) - may be excessive",
            location=location
        ))

    return issues


def validate_cloze_candidates_exist_in_statement(statement: Statement, location: Optional[str]) -> List[ValidationIssue]:
    """
    Validate that all cloze candidates appear in the statement text.

    Args:
        statement: Statement to validate
        location: Location string

    Returns:
        List of validation issues
    """
    issues: List[ValidationIssue] = []
    statement_text = statement.statement.lower()
    normalized_statement = _normalize_for_match(statement_text)

    for candidate in statement.cloze_candidates:
        # Case-insensitive search
        candidate_lower = candidate.lower()
        if candidate_lower in statement_text:
            continue
        if _normalize_for_match(candidate_lower) in normalized_statement:
            continue
        if candidate_lower not in statement_text:
            issues.append(ValidationIssue(
                severity="error",
                category="cloze",
                message=f"Cloze candidate '{candidate}' not found in statement",
                location=location
            ))

    return issues


def _normalize_for_match(text: str) -> str:
    """
    Normalize text for cloze candidate substring matching.

    Handles unicode dashes, comparator phrasing, and whitespace.
    """
    normalized = text.lower()
    normalized = normalized.replace("\u2013", "-").replace("\u2014", "-").replace("\u2011", "-")
    normalized = normalized.replace("\u00a0", " ")
    normalized = normalized.replace("≤", "<=").replace("≥", ">=")
    replacements = {
        "less than or equal to": "<=",
        "greater than or equal to": ">=",
        "less than": "<",
        "greater than": ">",
    }
    for phrase, symbol in replacements.items():
        normalized = normalized.replace(phrase, symbol)
    normalized = re.sub(r"\s*<\s*", "<", normalized)
    normalized = re.sub(r"\s*>\s*", ">", normalized)
    normalized = re.sub(r"\s*<=\s*", "<=", normalized)
    normalized = re.sub(r"\s*>=\s*", ">=", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def validate_cloze_uniqueness(statement: Statement, location: Optional[str]) -> List[ValidationIssue]:
    """
    Validate that cloze candidates are unique (no duplicates).

    Args:
        statement: Statement to validate
        location: Location string

    Returns:
        List of validation issues
    """
    issues: List[ValidationIssue] = []

    # Check for exact duplicates
    seen: Set[str] = set()
    duplicates: Set[str] = set()

    for candidate in statement.cloze_candidates:
        if candidate in seen:
            duplicates.add(candidate)
        seen.add(candidate)

    if duplicates:
        issues.append(ValidationIssue(
            severity="warning",
            category="cloze",
            message=f"Duplicate cloze candidates: {', '.join(duplicates)}",
            location=location
        ))

    # Check for case-insensitive duplicates
    seen_lower: Set[str] = set()
    case_duplicates: Set[str] = set()

    for candidate in statement.cloze_candidates:
        lower = candidate.lower()
        if lower in seen_lower and candidate not in duplicates:
            case_duplicates.add(candidate)
        seen_lower.add(lower)

    if case_duplicates:
        issues.append(ValidationIssue(
            severity="info",
            category="cloze",
            message=f"Case-insensitive duplicate candidates: {', '.join(case_duplicates)}",
            location=location
        ))

    return issues


def check_trivial_clozes(candidates: List[str], location: Optional[str]) -> List[ValidationIssue]:
    """
    Check for trivial or non-testable cloze candidates.

    Flags:
    - Single letters (except units like "L", "g", "mg")
    - Articles ("the", "a", "an")
    - Common words ("is", "are", "and", "or", "of", "in", "on", "at")
    - Very short candidates (<2 chars) that aren't medical abbreviations

    Args:
        candidates: List of cloze candidates
        location: Location string

    Returns:
        List of validation issues
    """
    issues: List[ValidationIssue] = []

    # Common articles and words
    trivial_words = {
        "the", "a", "an", "is", "are", "was", "were", "be", "been",
        "and", "or", "but", "not", "of", "in", "on", "at", "to", "for",
        "with", "by", "from", "as", "if", "can", "may", "will", "would"
    }

    # Known medical abbreviations that are OK when short
    medical_abbreviations = {
        "bp", "hr", "rr", "o2", "co2", "hb", "wbc", "rbc", "plt",
        "na", "k", "ca", "mg", "cl", "bun", "cr", "gfr", "alt", "ast",
        "ldl", "hdl", "tg", "tsh", "t3", "t4", "hba1c", "inr", "pt", "ptt"
    }

    for candidate in candidates:
        candidate_lower = candidate.lower().strip()

        # Check for trivial words
        if candidate_lower in trivial_words:
            issues.append(ValidationIssue(
                severity="warning",
                category="cloze",
                message=f"Trivial cloze candidate: '{candidate}' (common word)",
                location=location
            ))
            continue

        # Check for very short non-medical terms
        if len(candidate_lower) == 1:
            # Single letters OK if they're units or common abbreviations
            if candidate_lower not in ['l', 'g', 'h', 'm', 's']:  # liter, gram, hour, meter, second
                issues.append(ValidationIssue(
                    severity="warning",
                    category="cloze",
                    message=f"Trivial cloze candidate: '{candidate}' (single letter)",
                    location=location
                ))
        elif len(candidate_lower) == 2:
            # Two letters OK if medical abbreviation
            if candidate_lower not in medical_abbreviations:
                issues.append(ValidationIssue(
                    severity="info",
                    category="cloze",
                    message=f"Short cloze candidate: '{candidate}' (may be too simple)",
                    location=location
                ))

        # Check for numeric-only candidates (unless with units)
        if re.match(r'^\d+$', candidate_lower):
            issues.append(ValidationIssue(
                severity="info",
                category="cloze",
                message=f"Numeric-only cloze candidate: '{candidate}' (consider including units)",
                location=location
            ))

    return issues
