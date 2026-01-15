"""
JSON structure validation for extracted statements.

Validates that JSON has correct fields, types, and completeness.
"""

from typing import Dict, List
from src.infrastructure.models.data_models import Statement, TableStatement
from src.validation.validator import ValidationIssue


def validate_json_structure(data: Dict) -> List[ValidationIssue]:
    """
    Validate basic JSON structure of question data.

    Args:
        data: Question JSON data

    Returns:
        List of validation issues
    """
    issues: List[ValidationIssue] = []

    # Check for essential fields from Phase 1
    required_fields = ["question_id", "category", "critique", "key_points"]
    for field in required_fields:
        if field not in data:
            issues.append(ValidationIssue(
                severity="error",
                category="structure",
                message=f"Missing required field: {field}",
                location="root"
            ))

    # Check field types
    if "question_id" in data and not isinstance(data["question_id"], str):
        issues.append(ValidationIssue(
            severity="error",
            category="structure",
            message="question_id must be a string",
            location="root.question_id"
        ))

    if "category" in data and not isinstance(data["category"], str):
        issues.append(ValidationIssue(
            severity="error",
            category="structure",
            message="category must be a string",
            location="root.category"
        ))

    if "critique" in data and not isinstance(data["critique"], str):
        issues.append(ValidationIssue(
            severity="error",
            category="structure",
            message="critique must be a string",
            location="root.critique"
        ))

    if "key_points" in data and not isinstance(data["key_points"], list):
        issues.append(ValidationIssue(
            severity="error",
            category="structure",
            message="key_points must be a list",
            location="root.key_points"
        ))

    return issues


def validate_true_statements_field(data: Dict) -> List[ValidationIssue]:
    """
    Validate true_statements field structure.

    Args:
        data: Question JSON data

    Returns:
        List of validation issues
    """
    issues: List[ValidationIssue] = []

    if "true_statements" not in data:
        issues.append(ValidationIssue(
            severity="error",
            category="structure",
            message="Missing true_statements field - question not yet processed",
            location="root.true_statements"
        ))
        return issues

    true_statements = data["true_statements"]

    if not isinstance(true_statements, dict):
        issues.append(ValidationIssue(
            severity="error",
            category="structure",
            message="true_statements must be an object/dict",
            location="root.true_statements"
        ))
        return issues

    # Check for expected sub-fields
    for field in ["from_critique", "from_key_points"]:
        if field not in true_statements:
            issues.append(ValidationIssue(
                severity="warning",
                category="structure",
                message=f"Missing {field} in true_statements",
                location=f"true_statements.{field}"
            ))
        elif not isinstance(true_statements[field], list):
            issues.append(ValidationIssue(
                severity="error",
                category="structure",
                message=f"{field} must be a list",
                location=f"true_statements.{field}"
            ))

    # Validate each statement in from_critique
    if "from_critique" in true_statements and isinstance(true_statements["from_critique"], list):
        for i, stmt_data in enumerate(true_statements["from_critique"]):
            issues.extend(validate_statement_model(stmt_data, f"critique.statement[{i}]"))

    # Validate each statement in from_key_points
    if "from_key_points" in true_statements and isinstance(true_statements["from_key_points"], list):
        for i, stmt_data in enumerate(true_statements["from_key_points"]):
            issues.extend(validate_statement_model(stmt_data, f"key_points.statement[{i}]"))

    return issues


