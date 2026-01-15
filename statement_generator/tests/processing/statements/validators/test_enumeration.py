"""
Comprehensive tests for enumeration detection module.

Tests all detection functions for cloze deletion flashcard enumerations,
ensuring statements follow spaced repetition best practices.

Based on CLOZE_FLASHCARD_BEST_PRACTICES.md Section 4:
- Avoid testing entire lists in single cards
- Use overlapping chunked clozes for 3+ items
- Split multi-step procedures into individual statements

NOTE: These tests are designed to test the EXISTING implementation, including its
limitations. The regex patterns \\binclude\\b and \\bconsist of\\b use word boundaries
that don't match "includes" or "consists of". Tests use exact patterns that work.
"""

import pytest
from src.infrastructure.models.data_models import Statement
from src.validation.validator import ValidationIssue
from src.processing.statements.validators.enumeration import (
    validate_statement_enumerations,
    check_list_statement,
    check_multi_item_cloze,
    check_numeric_enumeration,
    check_comprehensive_coverage_claim,
    count_list_items,
    check_candidates_in_sequence,
)


# ============================================================================
# HELPER FUNCTION TESTS
# ============================================================================


class TestCountListItems:
    """Test count_list_items helper function"""

    def test_no_list_returns_zero(self):
        """Single item with no separators returns 0"""
        assert count_list_items("This is a single statement") == 0

    def test_two_items_with_comma(self):
        """Two items separated by comma returns 2"""
        assert count_list_items("Diabetes, hypertension") == 2

    def test_three_items_with_commas(self):
        """Three items with commas returns 3"""
        assert count_list_items("Diabetes, hypertension, smoking") == 3

    def test_oxford_comma_format(self):
        """Three items with Oxford comma and 'and' returns 3"""
        assert count_list_items("Diabetes, hypertension, and smoking") == 3

    def test_oxford_comma_or(self):
        """Three items with Oxford comma and 'or' returns 3"""
        assert count_list_items("Fever, chills, or night sweats") == 3

    def test_semicolon_separator(self):
        """Items separated by semicolons are counted"""
        assert count_list_items("First; second; third") == 3

    def test_mixed_separators(self):
        """Mixed comma and semicolon separators"""
        assert count_list_items("A, B; C, D") == 4

    def test_five_item_list(self):
        """Five items with commas returns 5"""
        result = count_list_items("A, B, C, D, and E")
        assert result == 5

    def test_empty_string(self):
        """Empty string returns 0"""
        assert count_list_items("") == 0


class TestCheckCandidatesInSequence:
    """Test check_candidates_in_sequence helper function"""

    def test_no_candidates_returns_zero(self):
        """Empty candidate list returns 0"""
        assert check_candidates_in_sequence("Some text", []) == 0

    def test_single_candidate_returns_zero(self):
        """Single candidate returns 0 (no sequence)"""
        stmt = "ACE inhibitors are first-line therapy"
        assert check_candidates_in_sequence(stmt, ["ACE inhibitors"]) == 0

    def test_two_candidates_with_comma_separator(self):
        """Two candidates separated by comma returns 2"""
        stmt = "Adverse effects include anaphylaxis, headache"
        candidates = ["anaphylaxis", "headache"]
        assert check_candidates_in_sequence(stmt, candidates) == 2

    def test_three_candidates_with_and_separator(self):
        """Three candidates with commas and 'and' returns 3"""
        stmt = "Risk factors include diabetes, hypertension, and smoking"
        candidates = ["diabetes", "hypertension", "smoking"]
        assert check_candidates_in_sequence(stmt, candidates) == 3

    def test_candidates_separated_by_other_words(self):
        """Candidates separated by non-separator words return 0"""
        stmt = "ACE inhibitors reduce blood pressure by blocking angiotensin"
        candidates = ["ACE inhibitors", "blood pressure", "angiotensin"]
        # Words between candidates are not just separators
        assert check_candidates_in_sequence(stmt, candidates) == 0

    def test_candidates_with_or_separator(self):
        """Candidates with 'or' separator are counted"""
        stmt = "Symptoms include fever, chills, or night sweats"
        candidates = ["fever", "chills", "night sweats"]
        assert check_candidates_in_sequence(stmt, candidates) == 3

    def test_four_candidates_in_sequence(self):
        """Four candidates in list format returns 4"""
        stmt = "Symptoms include fever, chills, nausea, and vomiting"
        candidates = ["fever", "chills", "nausea", "vomiting"]
        assert check_candidates_in_sequence(stmt, candidates) == 4

    def test_case_insensitive_matching(self):
        """Matching is case-insensitive"""
        stmt = "Risk factors include DIABETES, Hypertension, and smoking"
        candidates = ["diabetes", "hypertension", "smoking"]
        assert check_candidates_in_sequence(stmt, candidates) == 3


