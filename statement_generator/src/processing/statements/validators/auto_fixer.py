"""
Auto-fixer module for validation errors using NLP provenance.

Automatically corrects high-confidence validation errors by leveraging
NLP artifacts from the enriched prompt context. Implements conservative
fix strategies for negation, entity, and unit-related errors.
"""

import logging
import re
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple

from ....infrastructure.models.data_models import Statement
from ....infrastructure.models.fact_candidates import EnrichedPromptContext
from ....infrastructure.models.nlp_artifacts import EntityType, MedicalEntity, NLPArtifacts
from ....validation.validator import ValidationIssue

logger = logging.getLogger(__name__)


class FixType(str, Enum):
    """Types of automatic fixes that can be applied."""

    NEGATION_INSERTED = "negation_inserted"
    """Negation trigger was inserted from source."""

    ENTITY_ADDED = "entity_added"
    """Missing entity was added with clinical context."""

    UNIT_REPLACED = "unit_replaced"
    """Unit/value was replaced with exact source text."""

    COMPARATOR_ADDED = "comparator_added"
    """Comparator (>, <, etc.) was added from source."""


@dataclass
class FixApplied:
    """Record of a fix applied to a statement.

    Provides full provenance information for transparency and audit.
    """

    fix_type: FixType
    """Type of fix applied."""

    statement_index: int
    """Index of statement in the list that was fixed."""

    original_text: str
    """Original statement text before fix."""

    fixed_text: str
    """Statement text after fix was applied."""

    source_evidence: str
    """Text from source that justified the fix."""

    source_location: str
    """Location in source (e.g., sentence index, char span)."""

    confidence: float
    """Confidence score for this fix (0.0-1.0)."""

    issue_resolved: str
    """Description of the validation issue this fix resolves."""

    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    """When the fix was applied."""

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "fix_type": self.fix_type.value,
            "statement_index": self.statement_index,
            "original_text": self.original_text,
            "fixed_text": self.fixed_text,
            "source_evidence": self.source_evidence,
            "source_location": self.source_location,
            "confidence": self.confidence,
            "issue_resolved": self.issue_resolved,
            "timestamp": self.timestamp,
        }


# Minimum confidence threshold for applying fixes
MIN_FIX_CONFIDENCE = 0.8

# Negation triggers to look for
NEGATION_TRIGGERS = {
    "no", "not", "without", "absence", "absent", "lack", "lacks",
    "lacking", "neither", "nor", "never", "none", "negative",
    "rule out", "rules out", "ruled out", "exclude", "excludes",
    "excluded", "deny", "denies", "denied", "unlikely"
}

# Unit pattern for detecting values with comparators
UNIT_PATTERN = re.compile(
    r'([<>=]{1,2})\s*(\d+(?:\.\d+)?)\s*'
    r'(mg|mcg|mL|L|dL|g|kg|mmol|mEq|IU|U|mm|cm|m|mmHg|%|beats/min|breaths/min)?'
    r'(?:/(?:dL|L|min|day|hour|hr|h|kg|m2?))?',
    re.IGNORECASE
)

# Common comparators
COMPARATORS = {"<", ">", "<=", ">=", "=", "less than", "greater than",
               "more than", "below", "above", "under", "over"}


def auto_fix_statements(
    statements: List[Statement],
    nlp_context: EnrichedPromptContext,
    issues: List[ValidationIssue],
) -> Tuple[List[Statement], List[FixApplied]]:
    """
    Automatically fix validation errors using NLP provenance.

    Attempts conservative fixes for high-confidence errors only.
    Returns both the fixed statements and a log of all fixes applied.

    Args:
        statements: List of statements to fix
        nlp_context: NLP-enriched context with source artifacts
        issues: List of validation issues to attempt to fix

    Returns:
        Tuple of (fixed_statements, fixes_applied)
        - fixed_statements: Copy of statements with fixes applied
        - fixes_applied: Log of all fixes for transparency
    """
    if not statements or not issues:
        return statements, []

    # Create deep copy to avoid modifying originals
    fixed_statements = [deepcopy(stmt) for stmt in statements]
    fixes_applied: List[FixApplied] = []

    # Group issues by statement index
    issues_by_statement = _group_issues_by_statement(issues)

    # Get NLP artifacts
    nlp_artifacts = nlp_context.nlp_artifacts

    for stmt_idx, stmt_issues in issues_by_statement.items():
        if stmt_idx >= len(fixed_statements):
            logger.warning(f"Statement index {stmt_idx} out of range, skipping")
            continue

        statement = fixed_statements[stmt_idx]

        for issue in stmt_issues:
            fix = _attempt_fix(
                statement=statement,
                statement_index=stmt_idx,
                issue=issue,
                nlp_artifacts=nlp_artifacts,
                source_text=nlp_context.source_text,
            )

            if fix:
                # Apply the fix
                statement.statement = fix.fixed_text
                fixes_applied.append(fix)
                logger.info(
                    f"Applied {fix.fix_type.value} fix to statement {stmt_idx}: "
                    f"'{fix.original_text[:50]}...' -> '{fix.fixed_text[:50]}...'"
                )

    return fixed_statements, fixes_applied


