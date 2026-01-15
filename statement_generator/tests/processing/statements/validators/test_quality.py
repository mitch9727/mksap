"""
Comprehensive tests for quality_checks module.

Tests all quality validation functions including:
- Atomicity checks (enhanced with semicolons, multiple "and", conditionals)
- Patient-specific language detection
- Statement length checks (upgraded severity)
- Vague language detection
- Board relevance checks
"""

import pytest
from src.infrastructure.models.data_models import Statement
from src.processing.statements.validators.quality import (
    validate_statement_quality,
    check_atomicity,
    check_patient_specific_language,
    check_source_references,
    check_statement_length,
    check_vague_language,
    check_board_relevance,
)


class TestAtomicityEnhancements:
    """Test enhanced atomicity detection (Enhancement C)"""

    def test_semicolon_detection(self):
        """Semicolons always suggest compound sentences"""
        statement = "ACE inhibitors reduce blood pressure; they also reduce proteinuria."
        issues = check_atomicity(statement, "test.statement[0]")

        assert len(issues) == 1
        assert issues[0].severity == "warning"
        assert issues[0].category == "quality"
        assert "Semicolon suggests compound sentence" in issues[0].message
        assert issues[0].location == "test.statement[0]"

    def test_multiple_and_conjunctions(self):
        """Detect 3+ 'and' conjunctions"""
        statement = "ACE inhibitors reduce blood pressure and proteinuria and slow CKD progression and improve outcomes."
        issues = check_atomicity(statement, "test.statement[1]")

        assert len(issues) == 1
        assert issues[0].severity == "warning"
        assert "Multiple 'and' conjunctions (3)" in issues[0].message
        assert "suggest compound statement" in issues[0].message

    def test_two_and_conjunctions_ok(self):
        """2 'and' conjunctions should not trigger warning"""
        statement = "ACE inhibitors reduce blood pressure and proteinuria."
        issues = check_atomicity(statement, None)

        # Should not trigger multiple-and warning
        and_warning = any("Multiple 'and'" in i.message for i in issues)
        assert not and_warning

    def test_multi_clause_conditionals(self):
        """Detect complex if-then chains"""
        statement = "If patient has CKD then start ACE inhibitor and if proteinuria persists then add ARB."
        issues = check_atomicity(statement, None)

        assert len(issues) == 1
        assert issues[0].severity == "warning"
        assert "Multi-clause conditional" in issues[0].message

    def test_simple_conditional_ok(self):
        """Simple if-then should not trigger warning"""
        statement = "If patient has hypertension then start ACE inhibitor."
        issues = check_atomicity(statement, None)

        conditional_warning = any("Multi-clause conditional" in i.message for i in issues)
        assert not conditional_warning

    def test_atomicity_priority_semicolon_first(self):
        """Semicolon check should return early, preventing other checks"""
        statement = "ACE inhibitors reduce blood pressure; they also reduce proteinuria and slow CKD progression and improve outcomes."
        issues = check_atomicity(statement, None)

        # Should only get semicolon warning, not multiple-and warning
        assert len(issues) == 1
        assert "Semicolon" in issues[0].message

    def test_clean_atomic_statement(self):
        """Atomic statement with no issues"""
        statement = "ACE inhibitors reduce proteinuria in chronic kidney disease."
        issues = check_atomicity(statement, None)

        assert len(issues) == 0


class TestPatientSpecificLanguage:
    """Test patient-specific language detection (Enhancement B)"""

    def test_this_patient_detection(self):
        """Detect 'this patient' phrase"""
        statement = "This patient should receive ACE inhibitor therapy."
        issues = check_patient_specific_language(statement, "test.statement[0]")

        assert len(issues) == 1