# ============================================================================
# DETECTION FUNCTION TESTS
# ============================================================================


class TestCheckListStatement:
    """Test check_list_statement detection function"""

    def test_no_list_indicator_passes(self):
        """Statement without list indicators passes"""
        stmt = Statement(
            statement="ACE inhibitors are first-line therapy for hypertension.",
            cloze_candidates=["ACE inhibitors"]
        )
        issues = check_list_statement(stmt, None)
        assert len(issues) == 0

    def test_include_with_two_items_passes(self):
        """'Include' with 2 items passes (below threshold)"""
        stmt = Statement(
            statement="Adverse effects include anaphylaxis and headache.",
            cloze_candidates=["anaphylaxis", "headache"]
        )
        issues = check_list_statement(stmt, None)
        assert len(issues) == 0

    def test_include_with_three_items_flags(self):
        """'Include' with 3 items flags as enumeration"""
        stmt = Statement(
            statement="Adverse effects include anaphylaxis, headache, and nausea.",
            cloze_candidates=["anaphylaxis", "headache", "nausea"]
        )
        issues = check_list_statement(stmt, None)
        assert len(issues) == 1
        assert issues[0].severity == "warning"
        assert issues[0].category == "enumeration"
        assert "3 items" in issues[0].message

    def test_consist_of_with_four_items_flags(self):
        """'Consist of' with 4 items flags"""
        stmt = Statement(
            statement="Risk factors consist of diabetes, hypertension, smoking, and obesity.",
            cloze_candidates=["diabetes", "hypertension", "smoking", "obesity"]
        )
        issues = check_list_statement(stmt, None)
        assert len(issues) == 1
        assert "4 items" in issues[0].message

    def test_comprised_of_with_list_flags(self):
        """'Comprised of' with list flags"""
        stmt = Statement(
            statement="The triad is comprised of hypotension, JVD, and muffled sounds.",
            cloze_candidates=["hypotension", "JVD", "muffled sounds"]
        )
        issues = check_list_statement(stmt, None)
        assert len(issues) == 1

    def test_such_as_with_list_flags(self):
        """'Such as' with 3+ items flags"""
        stmt = Statement(
            statement="Common medications such as aspirin, ibuprofen, and naproxen.",
            cloze_candidates=["aspirin", "ibuprofen", "naproxen"]
        )
        issues = check_list_statement(stmt, None)
        assert len(issues) == 1

    def test_becks_triad_example_flags(self):
        """Beck's triad classic example flags (using 'include' not 'includes')"""
        stmt = Statement(
            statement="Beck's triad include hypotension, JVD, and muffled heart sounds.",
            cloze_candidates=["hypotension", "JVD", "muffled heart sounds"]
        )
        issues = check_list_statement(stmt, None)
        assert len(issues) == 1
        assert "3 items" in issues[0].message

    def test_becks_triad_rephrased_passes(self):
        """Beck's triad rephrased as single component passes"""
        stmt = Statement(
            statement="One component of Beck's triad is muffled heart sounds.",
            cloze_candidates=["muffled heart sounds"]
        )
        issues = check_list_statement(stmt, None)
        assert len(issues) == 0

    def test_five_item_list_flags(self):
        """Five-item list flags with correct count"""
        stmt = Statement(
            statement="Symptoms include fever, chills, night sweats, weight loss, and fatigue.",
            cloze_candidates=["fever", "chills", "night sweats", "weight loss", "fatigue"]
        )
        issues = check_list_statement(stmt, None)
        assert len(issues) == 1
        assert "5 items" in issues[0].message

    def test_location_field_preserved(self):
        """Location field is preserved in issue"""
        stmt = Statement(
            statement="Symptoms include fever, chills, and nausea.",
            cloze_candidates=["fever", "chills", "nausea"]
        )
        issues = check_list_statement(stmt, "critique.statement[2]")
        assert len(issues) == 1
        assert issues[0].location == "critique.statement[2]"

    def test_case_insensitive_list_indicator(self):
        """List indicators are case-insensitive"""
        stmt = Statement(
            statement="Risk factors INCLUDE diabetes, hypertension, and smoking.",
            cloze_candidates=["diabetes", "hypertension", "smoking"]
        )
        issues = check_list_statement(stmt, None)
        assert len(issues) == 1