def _group_issues_by_statement(issues: List[ValidationIssue]) -> Dict[int, List[ValidationIssue]]:
    """Group validation issues by statement index.

    Extracts statement index from location field (e.g., "critique.statement[2]").
    """
    grouped: Dict[int, List[ValidationIssue]] = {}

    for issue in issues:
        if not issue.location:
            continue

        # Extract index from location like "critique.statement[2]"
        match = re.search(r'statement\[(\d+)\]', issue.location)
        if match:
            idx = int(match.group(1))
            if idx not in grouped:
                grouped[idx] = []
            grouped[idx].append(issue)

    return grouped


def _attempt_fix(
    statement: Statement,
    statement_index: int,
    issue: ValidationIssue,
    nlp_artifacts: NLPArtifacts,
    source_text: str,
) -> Optional[FixApplied]:
    """Attempt to fix a single validation issue.

    Routes to appropriate fix strategy based on issue category.
    Returns None if fix cannot be applied with high confidence.
    """
    # Route to appropriate fixer based on issue category and message
    if issue.category == "hallucination" or issue.category == "fidelity":
        # Check for negation-related issues
        if _is_negation_issue(issue):
            return _fix_negation_error(
                statement, statement_index, issue, nlp_artifacts, source_text
            )

        # Check for entity-related issues
        if _is_entity_issue(issue):
            return _fix_missing_entity(
                statement, statement_index, issue, nlp_artifacts, source_text
            )

        # Check for unit-related issues
        if _is_unit_issue(issue):
            return _fix_unit_mismatch(
                statement, statement_index, issue, nlp_artifacts, source_text
            )

    elif issue.category == "negation":
        return _fix_negation_error(
            statement, statement_index, issue, nlp_artifacts, source_text
        )

    elif issue.category == "entity_completeness":
        return _fix_missing_entity(
            statement, statement_index, issue, nlp_artifacts, source_text
        )

    elif issue.category == "unit_mismatch":
        return _fix_unit_mismatch(
            statement, statement_index, issue, nlp_artifacts, source_text
        )

    return None


def _is_negation_issue(issue: ValidationIssue) -> bool:
    """Check if issue is related to missing negation."""
    negation_keywords = ["negat", "absence", "without", "no ", "not "]
    message_lower = issue.message.lower()
    return any(kw in message_lower for kw in negation_keywords)


def _is_entity_issue(issue: ValidationIssue) -> bool:
    """Check if issue is related to missing entities."""
    entity_keywords = ["entity", "missing", "term", "not in source"]
    message_lower = issue.message.lower()
    return any(kw in message_lower for kw in entity_keywords)


def _is_unit_issue(issue: ValidationIssue) -> bool:
    """Check if issue is related to unit/value mismatches."""
    unit_keywords = ["unit", "value", "number", "measurement", ">", "<", "mg", "ml"]
    message_lower = issue.message.lower()
    return any(kw in message_lower for kw in unit_keywords)


# =============================================================================
# NEGATION FIX STRATEGY
# =============================================================================

