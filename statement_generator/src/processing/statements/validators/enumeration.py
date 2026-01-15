"""
Enumeration detection for cloze deletion flashcards.

Detects statements that test entire lists in a single card, violating the
"avoid enumerations" principle from spaced repetition best practices.

Based on CLOZE_FLASHCARD_BEST_PRACTICES.md Section 4:
- DO NOT test entire lists in one card
- Use overlapping chunked clozes for lists of 3+ items
- Example: "Drug X adverse effects include [...], [...], and nausea"
- Alternative: "One adverse effect of Drug X is [...] (other effects: A, B, C)"

References:
- https://www.supermemo.com/en/blog/twenty-rules-of-formulating-knowledge
- Rule 6: Avoid sets (enumerations)
"""

import re
from typing import List, Optional, Tuple
from src.infrastructure.models.data_models import Statement
from src.validation.validator import ValidationIssue


# List indicators in statement text
LIST_INDICATORS = [
    r'\binclude\b',
    r'\bconsist of\b',
    r'\bcomprised of\b',
    r'\bare as follows\b',
    r'\bsuch as\b',
]

# Conjunction patterns indicating lists
CONJUNCTION_PATTERNS = [
    r',\s*and\b',  # "A, B, and C"
    r',\s*or\b',   # "A, B, or C"
    r';\s*',       # "A; B; C"
]


def validate_statement_enumerations(statement: Statement, location: Optional[str]) -> List[ValidationIssue]:
    """
    Run all enumeration checks on a statement.

    Args:
        statement: Statement to validate
        location: Location string for error reporting

    Returns:
        List of validation issues
    """
    issues: List[ValidationIssue] = []

    # Check for list-style statements
    issues.extend(check_list_statement(statement, location))

    # Check for multiple items being tested together
    issues.extend(check_multi_item_cloze(statement, location))

    # Check for numeric enumerations
    issues.extend(check_numeric_enumeration(statement, location))

    return issues


def check_list_statement(statement: Statement, location: Optional[str]) -> List[ValidationIssue]:
    """
    Check if statement is testing a list/enumeration.

    Flags statements with list indicators followed by comma-separated items.

    Examples:
    - ❌ "Adverse effects include anaphylaxis, headache, and nausea"
    - ❌ "Risk factors consist of diabetes, hypertension, and smoking"
    - ✅ "One adverse effect of Drug X is anaphylaxis"
    - ✅ "Diabetes is a risk factor for cardiovascular disease"

    Args:
        statement: Statement to validate
        location: Location string

    Returns:
        List of validation issues
    """
    issues: List[ValidationIssue] = []
    stmt_text = statement.statement

    # Check if statement contains list indicators
    has_list_indicator = any(
        re.search(pattern, stmt_text, re.IGNORECASE)
        for pattern in LIST_INDICATORS
    )

    if not has_list_indicator:
        return issues

    # Check if statement contains comma-separated items (3+ items)
    item_count = count_list_items(stmt_text)

    if item_count >= 3:
        issues.append(ValidationIssue(
            severity="warning",
            category="enumeration",
            message=(
                f"Statement tests a list ({item_count} items). "
                f"Lists of 3+ items should be chunked with overlapping clozes or "
                f"rephrased as individual facts. "
                f"Example: 'One adverse effect is [...]' instead of testing all effects."
            ),
            location=location
        ))

    return issues


def check_multi_item_cloze(statement: Statement, location: Optional[str]) -> List[ValidationIssue]:
    """
    Check if multiple related cloze candidates are being tested together.

    Detects statements with multiple cloze candidates that represent a list
    of similar items (e.g., multiple adverse effects, multiple risk factors).

    Args:
        statement: Statement to validate
        location: Location string

    Returns:
        List of validation issues
    """
    issues: List[ValidationIssue] = []

    # Check if statement has 4+ cloze candidates (potential enumeration)
    if len(statement.cloze_candidates) >= 4:
        # Check if candidates appear in a list pattern in the statement
        candidates_in_sequence = check_candidates_in_sequence(
            statement.statement,
            statement.cloze_candidates
        )

        if candidates_in_sequence >= 3:
            issues.append(ValidationIssue(
                severity="warning",
                category="enumeration",
                message=(
                    f"Multiple cloze candidates ({candidates_in_sequence}) appear in sequence, "
                    f"suggesting an enumeration. Consider splitting into separate statements "
                    f"or using overlapping chunked clozes."
                ),
                location=location
            ))

    return issues