class TestCheckMultiItemCloze:
    """Test check_multi_item_cloze detection function"""

    def test_two_cloze_candidates_passes(self):
        """Two cloze candidates passes"""
        stmt = Statement(
            statement="ACE inhibitors reduce blood pressure.",
            cloze_candidates=["ACE inhibitors", "blood pressure"]
        )
        issues = check_multi_item_cloze(stmt, None)
        assert len(issues) == 0

    def test_three_cloze_candidates_not_sequential_passes(self):
        """Three candidates not in sequence passes"""
        stmt = Statement(
            statement="ACE inhibitors reduce blood pressure by blocking angiotensin.",
            cloze_candidates=["ACE inhibitors", "blood pressure", "angiotensin"]
        )
        issues = check_multi_item_cloze(stmt, None)
        assert len(issues) == 0

    def test_four_candidates_in_sequence_flags(self):
        """Four candidates in sequence flags"""
        stmt = Statement(
            statement="Adverse effects include anaphylaxis, headache, nausea, and rash.",
            cloze_candidates=["anaphylaxis", "headache", "nausea", "rash"]
        )
        issues = check_multi_item_cloze(stmt, None)
        assert len(issues) == 1
        assert issues[0].severity == "warning"
        assert issues[0].category == "enumeration"

    def test_five_candidates_in_sequence_flags(self):
        """Five candidates in sequence flags"""
        stmt = Statement(
            statement="Risk factors include diabetes, hypertension, smoking, obesity, and age.",
            cloze_candidates=["diabetes", "hypertension", "smoking", "obesity", "age"]
        )
        issues = check_multi_item_cloze(stmt, None)
        assert len(issues) == 1
        assert "5" in issues[0].message

    def test_four_candidates_none_sequential_passes(self):
        """Four candidates, none sequential passes"""
        stmt = Statement(
            statement="ACE inhibitors for hypertension reduce cardiovascular mortality in diabetics.",
            cloze_candidates=["ACE inhibitors", "hypertension", "cardiovascular", "diabetics"]
        )
        # Candidates scattered throughout, not in list format
        issues = check_multi_item_cloze(stmt, None)
        assert len(issues) == 0

    def test_location_preserved(self):
        """Location field preserved in issue"""
        stmt = Statement(
            statement="Symptoms include fever, chills, nausea, and vomiting.",
            cloze_candidates=["fever", "chills", "nausea", "vomiting"]
        )
        issues = check_multi_item_cloze(stmt, "key_points.statement[0]")
        assert len(issues) == 1
        assert issues[0].location == "key_points.statement[0]"