def _fix_negation_error(
    statement: Statement,
    statement_index: int,
    issue: ValidationIssue,
    nlp_artifacts: NLPArtifacts,
    source_text: str,
) -> Optional[FixApplied]:
    """
    Fix negation error by inserting negation trigger from source.

    Strategy:
    1. Find negated entities in NLP artifacts that relate to this statement
    2. If statement is missing the negation, insert the trigger
    3. Only fix if we have high confidence from NLP provenance
    """
    statement_text = statement.statement.lower()

    # Check if statement already has negation
    if _has_negation(statement_text):
        return None

    # Find relevant negated entities from NLP artifacts
    negated_entities = nlp_artifacts.get_negated_entities()

    if not negated_entities:
        # No NLP provenance for negation - try pattern matching on source
        return _fix_negation_from_patterns(
            statement, statement_index, issue, source_text
        )

    # Find negated entity that appears in statement (without negation)
    for entity in negated_entities:
        entity_text_lower = entity.text.lower()

        # Check if entity text appears in statement
        if entity_text_lower in statement_text:
            # This entity should be negated but statement doesn't negate it
            trigger = entity.negation_trigger or "no"

            # Build fix by inserting negation
            fixed_text = _insert_negation(
                statement.statement,
                entity.text,
                trigger
            )

            if fixed_text and fixed_text != statement.statement:
                return FixApplied(
                    fix_type=FixType.NEGATION_INSERTED,
                    statement_index=statement_index,
                    original_text=statement.statement,
                    fixed_text=fixed_text,
                    source_evidence=f"'{entity.text}' negated by '{trigger}' in source",
                    source_location=f"sentence {entity.sentence_index}, chars {entity.start_char}-{entity.end_char}",
                    confidence=entity.confidence * 0.9,  # Slightly reduce for fix uncertainty
                    issue_resolved=issue.message,
                )

    return None


def _fix_negation_from_patterns(
    statement: Statement,
    statement_index: int,
    issue: ValidationIssue,
    source_text: str,
) -> Optional[FixApplied]:
    """
    Fix negation using pattern matching when NLP artifacts aren't available.

    Looks for explicit negation patterns in source that should appear in statement.
    """
    source_lower = source_text.lower()
    statement_lower = statement.statement.lower()

    # Find negation patterns in source
    for trigger in NEGATION_TRIGGERS:
        # Look for "no X" or "without X" patterns
        pattern = rf'\b{re.escape(trigger)}\s+(\w+(?:\s+\w+)?)'
        matches = re.finditer(pattern, source_lower)

        for match in matches:
            negated_term = match.group(1)

            # Check if this term is in statement without negation
            if negated_term in statement_lower and trigger not in statement_lower:
                # High confidence only if exact phrase match
                if f"{trigger} {negated_term}" in source_lower:
                    fixed_text = _insert_negation(
                        statement.statement,
                        negated_term,
                        trigger
                    )

                    if fixed_text and fixed_text != statement.statement:
                        return FixApplied(
                            fix_type=FixType.NEGATION_INSERTED,
                            statement_index=statement_index,
                            original_text=statement.statement,
                            fixed_text=fixed_text,
                            source_evidence=f"Source contains '{trigger} {negated_term}'",
                            source_location=f"chars {match.start()}-{match.end()}",
                            confidence=0.85,  # Pattern-based fix
                            issue_resolved=issue.message,
                        )

    return None


def _has_negation(text: str) -> bool:
    """Check if text already contains negation."""
    text_lower = text.lower()
    for trigger in NEGATION_TRIGGERS:
        if re.search(rf'\b{re.escape(trigger)}\b', text_lower):
            return True
    return False


def _insert_negation(statement: str, target_term: str, trigger: str) -> Optional[str]:
    """
    Insert negation trigger before target term in statement.

    Handles different grammatical structures intelligently.
    """
    statement_lower = statement.lower()
    target_lower = target_term.lower()

    # Find the target term position (case-insensitive)
    match = re.search(rf'\b{re.escape(target_lower)}\b', statement_lower)
    if not match:
        return None

    start_pos = match.start()

    # Get the actual text at that position (preserving case)
    actual_target = statement[start_pos:start_pos + len(target_term)]

    # Check what comes before the target
    prefix = statement[:start_pos].rstrip()
    suffix = statement[start_pos:]

    # Handle common patterns
    if prefix.endswith((" is", " are", " was", " were", " has", " have")):
        # "X is present" -> "X is not present" or "there is no X"
        if trigger in ("not", "no"):
            return f"{prefix} {trigger} {suffix}"
        else:
            # "without", "absence of" etc.
            return f"{prefix.rsplit(' ', 1)[0]} has {trigger} {suffix}"

    elif prefix.endswith((" with", " shows", " demonstrates", " reveals")):
        # "patient with X" -> "patient without X"
        if trigger == "without":
            base = prefix.rsplit(' ', 1)[0]
            return f"{base} without {suffix}"
        else:
            return f"{prefix} {trigger} {suffix}"

    else:
        # Default: insert trigger before target
        # Make sure we don't double-space
        space = " " if prefix and not prefix.endswith(" ") else ""
        return f"{prefix}{space}{trigger} {suffix}"