class TestSourceReferences:
    """Test source-referential language detection"""

    def test_this_critique_detection(self):
        statement = "The most appropriate management in this critique is urgent coronary angiography."
        issues = check_source_references(statement, "test.statement[0]")

        assert len(issues) == 1
        assert issues[0].severity == "info"
        assert issues[0].category == "quality"
        assert "this critique" in issues[0].message.lower()

    def test_based_on_question_detection(self):
        statement = "Based on the question, the diagnosis is bacterial endocarditis."
        issues = check_source_references(statement, None)

        assert len(issues) == 1
        assert "the question" in issues[0].message.lower()

    def test_vignette_detection(self):
        statement = "In this vignette, urgent anticoagulation is indicated."
        issues = check_source_references(statement, None)

        assert len(issues) == 1
        assert "this vignette" in issues[0].message.lower()

    def test_this_setting_detection(self):
        statement = "In this setting, urgent coronary angiography is indicated."
        issues = check_source_references(statement, None)

        assert len(issues) == 1
        assert "this setting" in issues[0].message.lower()

    def test_clean_statement_no_source_reference(self):
        statement = "Urgent coronary angiography is indicated for high-risk NSTEMI."
        issues = check_source_references(statement, None)

        assert len(issues) == 0
        assert issues[0].severity == "info"
        assert issues[0].category == "quality"
        assert "Patient-specific language detected" in issues[0].message
        assert "this patient" in issues[0].message.lower()

    def test_this_case_detection(self):
        """Detect 'this case' phrase"""
        statement = "In this case, the diagnosis is acute coronary syndrome."
        issues = check_patient_specific_language(statement, None)

        assert len(issues) == 1
        assert "this case" in issues[0].message.lower()

    def test_the_patient_detection(self):
        """Detect 'the patient' phrase"""
        statement = "The patient requires immediate cardioversion."
        issues = check_patient_specific_language(statement, None)

        assert len(issues) == 1
        assert "the patient" in issues[0].message.lower()

    def test_multiple_patient_specific_phrases(self):
        """Detect multiple patient-specific phrases"""
        statement = "This patient should receive therapy. The patient requires monitoring."
        issues = check_patient_specific_language(statement, None)

        assert len(issues) == 1
        # Should deduplicate repeated phrases
        assert "this patient" in issues[0].message.lower()
        assert "the patient" in issues[0].message.lower()

    def test_clean_generalized_statement(self):
        """Generalized statement without patient-specific language"""
        statement = "Patients with chronic kidney disease should receive ACE inhibitors."
        issues = check_patient_specific_language(statement, None)

        assert len(issues) == 0

    def test_case_insensitive_detection(self):
        """Detection should be case-insensitive"""
        statement = "THIS PATIENT requires immediate treatment."
        issues = check_patient_specific_language(statement, None)

        assert len(issues) == 1


class TestStatementLengthSeverity:
    """Test upgraded statement length check severity (Enhancement A)"""

    def test_long_statement_warning_severity(self):
        """Statements >200 chars should be WARNING, not INFO"""
        long_statement = "A" * 201
        issue = check_statement_length(long_statement, "test.statement[0]")

        assert issue is not None
        assert issue.severity == "warning"  # Upgraded from "info"
        assert issue.category == "quality"
        assert issue.location == "test.statement[0]"

    def test_long_statement_improved_message(self):
        """Message should mention retention and review speed"""
        long_statement = "A" * 250
        issue = check_statement_length(long_statement, None)

        assert "Long statements slow reviews and reduce retention" in issue.message
        assert "(250 chars)" in issue.message

    def test_acceptable_length_no_warning(self):
        """Statements <=200 chars should not trigger warning"""
        ok_statement = "A" * 200
        issue = check_statement_length(ok_statement, None)

        assert issue is None

    def test_short_statement_no_warning(self):
        """Short statements are fine"""
        short_statement = "ACE inhibitors reduce proteinuria."
        issue = check_statement_length(short_statement, None)

        assert issue is None


class TestVagueLanguage:
    """Test vague language detection (existing functionality)"""

    def test_single_vague_term(self):
        """Detect single vague qualifier"""
        statement = "ACE inhibitors often reduce blood pressure."
        issues = check_vague_language(statement, "test.statement[0]")

        assert len(issues) == 1
        assert issues[0].severity == "info"
        assert "Vague language detected" in issues[0].message
        assert "often" in issues[0].message

    def test_multiple_vague_terms(self):
        """Detect multiple vague qualifiers"""
        statement = "ACE inhibitors usually reduce blood pressure and may improve outcomes."
        issues = check_vague_language(statement, None)

        assert len(issues) == 1
        assert "usually" in issues[0].message
        assert "may" in issues[0].message

    def test_word_boundary_matching(self):
        """Should use word boundaries to avoid false positives"""
        # "mayonnaise" contains "may" but shouldn't match
        statement = "Patients should avoid mayonnaise."
        issues = check_vague_language(statement, None)

        assert len(issues) == 0

    def test_case_insensitive_vague_detection(self):
        """Detection should be case-insensitive"""
        statement = "OFTEN patients respond to therapy."
        issues = check_vague_language(statement, None)

        assert len(issues) == 1
        assert "often" in issues[0].message.lower()

    def test_clean_precise_statement(self):
        """Precise statement without vague language"""
        statement = "ACE inhibitors reduce systolic blood pressure by 10-15 mmHg."
        issues = check_vague_language(statement, None)

        assert len(issues) == 0


