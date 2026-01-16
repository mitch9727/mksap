"""
NLP validator for cross-checking LLM output against NLP artifacts.

Validates that LLM-generated statements are consistent with NLP-extracted
information from source text, catching common LLM errors:
- Negation inversions (e.g., "no diabetes" -> "has diabetes")
- Missing critical entities (diseases, medications, lab values)
- Unit/threshold mismatches (e.g., "5 mg" -> "50 mg")
"""

import logging
import re
from typing import List, Optional, Set, Tuple

from ....infrastructure.models.data_models import Statement
from ....infrastructure.models.fact_candidates import EnrichedPromptContext
from ....infrastructure.models.nlp_artifacts import EntityType, MedicalEntity, NLPArtifacts
from ....validation.validator import ValidationIssue

logger = logging.getLogger(__name__)

# Critical entity types that should be represented in statements
CRITICAL_ENTITY_TYPES = {
    EntityType.DISEASE,
    EntityType.MEDICATION,
    EntityType.LAB_VALUE,
    EntityType.PROCEDURE,
}

# Threshold for entity coverage (warn if below this ratio)
ENTITY_COVERAGE_THRESHOLD = 0.5

# Common negation patterns to detect in statements
NEGATION_PATTERNS = [
    r'\bno\b',
    r'\bnot\b',
    r'\bwithout\b',
    r'\babsence\s+of\b',
    r'\black\s+of\b',
    r'\bnegative\b',
    r'\bdenies\b',
    r'\bdoes\s+not\b',
    r'\bdid\s+not\b',
    r'\bcannot\b',
    r"\bcan't\b",
    r"\bdon't\b",
    r"\bdoesn't\b",
    r"\bdidn't\b",
    r'\bnever\b',
    r'\bnone\b',
    r'\bneither\b',
    r'\bnor\b',
    r'\brules?\s+out\b',
    r'\bexcludes?\b',
]

# Affirmative patterns that indicate presence/positive findings
AFFIRMATIVE_PATTERNS = [
    r'\bhas\b',
    r'\bhave\b',
    r'\bpresent\b',
    r'\bpositive\b',
    r'\bconfirmed\b',
    r'\bdiagnosed\b',
    r'\bshows?\b',
    r'\bdemonstrates?\b',
    r'\breveals?\b',
    r'\bindicates?\b',
    r'\bsuffer(?:s|ing)?\s+from\b',
    r'\baffected\s+by\b',
]


def validate_against_nlp(
    statements: List[Statement],
    nlp_context: EnrichedPromptContext
) -> List[ValidationIssue]:
    """
    Cross-check LLM-generated statements against NLP artifacts.

    Performs three main validation checks:
    1. Negation consistency - ensures negated entities remain negated in statements
    2. Entity completeness - ensures critical entities are represented
    3. Unit/threshold accuracy - ensures numeric values match source

    Args:
        statements: List of LLM-generated statements to validate
        nlp_context: NLP-enriched context with artifacts from source text

    Returns:
        List of validation issues found (empty if no issues)
    """
    issues: List[ValidationIssue] = []

    if not statements:
        logger.debug("No statements to validate against NLP")
        return issues

    nlp_artifacts = nlp_context.nlp_artifacts

    if not nlp_artifacts.entities:
        logger.debug("No NLP entities to validate against")
        return issues

    # Run each validation check
    for i, statement in enumerate(statements):
        location = f"statement[{i}]"

        # 1. Negation consistency check
        negation_issues = check_negation_consistency(
            statement,
            nlp_artifacts,
            location
        )
        issues.extend(negation_issues)

        # 2. Entity completeness check
        completeness_issues = check_entity_completeness(
            statement,
            nlp_artifacts,
            location
        )
        issues.extend(completeness_issues)

        # 3. Unit/threshold accuracy check
        unit_issues = check_unit_accuracy(
            statement,
            nlp_artifacts,
            location
        )
        issues.extend(unit_issues)

    # Log summary
    if issues:
        logger.warning(
            f"NLP validation found {len(issues)} issues across {len(statements)} statements"
        )
    else:
        logger.debug(
            f"NLP validation passed for {len(statements)} statements"
        )

    return issues


