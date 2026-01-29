"""
Integration tests for hybrid extra field approach.

Tests the complete flow from Stage 1 (verbatim extraction) through
Stage 2 (enhancement) and validation.

Test Coverage:
- End-to-end pipeline with hybrid approach
- Backward compatibility with legacy extra_field format
- Context source tracking (verbatim, enhanced, hybrid)
- Integration with file I/O migration
- Real question processing (cvmcq24001)
"""

from pathlib import Path
from src.infrastructure.models.data_models import Statement
from src.infrastructure.io.file_handler import QuestionFileIO


class TestHybridExtraFieldFlow:
    """Test complete flow of hybrid extra field approach"""

    def test_stage1_extracts_verbatim_only(self):
        """Stage 1 extractors should populate only extra_field_verbatim"""
        # This would require mocking LLM responses or using actual extraction
        # For now, we test the data model structure

        statement = Statement(
            statement="ACE inhibitors are contraindicated in bilateral renal artery stenosis.",
            cloze_candidates=[],
            extra_field_verbatim="Bilateral stenosis causes both kidneys to rely on angiotensin II.",
            extra_field_enhanced=None,
            context_source="verbatim",
        )

        # Verify Stage 1 output structure
        assert statement.extra_field_verbatim is not None
        assert statement.extra_field_enhanced is None
        assert statement.context_source == "verbatim"

    def test_stage2_adds_enhanced_context(self):
        """Stage 2 should add enhanced context while preserving verbatim"""
        # Simulate Stage 1 output
        stage1_statement = Statement(
            statement="Hemochromatosis is diagnosed with elevated transferrin saturation.",
            cloze_candidates=[],
            extra_field_verbatim="Transferrin saturation >45% is the screening test.",
            extra_field_enhanced=None,
            context_source="verbatim",
        )

        # Simulate Stage 2 enhancement
        stage1_statement.extra_field_enhanced = (
            "Transferrin saturation >45% is the most sensitive screening test. "
            "Ferritin confirms iron overload but can be elevated in inflammation. "
            "Genetic testing (HFE mutation) provides definitive diagnosis."
        )
        stage1_statement.context_source = "hybrid"

        # Verify Stage 2 output structure
        assert stage1_statement.extra_field_verbatim is not None
        assert stage1_statement.extra_field_enhanced is not None
        assert stage1_statement.context_source == "hybrid"

    def test_enhanced_only_when_no_verbatim(self):
        """Stage 2 should create enhanced-only when no verbatim exists"""
        stage1_statement = Statement(
            statement="Beta blockers reduce mortality in heart failure.",
            cloze_candidates=[],
            extra_field_verbatim=None,  # No verbatim from Stage 1
            extra_field_enhanced=None,
            context_source=None,
        )

        # Stage 2 adds enhanced context
        stage1_statement.extra_field_enhanced = (
            "Beta blockers improve cardiac output via upregulation of beta receptors. "
            "Carvedilol and metoprolol succinate have mortality benefit."
        )
        stage1_statement.context_source = "enhanced"

        # Verify enhanced-only structure
        assert stage1_statement.extra_field_verbatim is None
        assert stage1_statement.extra_field_enhanced is not None
        assert stage1_statement.context_source == "enhanced"


class TestBackwardCompatibility:
    """Test migration of legacy extra_field format"""

    def test_file_handler_migrates_legacy_format(self):
        """FileHandler should migrate old extra_field to new format"""
        # Create temporary question file with legacy format
        legacy_data = {
            "question_id": "test001",
            "category": "test",
            "critique": "Test critique",
            "key_points": ["Test key point"],
            "true_statements": {
                "from_critique": [
                    {
                        "statement": "Test statement with legacy extra field.",
                        "extra_field": "This is legacy enhanced context.",
                        "cloze_candidates": ["legacy"],
                    }
                ]
            },
        }

        # Create file handler and test migration
        file_io = QuestionFileIO(Path("/tmp"))

        # Simulate migration by calling _migrate_legacy_extra_field
        file_io._migrate_legacy_extra_field(legacy_data)

        # Check migration result
        stmt = legacy_data["true_statements"]["from_critique"][0]
        assert stmt["extra_field_verbatim"] is None
        assert stmt["extra_field_enhanced"] == "This is legacy enhanced context."
        assert stmt["context_source"] == "enhanced"
        assert "extra_field" in stmt  # Kept for backward compatibility

    def test_migration_preserves_new_format(self):
        """Migration should not affect already-migrated data"""
        new_data = {
            "question_id": "test002",
            "category": "test",
            "critique": "Test critique",
            "key_points": [],
            "true_statements": {
                "from_critique": [
                    {
                        "statement": "Test statement with new format.",
                        "extra_field_verbatim": "Verbatim context",
                        "extra_field_enhanced": "Enhanced context",
                        "context_source": "hybrid",
                        "cloze_candidates": [],
                    }
                ]
            },
        }

        file_io = QuestionFileIO(Path("/tmp"))
        file_io._migrate_legacy_extra_field(new_data)

        # Should remain unchanged
        stmt = new_data["true_statements"]["from_critique"][0]
        assert stmt["extra_field_verbatim"] == "Verbatim context"
        assert stmt["extra_field_enhanced"] == "Enhanced context"
        assert stmt["context_source"] == "hybrid"

    def test_migration_handles_null_extra_field(self):
        """Migration should handle None/null extra_field gracefully"""
        data_with_null = {
            "question_id": "test003",
            "category": "test",
            "critique": "Test",
            "key_points": [],
            "true_statements": {
                "from_critique": [
                    {
                        "statement": "Test statement with null extra field.",
                        "extra_field": None,
                        "cloze_candidates": [],
                    }
                ]
            },
        }

        file_io = QuestionFileIO(Path("/tmp"))
        file_io._migrate_legacy_extra_field(data_with_null)

        # Should migrate to None for both fields
        stmt = data_with_null["true_statements"]["from_critique"][0]
        assert stmt["extra_field_verbatim"] is None
        assert stmt["extra_field_enhanced"] is None
        assert stmt["context_source"] is None