def validate_table_statements_field(data: Dict) -> List[ValidationIssue]:
    """
    Validate table_statements field structure.

    Args:
        data: Question JSON data

    Returns:
        List of validation issues
    """
    issues: List[ValidationIssue] = []

    table_statements = data.get("table_statements")
    if not table_statements:
        return issues  # Optional field, no issue if missing

    if not isinstance(table_statements, dict):
        issues.append(ValidationIssue(
            severity="error",
            category="structure",
            message="table_statements must be an object/dict",
            location="root.table_statements"
        ))
        return issues

    # Check for expected sub-fields
    if "statements" not in table_statements:
        issues.append(ValidationIssue(
            severity="warning",
            category="structure",
            message="Missing statements in table_statements",
            location="table_statements.statements"
        ))
    elif not isinstance(table_statements["statements"], list):
        issues.append(ValidationIssue(
            severity="error",
            category="structure",
            message="statements must be a list",
            location="table_statements.statements"
        ))
    else:
        # Validate each table statement
        for i, stmt_data in enumerate(table_statements["statements"]):
            issues.extend(validate_table_statement_model(stmt_data, f"table.statement[{i}]"))

    return issues


def validate_statement_model(stmt: Dict, source: str) -> List[ValidationIssue]:
    """
    Validate a Statement model structure.

    Args:
        stmt: Statement data dict
        source: Location string (e.g., "critique.statement[0]")

    Returns:
        List of validation issues
    """
    issues: List[ValidationIssue] = []

    # Required fields
    if "statement" not in stmt:
        issues.append(ValidationIssue(
            severity="error",
            category="structure",
            message="Missing required field: statement",
            location=source
        ))
    elif not isinstance(stmt["statement"], str):
        issues.append(ValidationIssue(
            severity="error",
            category="structure",
            message="statement must be a string",
            location=source
        ))
    elif not stmt["statement"].strip():
        issues.append(ValidationIssue(
            severity="error",
            category="structure",
            message="statement cannot be empty",
            location=source
        ))

    # extra_field is optional, but must be string or null
    if "extra_field" in stmt:
        if stmt["extra_field"] is not None and not isinstance(stmt["extra_field"], str):
            issues.append(ValidationIssue(
                severity="error",
                category="structure",
                message="extra_field must be a string or null",
                location=source
            ))

    # cloze_candidates required and must be list
    if "cloze_candidates" not in stmt:
        issues.append(ValidationIssue(
            severity="error",
            category="structure",
            message="Missing required field: cloze_candidates",
            location=source
        ))
    elif not isinstance(stmt["cloze_candidates"], list):
        issues.append(ValidationIssue(
            severity="error",
            category="structure",
            message="cloze_candidates must be a list",
            location=source
        ))
    elif len(stmt["cloze_candidates"]) == 0:
        issues.append(ValidationIssue(
            severity="warning",
            category="structure",
            message="cloze_candidates is empty",
            location=source
        ))

    # Try to parse as Statement model
    try:
        Statement(**stmt)
    except Exception as e:
        issues.append(ValidationIssue(
            severity="error",
            category="structure",
            message=f"Failed to parse as Statement: {str(e)}",
            location=source
        ))

    return issues


def validate_table_statement_model(stmt: Dict, source: str) -> List[ValidationIssue]:
    """
    Validate a TableStatement model structure.

    Args:
        stmt: TableStatement data dict
        source: Location string (e.g., "table.statement[0]")

    Returns:
        List of validation issues
    """
    issues: List[ValidationIssue] = []

    # All Statement fields
    issues.extend(validate_statement_model(stmt, source))

    # Additional table_source field
    if "table_source" not in stmt:
        issues.append(ValidationIssue(
            severity="error",
            category="structure",
            message="Missing required field: table_source",
            location=source
        ))
    elif not isinstance(stmt["table_source"], str):
        issues.append(ValidationIssue(
            severity="error",
            category="structure",
            message="table_source must be a string",
            location=source
        ))
    elif not stmt["table_source"].strip():
        issues.append(ValidationIssue(
            severity="error",
            category="structure",
            message="table_source cannot be empty",
            location=source
        ))

    # Try to parse as TableStatement model
    try:
        TableStatement(**stmt)
    except Exception as e:
        issues.append(ValidationIssue(
            severity="error",
            category="structure",
            message=f"Failed to parse as TableStatement: {str(e)}",
            location=source
        ))

    return issues