# =============================================================================
# ENTITY FIX STRATEGY
# =============================================================================

def _fix_missing_entity(
    statement: Statement,
    statement_index: int,
    issue: ValidationIssue,
    nlp_artifacts: NLPArtifacts,
    source_text: str,
) -> Optional[FixApplied]:
    """
    Fix missing entity by adding it with clinical context from NLP artifacts.

    Strategy:
    1. Parse issue message to find what entity is missing
    2. Find entity in NLP artifacts
    3. Add entity with appropriate clinical context
    4. Only fix if we can preserve meaning and have high confidence
    """
    # Try to extract missing term from issue message
    missing_term = _extract_missing_term_from_issue(issue)

    if not missing_term:
        return None

    # Find this entity in NLP artifacts
    matching_entity = _find_entity_in_artifacts(missing_term, nlp_artifacts)

    if matching_entity:
        return _add_entity_from_nlp(
            statement, statement_index, issue, matching_entity, nlp_artifacts
        )

    # Fall back to source text matching
    return _add_entity_from_source(
        statement, statement_index, issue, missing_term, source_text
    )


def _extract_missing_term_from_issue(issue: ValidationIssue) -> Optional[str]:
    """Extract the missing term from an issue message."""
    message = issue.message

    # Pattern: "... not in source: term1, term2"
    match = re.search(r'not in source:\s*([^,]+)', message)
    if match:
        return match.group(1).strip()

    # Pattern: "missing term: X" or "missing entity: X"
    match = re.search(r'missing (?:term|entity):\s*(\w+)', message, re.IGNORECASE)
    if match:
        return match.group(1).strip()

    # Pattern: "'term' not found"
    match = re.search(r"'([^']+)'\s*not found", message)
    if match:
        return match.group(1).strip()

    return None


def _find_entity_in_artifacts(
    term: str,
    nlp_artifacts: NLPArtifacts,
) -> Optional[MedicalEntity]:
    """Find an entity in NLP artifacts that matches the given term."""
    term_lower = term.lower()

    for entity in nlp_artifacts.entities:
        if entity.text.lower() == term_lower:
            return entity
        # Also check for partial matches
        if term_lower in entity.text.lower() or entity.text.lower() in term_lower:
            return entity

    return None


def _add_entity_from_nlp(
    statement: Statement,
    statement_index: int,
    issue: ValidationIssue,
    entity: MedicalEntity,
    nlp_artifacts: NLPArtifacts,
) -> Optional[FixApplied]:
    """Add entity to statement using NLP artifact information."""
    # Get clinical context from the sentence containing the entity
    sentence = None
    for sent in nlp_artifacts.sentences:
        if sent.index == entity.sentence_index:
            sentence = sent
            break

    if not sentence:
        return None

    # Build the enhanced text
    entity_text = entity.text
    modifiers = " ".join(entity.modifiers) if entity.modifiers else ""

    # Construct addition based on entity type
    if entity.entity_type in (EntityType.MEDICATION, EntityType.CHEMICAL):
        addition = f" ({modifiers} {entity_text})".strip() if modifiers else f" ({entity_text})"
    elif entity.entity_type == EntityType.LAB_VALUE:
        addition = f" with {entity_text}"
    else:
        addition = f", {modifiers} {entity_text}".strip() if modifiers else f", {entity_text}"

    # Add to statement at appropriate location
    fixed_text = _insert_entity_intelligently(statement.statement, addition, entity.entity_type)

    if fixed_text and fixed_text != statement.statement:
        return FixApplied(
            fix_type=FixType.ENTITY_ADDED,
            statement_index=statement_index,
            original_text=statement.statement,
            fixed_text=fixed_text,
            source_evidence=f"Entity '{entity.text}' ({entity.entity_type.value}) from source",
            source_location=f"sentence {entity.sentence_index}, chars {entity.start_char}-{entity.end_char}",
            confidence=entity.confidence * 0.85,
            issue_resolved=issue.message,
        )

    return None