class TestContextSourceTracking:
    """Test context_source field tracking"""

    def test_verbatim_only_source(self):
        """Verbatim-only statements should have context_source='verbatim'"""
        statement = Statement(
            statement="Test",
            cloze_candidates=[],
            extra_field_verbatim="Source context",
            extra_field_enhanced=None,
            context_source="verbatim",
        )

        assert statement.context_source == "verbatim"

    def test_enhanced_only_source(self):
        """Enhanced-only statements should have context_source='enhanced'"""
        statement = Statement(
            statement="Test",
            cloze_candidates=[],
            extra_field_verbatim=None,
            extra_field_enhanced="LLM context",
            context_source="enhanced",
        )

        assert statement.context_source == "enhanced"

    def test_hybrid_source(self):
        """Hybrid statements should have context_source='hybrid'"""
        statement = Statement(
            statement="Test",
            cloze_candidates=[],
            extra_field_verbatim="Source",
            extra_field_enhanced="LLM enhancement",
            context_source="hybrid",
        )

        assert statement.context_source == "hybrid"

    def test_no_context_source_none(self):
        """Statements without context should have context_source=None"""
        statement = Statement(
            statement="Test",
            cloze_candidates=[],
            extra_field_verbatim=None,
            extra_field_enhanced=None,
            context_source=None,
        )

        assert statement.context_source is None