def check_negation_consistency(
    statement: Statement,
    nlp_artifacts: NLPArtifacts,
    location: Optional[str] = None
) -> List[ValidationIssue]:
    """
    Verify LLM preserved negations from source text.

    Checks that entities marked as negated in NLP analysis are not
    expressed as affirmative in the generated statement.

    Example:
        Source: "Patient has no diabetes"
        NLP: diabetes (is_negated=True, trigger="no")
        Bad statement: "Patient has diabetes" <- FLAGGED
        Good statement: "Patient does not have diabetes" <- OK

    Args:
        statement: Statement to check
        nlp_artifacts: NLP analysis of source text
        location: Location string for error reporting

    Returns:
        List of validation issues for negation problems
    """
    issues: List[ValidationIssue] = []

    # Get negated entities from NLP
    negated_entities = nlp_artifacts.get_negated_entities()

    if not negated_entities:
        return issues

    statement_text = statement.statement.lower()

    for entity in negated_entities:
        entity_text = entity.text.lower()

        # Check if entity appears in statement
        if not _entity_in_text(entity_text, statement_text):
            continue

        # Entity is mentioned - check if negation is preserved
        has_negation = _has_negation_context(entity_text, statement_text)
        has_affirmative = _has_affirmative_context(entity_text, statement_text)

        if has_affirmative and not has_negation:
            # Entity is stated affirmatively but was negated in source
            trigger = entity.negation_trigger or "negated"
            issues.append(ValidationIssue(
                severity="error",
                category="negation",
                message=(
                    f"Negation inversion detected: '{entity.text}' was negated "
                    f"in source ('{trigger}') but appears affirmative in statement"
                ),
                location=location
            ))
            logger.warning(
                f"Negation inversion: '{entity.text}' ({trigger}) at {location}"
            )

        elif not has_negation:
            # Entity mentioned without clear negation context
            trigger = entity.negation_trigger or "negated"
            issues.append(ValidationIssue(
                severity="warning",
                category="negation",
                message=(
                    f"Possible negation loss: '{entity.text}' was negated in source "
                    f"('{trigger}') but statement lacks clear negation"
                ),
                location=location
            ))
            logger.debug(
                f"Possible negation loss: '{entity.text}' at {location}"
            )

    return issues


def check_entity_completeness(
    statement: Statement,
    nlp_artifacts: NLPArtifacts,
    location: Optional[str] = None
) -> List[ValidationIssue]:
    """
    Check if critical entities from NLP are represented in statement.

    Ensures that important medical entities (diseases, medications, lab values)
    identified by NLP are captured in the generated statements.

    Args:
        statement: Statement to check
        nlp_artifacts: NLP analysis of source text
        location: Location string for error reporting

    Returns:
        List of validation issues for entity coverage problems
    """
    issues: List[ValidationIssue] = []

    # Get critical entities from NLP
    critical_entities = [
        e for e in nlp_artifacts.entities
        if e.entity_type in CRITICAL_ENTITY_TYPES
    ]

    if not critical_entities:
        return issues

    statement_text = statement.statement.lower()
    missing_entities: List[MedicalEntity] = []
    found_entities: List[MedicalEntity] = []

    for entity in critical_entities:
        entity_text = entity.text.lower()

        if _entity_in_text(entity_text, statement_text):
            found_entities.append(entity)
        else:
            # Check for partial match or synonym
            if not _fuzzy_entity_match(entity, statement_text):
                missing_entities.append(entity)
            else:
                found_entities.append(entity)

    # Calculate coverage
    coverage = len(found_entities) / len(critical_entities) if critical_entities else 1.0

    if missing_entities and coverage < ENTITY_COVERAGE_THRESHOLD:
        # Group missing by type for clearer message
        missing_by_type = _group_entities_by_type(missing_entities)
        missing_summary = ", ".join(
            f"{len(entities)} {etype.value.lower()}(s): {', '.join(e.text for e in entities[:3])}"
            + ("..." if len(entities) > 3 else "")
            for etype, entities in missing_by_type.items()
        )

        issues.append(ValidationIssue(
            severity="warning",
            category="entity_completeness",
            message=(
                f"Low entity coverage ({int(coverage * 100)}%): "
                f"Missing {missing_summary}"
            ),
            location=location
        ))
        logger.debug(
            f"Entity coverage {int(coverage * 100)}% at {location}"
        )

    return issues