def _add_entity_from_source(
    statement: Statement,
    statement_index: int,
    issue: ValidationIssue,
    missing_term: str,
    source_text: str,
) -> Optional[FixApplied]:
    """Add entity using direct source text matching."""
    source_lower = source_text.lower()
    term_lower = missing_term.lower()

    # Find the term in source with context
    match = re.search(rf'(\b\w+\s+)?{re.escape(term_lower)}(\s+\w+\b)?', source_lower)

    if not match:
        return None

    # Get the full context phrase from source
    context_phrase = source_text[match.start():match.end()].strip()

    # Only proceed if we have good context
    if len(context_phrase) < len(missing_term) + 3:
        return None

    # Add as parenthetical clarification
    fixed_text = f"{statement.statement.rstrip('.')} ({context_phrase})."

    return FixApplied(
        fix_type=FixType.ENTITY_ADDED,
        statement_index=statement_index,
        original_text=statement.statement,
        fixed_text=fixed_text,
        source_evidence=f"Term '{context_phrase}' found in source",
        source_location=f"chars {match.start()}-{match.end()}",
        confidence=0.75,  # Lower confidence for pattern-based
        issue_resolved=issue.message,
    )


def _insert_entity_intelligently(
    statement: str,
    addition: str,
    entity_type: EntityType,
) -> str:
    """Insert entity addition at an appropriate location in the statement."""
    # Remove trailing period for insertion
    base = statement.rstrip('.')

    if entity_type == EntityType.LAB_VALUE:
        # Lab values typically go at the end
        return f"{base}{addition}."

    elif entity_type in (EntityType.MEDICATION, EntityType.CHEMICAL):
        # Medications can be parenthetical
        return f"{base}{addition}."

    elif entity_type == EntityType.DISEASE:
        # Diseases might need more context
        return f"{base}{addition}."

    else:
        # Default: append
        return f"{base}{addition}."


# =============================================================================
# UNIT FIX STRATEGY
# =============================================================================

def _fix_unit_mismatch(
    statement: Statement,
    statement_index: int,
    issue: ValidationIssue,
    nlp_artifacts: NLPArtifacts,
    source_text: str,
) -> Optional[FixApplied]:
    """
    Fix unit mismatch by replacing with exact source text including comparators.

    Strategy:
    1. Find numeric values in both statement and source
    2. Match values and detect comparator differences
    3. Replace statement value with exact source representation
    4. High confidence only for exact matches
    """
    statement_text = statement.statement

    # Extract values from statement and source
    statement_values = _extract_numeric_values(statement_text)
    source_values = _extract_numeric_values(source_text)

    if not statement_values or not source_values:
        return None

    # Try to match and fix each value
    for stmt_val in statement_values:
        for src_val in source_values:
            fix = _try_value_fix(
                statement=statement,
                statement_index=statement_index,
                issue=issue,
                stmt_value=stmt_val,
                src_value=src_val,
                source_text=source_text,
            )
            if fix:
                return fix

    return None


def _extract_numeric_values(text: str) -> List[Dict]:
    """Extract numeric values with their context from text."""
    values = []

    # Find values with comparators and units
    for match in UNIT_PATTERN.finditer(text):
        comparator = match.group(1) or ""
        number = match.group(2)
        unit = match.group(3) or ""
        full_match = match.group(0)

        values.append({
            "comparator": comparator,
            "number": number,
            "unit": unit,
            "full_text": full_match,
            "start": match.start(),
            "end": match.end(),
        })

    # Also find simple numbers with context
    simple_pattern = re.compile(r'(\d+(?:\.\d+)?)\s*(mg|mcg|mL|L|dL|g|kg|%|mmHg)?', re.IGNORECASE)
    for match in simple_pattern.finditer(text):
        # Skip if already captured by UNIT_PATTERN
        already_captured = any(
            v["start"] <= match.start() < v["end"]
            for v in values
        )
        if not already_captured:
            values.append({
                "comparator": "",
                "number": match.group(1),
                "unit": match.group(2) or "",
                "full_text": match.group(0),
                "start": match.start(),
                "end": match.end(),
            })

    return values