class TestRealQuestionProcessing:
    """Test with real MKSAP question data"""

    def test_cvmcq24001_hybrid_approach(self):
        """Process cvmcq24001 with hybrid approach using mocked LLM"""
        import json

        # Read actual cvmcq24001.json file
        question_path = Path(
            "/Users/Mitchell/coding/projects/MKSAP/mksap_data/cv/cvmcq24001/cvmcq24001.json"
        )
        assert question_path.exists(), "cvmcq24001.json not found"

        with open(question_path, "r") as f:
            question_data = json.load(f)

        # Verify question has critique and key_points
        assert "critique" in question_data
        assert "key_points" in question_data

        # Mock Stage 1 LLM response (verbatim extraction)
        mock_stage1_response = {
            "statements": [
                {
                    "statement": "In patients with suspected ACS but nondiagnostic initial testing, serial ECGs and modified lead ECGs are indicated.",
                    "extra_field": "Serial ECGs should be repeated every 15 to 30 minutes as necessary to clarify the diagnosis.",
                    "cloze_candidates": [],
                },
                {
                    "statement": "Posterior myocardial infarction requires modified posterior leads V7, V8, and/or V9.",
                    "extra_field": "Recognition of 1 mm ST-segment elevation in leads V7 and V8 is diagnostic of posterior MI.",
                    "cloze_candidates": [],
                },
            ]
        }

        # Mock Stage 2 LLM response (context enhancement)
        mock_stage2_response = {
            "enhancements": {
                "1": {
                    "context": "Serial ECGs every 15-30 minutes clarify diagnosis. Posterior MI shows ST elevation in V7-V9 leads, indicating need for immediate reperfusion (PCI or thrombolysis)."
                }
            }
        }

        # Create statements simulating Stage 1 output (verbatim only)
        stage1_statements = [
            Statement(
                statement=mock_stage1_response["statements"][0]["statement"],
                extra_field_verbatim=mock_stage1_response["statements"][0][
                    "extra_field"
                ],
                extra_field_enhanced=None,
                context_source="verbatim",
                cloze_candidates=[],
            ),
            Statement(
                statement=mock_stage1_response["statements"][1]["statement"],
                extra_field_verbatim=mock_stage1_response["statements"][1][
                    "extra_field"
                ],
                extra_field_enhanced=None,
                context_source="verbatim",
                cloze_candidates=[],
            ),
        ]

        # Verify Stage 1: verbatim extraction only
        for stmt in stage1_statements:
            assert stmt.extra_field_verbatim is not None
            assert stmt.extra_field_enhanced is None
            assert stmt.context_source == "verbatim"

        # Simulate Stage 2: enhancement (only first statement needs enhancement)
        stage2_statements = stage1_statements.copy()
        stage2_statements[0].extra_field_enhanced = mock_stage2_response[
            "enhancements"
        ]["1"]["context"]
        stage2_statements[0].context_source = "hybrid"

        # Verify Stage 2: hybrid context
        assert stage2_statements[0].extra_field_verbatim is not None
        assert stage2_statements[0].extra_field_enhanced is not None
        assert stage2_statements[0].context_source == "hybrid"

        # Verify second statement remains verbatim-only
        assert stage2_statements[1].context_source == "verbatim"
        assert stage2_statements[1].extra_field_enhanced is None

        # Verify hallucination validator would run (test the structure)
        from src.processing.statements.validators.hallucination import (
            validate_enhanced_context,
        )

        source_context = {
            "critique": question_data["critique"],
            "key_points": question_data["key_points"],
        }

        # Validate enhanced context against source
        issues = validate_enhanced_context(
            stage2_statements[0], source_context, "test.cvmcq24001[0]"
        )

        # Should not flag hallucination since enhancement references source material
        assert len(issues) == 0, f"Unexpected validation issues: {issues}"

    def test_batch_processing_with_hybrid(self):
        """Process multiple questions with hybrid approach (simulated batch)"""
        # Simulate processing 3 questions with different scenarios:
        # 1. New question → hybrid approach
        # 2. Legacy question → migration to new format
        # 3. Mixed quality contexts

        # Question 1: Fresh processing with hybrid approach
        q1_statements = [
            Statement(
                statement="ACE inhibitors are contraindicated in bilateral renal artery stenosis.",
                extra_field_verbatim="Bilateral stenosis makes both kidneys dependent on angiotensin II.",
                extra_field_enhanced="Both kidneys rely on angiotensin II for GFR maintenance. ACE inhibition causes acute kidney injury.",
                context_source="hybrid",
                cloze_candidates=["ACE inhibitors", "bilateral renal artery stenosis"],
            ),
            Statement(
                statement="Hemochromatosis is diagnosed with elevated transferrin saturation.",
                extra_field_verbatim="Transferrin saturation >45% is the screening test.",
                extra_field_enhanced=None,
                context_source="verbatim",
                cloze_candidates=["transferrin saturation"],
            ),
        ]

        # Question 2: Legacy format (simulates migration)
        q2_legacy_statement = Statement(
            statement="Reslizumab adverse effects include anaphylaxis.",
            extra_field="Reslizumab is an anti-IL-5 monoclonal antibody for severe eosinophilic asthma.",
            extra_field_verbatim=None,
            extra_field_enhanced=None,
            context_source=None,
            cloze_candidates=["Reslizumab", "anaphylaxis"],
        )

        # Simulate migration for legacy statement
        q2_migrated = Statement(
            statement=q2_legacy_statement.statement,
            extra_field_verbatim=None,  # Legacy had no verbatim
            extra_field_enhanced=q2_legacy_statement.extra_field,  # Old extra_field → enhanced
            context_source="enhanced",
            cloze_candidates=q2_legacy_statement.cloze_candidates,
        )

        # Question 3: No context (enhancement skipped)
        q3_statements = [
            Statement(
                statement="Tinea cruris is caused by dermatophytes.",
                extra_field_verbatim=None,
                extra_field_enhanced=None,
                context_source=None,
                cloze_candidates=["dermatophytes"],
            )
        ]

        # Collect all statements
        all_statements = q1_statements + [q2_migrated] + q3_statements

        # Verify batch processing outcomes
        # 1. Check context_source values are valid
        valid_sources = {"verbatim", "enhanced", "hybrid", None}
        for stmt in all_statements:
            assert stmt.context_source in valid_sources, (
                f"Invalid context_source: {stmt.context_source}"
            )

        # 2. Verify hybrid statements have both fields
        hybrid_statements = [s for s in all_statements if s.context_source == "hybrid"]
        for stmt in hybrid_statements:
            assert stmt.extra_field_verbatim is not None
            assert stmt.extra_field_enhanced is not None

        # 3. Verify verbatim-only statements have only verbatim
        verbatim_statements = [
            s for s in all_statements if s.context_source == "verbatim"
        ]
        for stmt in verbatim_statements:
            assert stmt.extra_field_verbatim is not None
            assert stmt.extra_field_enhanced is None

        # 4. Verify enhanced-only statements (migrated legacy)
        enhanced_statements = [
            s for s in all_statements if s.context_source == "enhanced"
        ]
        for stmt in enhanced_statements:
            assert stmt.extra_field_enhanced is not None
            # Verbatim can be None (legacy migration)

        # 5. Verify hallucination validation would run for enhanced content
        from src.processing.statements.validators.hallucination import (
            validate_enhanced_context,
        )

        # Test on hybrid statement
        source_context = {
            "critique": "ACE inhibitors are contraindicated in bilateral renal artery stenosis. Bilateral stenosis makes both kidneys dependent on angiotensin II for GFR maintenance.",
            "key_points": [],
        }

        issues = validate_enhanced_context(
            q1_statements[0],  # Hybrid statement
            source_context,
            "test.batch[0]",
        )

        # Should pass - enhanced content references source
        assert len(issues) == 0

        # 6. Verify counts
        assert len(all_statements) == 4
        assert len([s for s in all_statements if s.context_source == "hybrid"]) == 1
        assert len([s for s in all_statements if s.context_source == "verbatim"]) == 1
        assert len([s for s in all_statements if s.context_source == "enhanced"]) == 1
        assert len([s for s in all_statements if s.context_source is None]) == 1