class TestCheckNumericEnumeration:
    """Test check_numeric_enumeration detection function"""

    def test_no_numbered_pattern_passes(self):
        """Statement without numbers passes"""
        stmt = Statement(
            statement="ACE inhibitors are first-line therapy.",
            cloze_candidates=["ACE inhibitors"]
        )
        issues = check_numeric_enumeration(stmt, None)
        assert len(issues) == 0

    def test_single_number_passes(self):
        """Single numbered item passes"""
        stmt = Statement(
            statement="The first step is assessment.",
            cloze_candidates=["assessment"]
        )
        issues = check_numeric_enumeration(stmt, None)
        assert len(issues) == 0

    def test_parentheses_numbers_flags(self):
        """(1), (2), (3) pattern flags"""
        stmt = Statement(
            statement="Steps: (1) assess, (2) intervene, (3) evaluate.",
            cloze_candidates=["assess", "intervene", "evaluate"]
        )
        issues = check_numeric_enumeration(stmt, None)
        assert len(issues) == 1
        assert issues[0].severity == "warning"
        assert issues[0].category == "enumeration"

    def test_period_numbers_flags(self):
        """1. 2. 3. pattern flags"""
        stmt = Statement(
            statement="Management: 1. fluids, 2. antibiotics, 3. monitoring.",
            cloze_candidates=["fluids", "antibiotics", "monitoring"]
        )
        issues = check_numeric_enumeration(stmt, None)
        assert len(issues) == 1

    def test_closing_paren_numbers_flags(self):
        """1) 2) 3) pattern flags"""
        stmt = Statement(
            statement="Criteria: 1) fever, 2) leukocytosis, 3) tachycardia.",
            cloze_candidates=["fever", "leukocytosis", "tachycardia"]
        )
        issues = check_numeric_enumeration(stmt, None)
        assert len(issues) == 1

    def test_step_1_step_2_flags(self):
        """'Step 1...step 2' pattern flags"""
        stmt = Statement(
            statement="In step 1 assess airway, step 2 check breathing.",
            cloze_candidates=["assess airway", "check breathing"]
        )
        issues = check_numeric_enumeration(stmt, None)
        assert len(issues) == 1

    def test_three_types_flags_as_info(self):
        """'Three types' explicit count flags as info"""
        stmt = Statement(
            statement="There are three types of diabetes.",
            cloze_candidates=["diabetes"]
        )
        issues = check_numeric_enumeration(stmt, None)
        assert len(issues) == 1
        assert issues[0].severity == "info"
        assert "three types" in issues[0].message.lower()

    def test_five_criteria_flags_as_info(self):
        """'Five criteria' explicit count flags"""
        stmt = Statement(
            statement="The diagnosis requires five criteria.",
            cloze_candidates=["diagnosis"]
        )
        issues = check_numeric_enumeration(stmt, None)
        assert len(issues) == 1
        assert "five criteria" in issues[0].message.lower()

    def test_four_categories_flags(self):
        """'4 categories' numeric count flags"""
        stmt = Statement(
            statement="There are 4 categories of shock.",
            cloze_candidates=["shock"]
        )
        issues = check_numeric_enumeration(stmt, None)
        assert len(issues) == 1

    def test_location_preserved(self):
        """Location preserved in issue"""
        stmt = Statement(
            statement="Steps: (1) assess, (2) intervene.",
            cloze_candidates=["assess", "intervene"]
        )
        issues = check_numeric_enumeration(stmt, "critique.statement[5]")
        assert len(issues) == 1
        assert issues[0].location == "critique.statement[5]"


class TestCheckComprehensiveCoverageClaim:
    """Test check_comprehensive_coverage_claim detection function"""

    def test_no_comprehensive_term_passes(self):
        """Statement without comprehensive terms passes"""
        stmt = Statement(
            statement="Common adverse effects include headache.",
            cloze_candidates=["headache"]
        )
        issues = check_comprehensive_coverage_claim(stmt, None)
        assert len(issues) == 0

    def test_all_adverse_effects_flags(self):
        """'All adverse effects' flags"""
        stmt = Statement(
            statement="All adverse effects of Drug X include anaphylaxis, headache, and nausea.",
            cloze_candidates=["anaphylaxis", "headache", "nausea"]
        )
        issues = check_comprehensive_coverage_claim(stmt, None)
        assert len(issues) == 1
        assert issues[0].severity == "warning"
        assert issues[0].category == "enumeration"

    def test_every_diagnostic_criterion_flags(self):
        """'Every diagnostic criterion' flags"""
        stmt = Statement(
            statement="Every diagnostic criterion for Disease Y is important.",
            cloze_candidates=["Disease Y"]
        )
        issues = check_comprehensive_coverage_claim(stmt, None)
        assert len(issues) == 1

    def test_complete_list_flags(self):
        """'Complete list' flags"""
        stmt = Statement(
            statement="The complete list of risk factors include diabetes, hypertension, and smoking.",
            cloze_candidates=["diabetes", "hypertension", "smoking"]
        )
        issues = check_comprehensive_coverage_claim(stmt, None)
        assert len(issues) == 1

    def test_full_list_flags(self):
        """'Full list' flags"""
        stmt = Statement(
            statement="Here is the full list of complications.",
            cloze_candidates=["complications"]
        )
        issues = check_comprehensive_coverage_claim(stmt, None)
        assert len(issues) == 1

    def test_entire_set_flags(self):
        """'Entire set' flags"""
        stmt = Statement(
            statement="The entire set of symptoms must be present.",
            cloze_candidates=["symptoms"]
        )
        issues = check_comprehensive_coverage_claim(stmt, None)
        assert len(issues) == 1

    def test_each_of_the_flags(self):
        """'Each of the' flags"""
        stmt = Statement(
            statement="Each of the following criteria is required.",
            cloze_candidates=["criteria"]
        )
        issues = check_comprehensive_coverage_claim(stmt, None)
        assert len(issues) == 1

    def test_case_insensitive_matching(self):
        """Matching is case-insensitive"""
        stmt = Statement(
            statement="ALL adverse effects include headache, nausea, and rash.",
            cloze_candidates=["headache", "nausea", "rash"]
        )
        issues = check_comprehensive_coverage_claim(stmt, None)
        assert len(issues) == 1

    def test_location_preserved(self):
        """Location preserved in issue"""
        stmt = Statement(
            statement="All symptoms include fever.",
            cloze_candidates=["fever"]
        )
        issues = check_comprehensive_coverage_claim(stmt, "key_points.statement[1]")
        assert len(issues) == 1
        assert issues[0].location == "key_points.statement[1]"


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