def check_numeric_enumeration(statement: Statement, location: Optional[str]) -> List[ValidationIssue]:
    """
    Check for statements testing step-by-step procedures or numbered lists.

    Examples:
    - ❌ "The steps are: (1) assess airway, (2) check breathing, (3) evaluate circulation"
    - ❌ "Three criteria include: A, B, and C"
    - ✅ "The first step in trauma assessment is airway evaluation"

    Args:
        statement: Statement to validate
        location: Location string

    Returns:
        List of validation issues
    """
    issues: List[ValidationIssue] = []
    stmt_lower = statement.statement.lower()

    # Check for numbered step indicators
    numbered_patterns = [
        r'\(\d+\)',        # (1), (2), (3)
        r'\d+\.',          # 1. 2. 3.
        r'\d+\)',          # 1) 2) 3)
        r'\bfirst\b.*\bsecond\b.*\bthird\b',
        r'\bstep \d+\b',
    ]

    for pattern in numbered_patterns:
        matches = re.findall(pattern, stmt_lower)
        if len(matches) >= 2:  # At least 2 steps/items
            issues.append(ValidationIssue(
                severity="warning",
                category="enumeration",
                message=(
                    f"Numbered enumeration detected ({len(matches)} items). "
                    f"Multi-step procedures should be split into individual statements, "
                    f"one per step, for better retention."
                ),
                location=location
            ))
            break

    # Check for explicit count indicators
    count_patterns = [
        r'\b(two|three|four|five|six)\s+(types|categories|classes|criteria|features|signs|symptoms)\b',
        r'\b\d+\s+(types|categories|classes|criteria|features|signs|symptoms)\b',
    ]

    for pattern in count_patterns:
        match = re.search(pattern, stmt_lower)
        if match:
            count_term = match.group(0)
            issues.append(ValidationIssue(
                severity="info",
                category="enumeration",
                message=(
                    f"Explicit count detected: '{count_term}'. "
                    f"Testing entire enumeration is difficult. "
                    f"Consider: 'One {match.group(1)} of X is [...]' format."
                ),
                location=location
            ))
            break

    return issues


def count_list_items(text: str) -> int:
    """
    Count the number of items in a comma/semicolon-separated list.

    Args:
        text: Statement text

    Returns:
        Number of list items detected
    """
    # Split by common separators
    # Handle "A, B, and C" or "A; B; C" patterns

    # Remove any trailing conjunctions
    text = re.sub(r',\s*(and|or)\s+', ',', text, flags=re.IGNORECASE)

    # Count commas and semicolons
    comma_count = text.count(',')
    semicolon_count = text.count(';')

    # Items = separators + 1 (if there are any separators)
    if comma_count > 0 or semicolon_count > 0:
        return comma_count + semicolon_count + 1

    return 0


def check_candidates_in_sequence(statement_text: str, candidates: List[str]) -> int:
    """
    Check how many cloze candidates appear in sequence (list pattern).

    Args:
        statement_text: Full statement text
        candidates: List of cloze candidates

    Returns:
        Number of candidates appearing in sequence
    """
    # Find positions of each candidate in the statement
    positions = []
    for candidate in candidates:
        # Case-insensitive search
        match = re.search(re.escape(candidate), statement_text, re.IGNORECASE)
        if match:
            positions.append((match.start(), candidate))

    # Sort by position
    positions.sort()

    # Count candidates that appear with only minor text between them
    # (commas, conjunctions, prepositions)
    sequential_count = 0
    if len(positions) >= 2:
        for i in range(len(positions) - 1):
            pos1, cand1 = positions[i]
            pos2, cand2 = positions[i + 1]

            # Text between candidates
            between_text = statement_text[pos1 + len(cand1):pos2].strip()

            # Check if it's just a separator (comma, "and", "or", etc.)
            if re.match(r'^[,;]?\s*(and|or)?\s*$', between_text, re.IGNORECASE):
                sequential_count += 1

    # Add 1 to count first candidate if there's a sequence
    if sequential_count > 0:
        sequential_count += 1

    return sequential_count


def check_comprehensive_coverage_claim(statement: Statement, location: Optional[str]) -> List[ValidationIssue]:
    """
    Check for statements claiming comprehensive coverage (e.g., "all", "every", "complete").

    Such statements often try to test entire sets, which is ineffective for flashcards.

    Examples:
    - ❌ "All adverse effects of Drug X include..."
    - ❌ "Every diagnostic criterion for Disease Y is..."
    - ❌ "Complete list of risk factors includes..."

    Args:
        statement: Statement to validate
        location: Location string

    Returns:
        List of validation issues
    """
    issues: List[ValidationIssue] = []
    stmt_lower = statement.statement.lower()

    comprehensive_terms = [
        r'\ball\b',
        r'\bevery\b',
        r'\bcomplete list\b',
        r'\bfull list\b',
        r'\bentire set\b',
        r'\beach of the\b',
    ]

    for pattern in comprehensive_terms:
        if re.search(pattern, stmt_lower):
            pattern_label = pattern.replace(r"\b", "")
            issues.append(ValidationIssue(
                severity="warning",
                category="enumeration",
                message=(
                    f"Comprehensive coverage claim detected ('{pattern_label}'). "
                    f"Testing complete sets is ineffective. Use partial examples instead: "
                    f"'One adverse effect...' or 'Examples include...'"
                ),
                location=location
            ))
            break

    return issues