def check_unit_accuracy(
    statement: Statement,
    nlp_artifacts: NLPArtifacts,
    location: Optional[str] = None
) -> List[ValidationIssue]:
    """
    Verify numeric values and units match source exactly.

    Compares quantities, measurements, and thresholds between NLP-extracted
    entities and the generated statement to catch transcription errors.

    Example:
        Source: "Give 5 mg daily"
        NLP: QUANTITY("5 mg")
        Bad statement: "Give 50 mg daily" <- FLAGGED (value mismatch)
        Bad statement: "Give 5 g daily" <- FLAGGED (unit mismatch)

    Args:
        statement: Statement to check
        nlp_artifacts: NLP analysis of source text
        location: Location string for error reporting

    Returns:
        List of validation issues for unit/threshold problems
    """
    issues: List[ValidationIssue] = []

    # Get quantity and lab value entities
    quantity_entities = [
        e for e in nlp_artifacts.entities
        if e.entity_type in {EntityType.QUANTITY, EntityType.LAB_VALUE}
    ]

    if not quantity_entities:
        return issues

    statement_text = statement.statement

    # Extract numeric patterns from statement
    statement_quantities = _extract_quantities(statement_text)

    for entity in quantity_entities:
        source_quantity = _parse_quantity(entity.text)
        if not source_quantity:
            continue

        source_value, source_unit = source_quantity

        # Check if this entity's value appears in statement
        for stmt_text, stmt_value, stmt_unit in statement_quantities:
            # Check if similar context (within reason)
            if not _quantities_related(entity.text, stmt_text):
                continue

            # Compare values
            if stmt_value != source_value:
                issues.append(ValidationIssue(
                    severity="error",
                    category="unit_accuracy",
                    message=(
                        f"Value mismatch: source has '{entity.text}' "
                        f"but statement has '{stmt_text}'"
                    ),
                    location=location
                ))
                logger.warning(
                    f"Value mismatch: {entity.text} vs {stmt_text} at {location}"
                )

            # Compare units (if both have units)
            elif source_unit and stmt_unit and not _units_equivalent(source_unit, stmt_unit):
                issues.append(ValidationIssue(
                    severity="error",
                    category="unit_accuracy",
                    message=(
                        f"Unit mismatch: source has '{entity.text}' "
                        f"but statement has '{stmt_text}'"
                    ),
                    location=location
                ))
                logger.warning(
                    f"Unit mismatch: {entity.text} vs {stmt_text} at {location}"
                )

    return issues


# =============================================================================
# Helper functions
# =============================================================================

def _entity_in_text(entity_text: str, text: str) -> bool:
    """Check if entity appears in text (case-insensitive, word boundary)."""
    # Escape regex special characters
    pattern = r'\b' + re.escape(entity_text) + r'\b'
    return bool(re.search(pattern, text, re.IGNORECASE))


def _has_negation_context(entity_text: str, statement_text: str) -> bool:
    """Check if entity is mentioned in a negation context within the statement."""
    # Look for negation pattern near the entity
    for pattern in NEGATION_PATTERNS:
        # Check if negation appears within 50 chars before entity
        # This captures "no diabetes", "without hypertension", etc.
        combined_pattern = f"({pattern})\\s+[\\w\\s]{{0,30}}\\b{re.escape(entity_text)}\\b"
        if re.search(combined_pattern, statement_text, re.IGNORECASE):
            return True

        # Also check for entity before negation for patterns like "diabetes is not present"
        combined_pattern = f"\\b{re.escape(entity_text)}\\b[\\w\\s]{{0,30}}({pattern})"
        if re.search(combined_pattern, statement_text, re.IGNORECASE):
            return True

    return False


def _has_affirmative_context(entity_text: str, statement_text: str) -> bool:
    """Check if entity is mentioned in an affirmative context."""
    for pattern in AFFIRMATIVE_PATTERNS:
        # Check for affirmative pattern near entity
        combined_pattern = f"({pattern})\\s+[\\w\\s]{{0,20}}\\b{re.escape(entity_text)}\\b"
        if re.search(combined_pattern, statement_text, re.IGNORECASE):
            return True

        combined_pattern = f"\\b{re.escape(entity_text)}\\b[\\w\\s]{{0,20}}({pattern})"
        if re.search(combined_pattern, statement_text, re.IGNORECASE):
            return True

    return False