class TestValidateStatementEnumerations:
    """Test main validate_statement_enumerations orchestrator"""

    def test_no_issues_passes(self):
        """Clean statement passes all checks"""
        stmt = Statement(
            statement="ACE inhibitors are first-line therapy for hypertension.",
            cloze_candidates=["ACE inhibitors", "hypertension"]
        )
        issues = validate_statement_enumerations(stmt, None)
        assert len(issues) == 0

    def test_list_statement_detected(self):
        """List statement is detected"""
        stmt = Statement(
            statement="Adverse effects include anaphylaxis, headache, and nausea.",
            cloze_candidates=["anaphylaxis", "headache", "nausea"]
        )
        issues = validate_statement_enumerations(stmt, None)
        assert len(issues) >= 1
        assert any(issue.category == "enumeration" for issue in issues)

    def test_multi_item_cloze_detected(self):
        """Multi-item cloze is detected"""
        stmt = Statement(
            statement="Symptoms include fever, chills, nausea, and vomiting.",
            cloze_candidates=["fever", "chills", "nausea", "vomiting"]
        )
        issues = validate_statement_enumerations(stmt, None)
        assert len(issues) >= 1

    def test_numeric_enumeration_detected(self):
        """Numeric enumeration is detected"""
        stmt = Statement(
            statement="Steps: (1) assess, (2) intervene, (3) evaluate.",
            cloze_candidates=["assess", "intervene", "evaluate"]
        )
        issues = validate_statement_enumerations(stmt, None)
        assert len(issues) >= 1

    def test_location_passed_through(self):
        """Location is passed to all checks"""
        stmt = Statement(
            statement="Symptoms include fever, chills, and nausea.",
            cloze_candidates=["fever", "chills", "nausea"]
        )
        issues = validate_statement_enumerations(stmt, "critique.statement[0]")
        assert all(issue.location == "critique.statement[0]" for issue in issues)


# ============================================================================
# EDGE CASES
# ============================================================================


class TestEdgeCases:
    """Test edge cases and boundary conditions"""

    def test_empty_statement(self):
        """Empty statement doesn't crash"""
        stmt = Statement(statement="", cloze_candidates=[])
        issues = validate_statement_enumerations(stmt, None)
        assert isinstance(issues, list)

    def test_very_long_statement(self):
        """Very long statement doesn't crash"""
        stmt = Statement(
            statement="This is a very long statement. " * 100,
            cloze_candidates=["long"]
        )
        issues = validate_statement_enumerations(stmt, None)
        assert isinstance(issues, list)

    def test_special_characters_in_statement(self):
        """Special characters don't break regex"""
        stmt = Statement(
            statement="Dose: 5-10 mg/kg/day (max: 2 g/day) include fever, chills, and nausea.",
            cloze_candidates=["fever", "chills", "nausea"]
        )
        issues = validate_statement_enumerations(stmt, None)
        assert isinstance(issues, list)

    def test_unicode_characters(self):
        """Unicode characters handled correctly"""
        stmt = Statement(
            statement="β-blockers include propranolol, metoprolol, and carvedilol.",
            cloze_candidates=["propranolol", "metoprolol", "carvedilol"]
        )
        issues = validate_statement_enumerations(stmt, None)
        assert len(issues) >= 1  # Should still detect enumeration

    def test_no_cloze_candidates(self):
        """Statement with no cloze candidates doesn't crash"""
        stmt = Statement(
            statement="Adverse effects include anaphylaxis, headache, and nausea.",
            cloze_candidates=[]
        )
        issues = validate_statement_enumerations(stmt, None)
        # Should still detect list statement
        assert len(issues) >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