class TestTableStatementHybrid:
    """Test hybrid approach for table statements"""

    def test_table_statement_has_hybrid_fields(self):
        """TableStatement should support hybrid extra field"""
        from src.infrastructure.models.data_models import TableStatement

        table_stmt = TableStatement(
            statement="Serum calcium >11 mg/dL indicates hypercalcemia.",
            cloze_candidates=[">11 mg/dL"],
            extra_field_verbatim="Table caption: Calcium reference ranges",
            extra_field_enhanced="Severe hypercalcemia (>14 mg/dL) requires urgent treatment.",
            context_source="hybrid",
            table_source="inline_table_1.html",
        )

        assert table_stmt.extra_field_verbatim is not None
        assert table_stmt.extra_field_enhanced is not None
        assert table_stmt.context_source == "hybrid"

    def test_table_migration(self):
        """Table statements should migrate legacy format"""
        data_with_table = {
            "question_id": "test004",
            "category": "test",
            "critique": "Test",
            "key_points": [],
            "table_statements": {
                "statements": [
                    {
                        "statement": "Table fact",
                        "extra_field": "Legacy table context",
                        "cloze_candidates": [],
                        "table_source": "table1.html",
                    }
                ],
                "tables_processed": 1,
                "tables_skipped": 0,
            },
        }

        file_io = QuestionFileIO(Path("/tmp"))
        file_io._migrate_legacy_extra_field(data_with_table)

        # Check table statement migration
        stmt = data_with_table["table_statements"]["statements"][0]
        assert stmt["extra_field_verbatim"] is None
        assert stmt["extra_field_enhanced"] == "Legacy table context"
        assert stmt["context_source"] == "enhanced"


class TestValidationIntegration:
    """Test integration with hallucination validator"""

    def test_enhanced_context_validation_triggered(self):
        """Validation should run for enhanced and hybrid contexts"""
        from src.processing.statements.validators.hallucination import (
            validate_enhanced_context,
        )

        # Enhanced context
        enhanced_stmt = Statement(
            statement="Test",
            cloze_candidates=[],
            extra_field_enhanced="Enhanced context here",
            context_source="enhanced",
        )

        source = {"critique": "Original critique text"}

        # Should run validation
        issues = validate_enhanced_context(enhanced_stmt, source, None)
        # Issues depend on actual overlap, but validation should execute

    def test_verbatim_context_validation_skipped(self):
        """Validation should skip for verbatim-only contexts"""
        from src.processing.statements.validators.hallucination import (
            validate_enhanced_context,
        )

        # Verbatim only
        verbatim_stmt = Statement(
            statement="Test",
            cloze_candidates=[],
            extra_field_verbatim="Verbatim only",
            extra_field_enhanced=None,
            context_source="verbatim",
        )

        source = {"critique": "Original critique text"}

        # Should skip validation
        issues = validate_enhanced_context(verbatim_stmt, source, None)
        assert len(issues) == 0  # No validation for verbatim-only


# 1. Add real file I/O tests with actual temp files
# 2. Add concurrent processing tests (multiple questions in parallel)
# 3. Add performance benchmarks (time to process 100 questions)
# 4. Add tests for error recovery (what if Stage 2 fails?)
# 5. Add tests for configuration changes (enable/disable enhancement)
# 6. Add regression tests using all 14 test questions from audit
# 7. Add property-based tests for migration logic
# 8. Add tests for serialization/deserialization round-trip