def _try_value_fix(
    statement: Statement,
    statement_index: int,
    issue: ValidationIssue,
    stmt_value: Dict,
    src_value: Dict,
    source_text: str,
) -> Optional[FixApplied]:
    """Try to fix a specific value mismatch."""
    # Check if numbers match (or are close)
    stmt_num = float(stmt_value["number"])
    src_num = float(src_value["number"])

    # Numbers must match for high confidence
    if stmt_num != src_num:
        return None

    # Check for comparator differences
    stmt_comp = stmt_value["comparator"]
    src_comp = src_value["comparator"]

    # If source has comparator but statement doesn't, add it
    if src_comp and not stmt_comp:
        fixed_text = statement.statement.replace(
            stmt_value["full_text"],
            src_value["full_text"]
        )

        if fixed_text != statement.statement:
            return FixApplied(
                fix_type=FixType.COMPARATOR_ADDED,
                statement_index=statement_index,
                original_text=statement.statement,
                fixed_text=fixed_text,
                source_evidence=f"Source uses '{src_value['full_text']}' with comparator",
                source_location=f"chars {src_value['start']}-{src_value['end']}",
                confidence=0.9,
                issue_resolved=issue.message,
            )

    # Check for unit differences
    stmt_unit = stmt_value["unit"].lower() if stmt_value["unit"] else ""
    src_unit = src_value["unit"].lower() if src_value["unit"] else ""

    if stmt_unit != src_unit and src_unit:
        fixed_text = statement.statement.replace(
            stmt_value["full_text"],
            src_value["full_text"]
        )

        if fixed_text != statement.statement:
            return FixApplied(
                fix_type=FixType.UNIT_REPLACED,
                statement_index=statement_index,
                original_text=statement.statement,
                fixed_text=fixed_text,
                source_evidence=f"Source uses '{src_value['full_text']}' (unit: {src_unit})",
                source_location=f"chars {src_value['start']}-{src_value['end']}",
                confidence=0.85,
                issue_resolved=issue.message,
            )

    return None


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def filter_high_confidence_fixes(
    fixes: List[FixApplied],
    min_confidence: float = MIN_FIX_CONFIDENCE,
) -> List[FixApplied]:
    """Filter fixes to only include high-confidence ones."""
    return [f for f in fixes if f.confidence >= min_confidence]


def summarize_fixes(fixes: List[FixApplied]) -> str:
    """Generate a human-readable summary of fixes applied."""
    if not fixes:
        return "No fixes applied."

    lines = [f"Applied {len(fixes)} fix(es):"]

    # Group by fix type
    by_type: Dict[FixType, List[FixApplied]] = {}
    for fix in fixes:
        if fix.fix_type not in by_type:
            by_type[fix.fix_type] = []
        by_type[fix.fix_type].append(fix)

    for fix_type, type_fixes in by_type.items():
        lines.append(f"\n{fix_type.value} ({len(type_fixes)}):")
        for fix in type_fixes:
            lines.append(f"  - Statement {fix.statement_index}: {fix.source_evidence}")
            lines.append(f"    Confidence: {fix.confidence:.2f}")

    return "\n".join(lines)


def validate_fix_safety(fix: FixApplied) -> Tuple[bool, Optional[str]]:
    """
    Validate that a fix is safe to apply.

    Returns:
        Tuple of (is_safe, reason_if_unsafe)
    """
    # Check that fix doesn't dramatically change meaning
    original_words = set(fix.original_text.lower().split())
    fixed_words = set(fix.fixed_text.lower().split())

    # Calculate word overlap
    common_words = original_words & fixed_words
    overlap_ratio = len(common_words) / max(len(original_words), 1)

    if overlap_ratio < 0.5:
        return False, f"Fix changes too much text (only {overlap_ratio:.0%} overlap)"

    # Check for reasonable length change
    length_ratio = len(fix.fixed_text) / max(len(fix.original_text), 1)
    if length_ratio > 2.0:
        return False, f"Fix more than doubles text length ({length_ratio:.1f}x)"

    if length_ratio < 0.5:
        return False, f"Fix removes too much text ({length_ratio:.1f}x)"

    # Check confidence threshold
    if fix.confidence < MIN_FIX_CONFIDENCE:
        return False, f"Confidence {fix.confidence:.2f} below threshold {MIN_FIX_CONFIDENCE}"

    return True, None


def apply_fixes_safely(
    statements: List[Statement],
    fixes: List[FixApplied],
) -> Tuple[List[Statement], List[FixApplied], List[Tuple[FixApplied, str]]]:
    """
    Apply fixes with safety validation.

    Returns:
        Tuple of (modified_statements, applied_fixes, rejected_fixes_with_reasons)
    """
    modified = [deepcopy(stmt) for stmt in statements]
    applied: List[FixApplied] = []
    rejected: List[Tuple[FixApplied, str]] = []

    for fix in fixes:
        is_safe, reason = validate_fix_safety(fix)

        if is_safe:
            if fix.statement_index < len(modified):
                modified[fix.statement_index].statement = fix.fixed_text
                applied.append(fix)
                logger.info(f"Safely applied fix: {fix.fix_type.value}")
        else:
            rejected.append((fix, reason or "Unknown safety concern"))
            logger.warning(f"Rejected unsafe fix: {reason}")

    return modified, applied, rejected