class TestBoardRelevance:
    """Test board relevance checks (existing functionality)"""

    def test_pure_trivia_without_context(self):
        """Pure trivia should be flagged"""
        statement = "Diabetes was discovered in ancient Egypt."
        issue = check_board_relevance(statement, "test.statement[0]")

        assert issue is not None
        assert issue.severity == "warning"
        assert "Possible trivia without clinical context" in issue.message

    def test_trivia_with_clinical_context_ok(self):
        """Trivia with clinical context should pass"""
        statement = "Metformin is derived from French lilac and is first-line therapy for diabetes."
        issue = check_board_relevance(statement, None)

        # Should not flag because "therapy" provides clinical context
        assert issue is None

    def test_clinical_statement_ok(self):
        """Clinical statement without trivia patterns"""
        statement = "ACE inhibitors are first-line therapy for hypertension in CKD."
        issue = check_board_relevance(statement, None)

        assert issue is None

    def test_multiple_trivia_patterns(self):
        """Should detect various trivia patterns"""
        trivia_statements = [
            "Aspirin is also known as acetylsalicylic acid.",
            "The kidney is located in the retroperitoneum.",
            "Insulin was discovered by Banting and Best.",
        ]

        for stmt in trivia_statements:
            issue = check_board_relevance(stmt, None)
            assert issue is not None
            assert issue.severity == "warning"


class TestIntegration:
    """Integration tests for validate_statement_quality"""

    def test_clean_statement_no_issues(self):
        """High-quality statement should have no issues"""
        stmt = Statement(
            statement="ACE inhibitors reduce proteinuria in chronic kidney disease.",
            extra_field=None,
            cloze_candidates=["ACE inhibitors", "proteinuria", "chronic kidney disease"]
        )

        issues = validate_statement_quality(stmt, None)
        assert len(issues) == 0

    def test_multiple_quality_issues(self):
        """Statement with multiple issues should flag all"""
        stmt = Statement(
            statement="This patient often has hypertension; they also have diabetes and kidney disease and heart failure.",
            extra_field=None,
            cloze_candidates=[]
        )

        issues = validate_statement_quality(stmt, "test.statement[0]")

        # Should detect: patient-specific, vague language, semicolon
        assert len(issues) >= 3

        severities = [i.severity for i in issues]
        categories = [i.category for i in issues]

        # All should be quality issues
        assert all(c == "quality" for c in categories)

        # Should have at least one warning
        assert "warning" in severities

    def test_long_statement_with_compound_structure(self):
        """Long compound statement should trigger multiple warnings"""
        long_compound = "A" * 100 + " and this is compound; " + "B" * 100
        stmt = Statement(
            statement=long_compound,
            extra_field=None,
            cloze_candidates=[]
        )

        issues = validate_statement_quality(stmt, None)

        # Should detect: length warning + semicolon warning
        assert len(issues) >= 2

        warnings = [i for i in issues if i.severity == "warning"]
        assert len(warnings) >= 2

    def test_location_propagation(self):
        """Location should propagate to all issues"""
        stmt = Statement(
            statement="This patient often requires therapy.",
            extra_field=None,
            cloze_candidates=[]
        )

        location = "critique.statement[5]"
        issues = validate_statement_quality(stmt, location)

        # All issues should have the same location
        for issue in issues:
            assert issue.location == location

    def test_validate_statement_quality_returns_list(self):
        """validate_statement_quality should always return a list"""
        stmt = Statement(
            statement="Simple statement.",
            extra_field=None,
            cloze_candidates=[]
        )

        result = validate_statement_quality(stmt, None)
        assert isinstance(result, list)


# Run pytest with coverage if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=src.validation.quality_checks", "--cov-report=term-missing"])
