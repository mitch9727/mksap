"""
Core validation framework for statement extraction quality.

Validates JSON structure, statement quality, cloze candidates, and source fidelity.
"""

from typing import Dict, List, Optional, Literal
from pydantic import BaseModel, Field

from ..models import Statement, TableStatement


class ValidationIssue(BaseModel):
    """Single validation issue"""

    severity: Literal["error", "warning", "info"]
    category: str  # "structure", "quality", "cloze", "hallucination"
    message: str
    location: Optional[str] = None  # "critique.statement[2]"


class ValidationResult(BaseModel):
    """Result of validating a single question"""

    question_id: str
    valid: bool
    errors: List[ValidationIssue] = Field(default_factory=list)
    warnings: List[ValidationIssue] = Field(default_factory=list)
    info: List[ValidationIssue] = Field(default_factory=list)
    stats: Dict[str, int] = Field(default_factory=dict)  # counts by category


class StatementValidator:
    """Main validator for extracted statements"""

    def __init__(self):
        """Initialize validator"""
        pass

    def validate_question(self, question_data: Dict) -> ValidationResult:
        """
        Validate a complete question with extracted statements.

        Args:
            question_data: Full question JSON with true_statements field

        Returns:
            ValidationResult with all issues found
        """
        from .structure_checks import (
            validate_json_structure,
            validate_true_statements_field,
            validate_table_statements_field,
        )
        from .quality_checks import validate_statement_quality
        from .cloze_checks import validate_statement_clozes
        from .hallucination_checks import validate_statement_fidelity
        from .ambiguity_checks import validate_statement_ambiguity
        from .enumeration_checks import validate_statement_enumerations
        from ..nlp_utils import get_nlp, nlp_pipe

        question_id = question_data.get("question_id", "unknown")
        all_issues: List[ValidationIssue] = []

        # 1. Validate JSON structure
        all_issues.extend(validate_json_structure(question_data))
        all_issues.extend(validate_true_statements_field(question_data))

        # Check if table_statements exists
        if "table_statements" in question_data:
            all_issues.extend(validate_table_statements_field(question_data))

        nlp = get_nlp()

        # 2. Validate each statement from critique
        true_statements = question_data.get("true_statements", {})
        critique_text = question_data.get("critique", "")
        critique_doc = nlp(critique_text) if nlp and critique_text else None
        critique_stmt_texts = [
            stmt_data.get("statement", "")
            for stmt_data in true_statements.get("from_critique", [])
        ]
        critique_stmt_docs = nlp_pipe(critique_stmt_texts)

        for i, stmt_data in enumerate(true_statements.get("from_critique", [])):
            try:
                stmt = Statement(**stmt_data)
                location = f"critique.statement[{i}]"
                statement_doc = critique_stmt_docs[i] if i < len(critique_stmt_docs) else None

                # Quality checks
                all_issues.extend(validate_statement_quality(stmt, location))

                # Cloze checks
                all_issues.extend(validate_statement_clozes(stmt, location))

                # Ambiguity checks (NEW - Week 2)
                all_issues.extend(validate_statement_ambiguity(stmt, location, statement_doc=statement_doc))

                # Enumeration checks (NEW - Week 2)
                all_issues.extend(validate_statement_enumerations(stmt, location))

                # Hallucination checks
                all_issues.extend(
                    validate_statement_fidelity(
                        stmt,
                        critique_text,
                        location,
                        statement_doc=statement_doc,
                        source_doc=critique_doc,
                    )
                )

            except Exception as e:
                all_issues.append(ValidationIssue(
                    severity="error",
                    category="structure",
                    message=f"Failed to parse statement: {str(e)}",
                    location=f"critique.statement[{i}]"
                ))

        # 3. Validate each statement from key_points
        key_points_text = " ".join(question_data.get("key_points", []))
        key_points_doc = nlp(key_points_text) if nlp and key_points_text else None
        key_point_stmt_texts = [
            stmt_data.get("statement", "")
            for stmt_data in true_statements.get("from_key_points", [])
        ]
        key_point_stmt_docs = nlp_pipe(key_point_stmt_texts)

        for i, stmt_data in enumerate(true_statements.get("from_key_points", [])):
            try:
                stmt = Statement(**stmt_data)
                location = f"key_points.statement[{i}]"
                statement_doc = key_point_stmt_docs[i] if i < len(key_point_stmt_docs) else None

                # Quality checks
                all_issues.extend(validate_statement_quality(stmt, location))

                # Cloze checks
                all_issues.extend(validate_statement_clozes(stmt, location))

                # Ambiguity checks (NEW - Week 2)
                all_issues.extend(validate_statement_ambiguity(stmt, location, statement_doc=statement_doc))

                # Enumeration checks (NEW - Week 2)
                all_issues.extend(validate_statement_enumerations(stmt, location))

                # Hallucination checks
                all_issues.extend(
                    validate_statement_fidelity(
                        stmt,
                        key_points_text,
                        location,
                        statement_doc=statement_doc,
                        source_doc=key_points_doc,
                    )
                )

            except Exception as e:
                all_issues.append(ValidationIssue(
                    severity="error",
                    category="structure",
                    message=f"Failed to parse statement: {str(e)}",
                    location=f"key_points.statement[{i}]"
                ))

        # 4. Validate table statements if present
        table_statements = question_data.get("table_statements", {})
        table_stmt_texts = [
            stmt_data.get("statement", "")
            for stmt_data in table_statements.get("statements", [])
        ]
        table_stmt_docs = nlp_pipe(table_stmt_texts)

        for i, stmt_data in enumerate(table_statements.get("statements", [])):
            try:
                stmt = TableStatement(**stmt_data)
                location = f"table.statement[{i}]"
                statement_doc = table_stmt_docs[i] if i < len(table_stmt_docs) else None

                # Quality checks (using Statement interface)
                base_stmt = Statement(
                    statement=stmt.statement,
                    extra_field=stmt.extra_field,
                    cloze_candidates=stmt.cloze_candidates
                )
                all_issues.extend(validate_statement_quality(base_stmt, location))

                # Cloze checks
                all_issues.extend(validate_statement_clozes(base_stmt, location))

                # Ambiguity checks (NEW - Week 2)
                all_issues.extend(validate_statement_ambiguity(base_stmt, location, statement_doc=statement_doc))

                # Enumeration checks (NEW - Week 2)
                all_issues.extend(validate_statement_enumerations(base_stmt, location))

                # For tables, we don't have full source text for hallucination detection
                # Could enhance later by reading actual table HTML

            except Exception as e:
                all_issues.append(ValidationIssue(
                    severity="error",
                    category="structure",
                    message=f"Failed to parse table statement: {str(e)}",
                    location=f"table.statement[{i}]"
                ))

        # Categorize issues by severity
        errors = [i for i in all_issues if i.severity == "error"]
        warnings = [i for i in all_issues if i.severity == "warning"]
        info_issues = [i for i in all_issues if i.severity == "info"]

        # Calculate stats
        stats = {
            "total_issues": len(all_issues),
            "structure": len([i for i in all_issues if i.category == "structure"]),
            "quality": len([i for i in all_issues if i.category == "quality"]),
            "cloze": len([i for i in all_issues if i.category == "cloze"]),
            "hallucination": len([i for i in all_issues if i.category == "hallucination"]),
            "ambiguity": len([i for i in all_issues if i.category == "ambiguity"]),  # NEW - Week 2
            "enumeration": len([i for i in all_issues if i.category == "enumeration"]),  # NEW - Week 2
        }

        return ValidationResult(
            question_id=question_id,
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            info=info_issues,
            stats=stats,
        )

    def validate_statement(self, statement: Statement, source_text: str) -> List[ValidationIssue]:
        """
        Validate a single statement against source text.

        Args:
            statement: Statement to validate
            source_text: Source text (critique, key_point, or table)

        Returns:
            List of validation issues
        """
        from .quality_checks import validate_statement_quality
        from .cloze_checks import validate_statement_clozes
        from .hallucination_checks import validate_statement_fidelity
        from .ambiguity_checks import validate_statement_ambiguity
        from .enumeration_checks import validate_statement_enumerations
        from ..nlp_utils import get_nlp

        issues: List[ValidationIssue] = []
        nlp = get_nlp()
        statement_doc = nlp(statement.statement) if nlp and statement.statement else None
        source_doc = nlp(source_text) if nlp and source_text else None

        issues.extend(validate_statement_quality(statement, None))
        issues.extend(validate_statement_clozes(statement, None))
        issues.extend(validate_statement_ambiguity(statement, None, statement_doc=statement_doc))
        issues.extend(validate_statement_enumerations(statement, None))
        issues.extend(
            validate_statement_fidelity(
                statement,
                source_text,
                None,
                statement_doc=statement_doc,
                source_doc=source_doc,
            )
        )

        return issues

    def validate_cloze_candidates(self, statement: Statement) -> List[ValidationIssue]:
        """
        Validate cloze candidates for a statement.

        Args:
            statement: Statement with cloze candidates

        Returns:
            List of validation issues
        """
        from .cloze_checks import validate_statement_clozes
        return validate_statement_clozes(statement, None)