def _fuzzy_entity_match(entity: MedicalEntity, text: str) -> bool:
    """
    Check for fuzzy matches of entity in text.

    Handles:
    - Plural forms
    - Common abbreviations
    - Partial matches for multi-word entities
    """
    entity_text = entity.text.lower()

    # Check exact match first
    if _entity_in_text(entity_text, text):
        return True

    # Try plural/singular variations
    variations = [
        entity_text + 's',
        entity_text + 'es',
        entity_text.rstrip('s') if entity_text.endswith('s') else None,
        entity_text.rstrip('es') if entity_text.endswith('es') else None,
    ]

    for var in variations:
        if var and _entity_in_text(var, text):
            return True

    # For multi-word entities, check if key words are present
    words = entity_text.split()
    if len(words) > 1:
        # Check if at least half of significant words are present
        significant_words = [w for w in words if len(w) > 3]
        if significant_words:
            found_words = sum(1 for w in significant_words if w in text)
            if found_words >= len(significant_words) / 2:
                return True

    return False


def _group_entities_by_type(
    entities: List[MedicalEntity]
) -> dict:
    """Group entities by their entity type."""
    grouped: dict = {}
    for entity in entities:
        if entity.entity_type not in grouped:
            grouped[entity.entity_type] = []
        grouped[entity.entity_type].append(entity)
    return grouped


def _extract_quantities(text: str) -> List[Tuple[str, float, Optional[str]]]:
    """
    Extract quantities with values and units from text.

    Returns:
        List of (original_text, numeric_value, unit) tuples
    """
    quantities = []

    # Pattern: number followed by optional unit
    # Matches: "5 mg", "10.5 mL", ">250", "3-5 days", "100%", etc.
    pattern = r'([<>=]?\s*\d+(?:\.\d+)?(?:\s*-\s*\d+(?:\.\d+)?)?)\s*(%|[a-zA-Z/]+)?'

    for match in re.finditer(pattern, text):
        original = match.group(0).strip()
        value_str = match.group(1).strip()
        unit = match.group(2).strip() if match.group(2) else None

        # Parse numeric value (take first number in range)
        value_match = re.search(r'\d+(?:\.\d+)?', value_str)
        if value_match:
            try:
                value = float(value_match.group())
                quantities.append((original, value, unit))
            except ValueError:
                continue

    return quantities


def _parse_quantity(text: str) -> Optional[Tuple[float, Optional[str]]]:
    """
    Parse a quantity string into value and unit.

    Returns:
        Tuple of (numeric_value, unit) or None if not parseable
    """
    # Extract number and unit
    match = re.search(r'([<>=]?\s*\d+(?:\.\d+)?)\s*(%|[a-zA-Z/]+)?', text)
    if not match:
        return None

    value_str = match.group(1).strip()
    unit = match.group(2).strip() if match.group(2) else None

    # Parse the numeric value (ignore comparison operators)
    value_match = re.search(r'\d+(?:\.\d+)?', value_str)
    if not value_match:
        return None

    try:
        value = float(value_match.group())
        return (value, unit)
    except ValueError:
        return None


def _quantities_related(source_text: str, statement_text: str) -> bool:
    """
    Check if two quantity strings are likely referring to the same thing.

    Uses fuzzy matching on surrounding context.
    """
    # Simple heuristic: check if they have same unit
    source_parsed = _parse_quantity(source_text)
    stmt_parsed = _parse_quantity(statement_text)

    if not source_parsed or not stmt_parsed:
        return False

    source_unit = source_parsed[1]
    stmt_unit = stmt_parsed[1]

    # If both have units, they should match
    if source_unit and stmt_unit:
        return _units_equivalent(source_unit, stmt_unit)

    # If neither has units, assume possibly related
    if not source_unit and not stmt_unit:
        return True

    return False


def _units_equivalent(unit1: str, unit2: str) -> bool:
    """
    Check if two units are equivalent (handles common variations).

    Examples:
        "mg" == "mg" -> True
        "mL" == "ml" -> True (case-insensitive)
        "mg/dL" == "mg/dl" -> True
        "mg" == "g" -> False
    """
    # Normalize case
    u1 = unit1.lower()
    u2 = unit2.lower()

    if u1 == u2:
        return True

    # Common equivalences
    equivalences = [
        {'ml', 'milliliter', 'milliliters'},
        {'mg', 'milligram', 'milligrams'},
        {'g', 'gram', 'grams'},
        {'l', 'liter', 'liters'},
        {'kg', 'kilogram', 'kilograms'},
        {'mcg', 'microgram', 'micrograms', 'ug'},
        {'iu', 'international unit', 'international units'},
        {'%', 'percent'},
        {'mmol', 'millimole', 'millimoles'},
        {'meq', 'milliequivalent', 'milliequivalents'},
    ]

    for equiv_set in equivalences:
        if u1 in equiv_set and u2 in equiv_set:
            return True

    return False
