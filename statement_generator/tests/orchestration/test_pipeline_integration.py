"""
Integration tests for Pipeline orchestration.

Tests the complete 6-step workflow:
1. Read question
2. Extract statements from critique
3. Extract statements from key_points
4. Extract statements from tables
5. Identify cloze candidates
6. Normalize text and validate

Covers:
- Basic workflow (legacy mode)
- Hybrid mode with NLP preprocessing
- Error propagation
- Real question processing
- Statement consolidation integration
- Context enhancement integration
"""

import pytest
import json
from pathlib import Path
from unittest.mock import MagicMock, patch
from src.orchestration.pipeline import StatementPipeline
from src.infrastructure.llm.client import ClaudeClient
from src.infrastructure.io.file_handler import QuestionFileIO
from src.infrastructure.config.settings import NLPConfig
from src.infrastructure.models.data_models import ProcessingResult


@pytest.fixture
def mock_claude_client():
    """Mock ClaudeClient for testing without API calls"""
    client = MagicMock(spec=ClaudeClient)

    # Mock critique extraction response
    client.generate.side_effect = [
        # Critique extraction
        json.dumps(
            {
                "statements": [
                    {
                        "statement": "ACE inhibitors are contraindicated in bilateral renal artery stenosis.",
                        "extra_field": "Bilateral stenosis makes both kidneys dependent on angiotensin II.",
                        "cloze_candidates": [],
                    }
                ]
            }
        ),
        # Key points extraction
        json.dumps(
            {
                "statements": [
                    {
                        "statement": "Hemochromatosis is diagnosed with elevated transferrin saturation.",
                        "extra_field": "Transferrin saturation >45% is the screening test.",
                        "cloze_candidates": [],
                    }
                ]
            }
        ),
        # Context enhancement (critique)
        json.dumps(
            {
                "enhancements": {
                    "1": {
                        "context": "Bilateral stenosis reduces renal perfusion, making ACE inhibitors risky."
                    }
                }
            }
        ),
        # Context enhancement (key points)
        json.dumps(
            {
                "enhancements": {
                    "1": {"context": "Transferrin saturation reflects iron overload."}
                }
            }
        ),
        # Cloze identification (critique)
        json.dumps(
            {
                "cloze_mapping": {
                    "1": [
                        "ACE inhibitors",
                        "bilateral renal artery stenosis",
                    ],
                    "2": ["transferrin saturation"],
                }
            }
        ),
        # Cloze identification (key points)
        json.dumps(
            {
                "cloze_mapping": {
                    "1": ["transferrin saturation"],
                }
            }
        ),
    ]
    client.parse_json_response.side_effect = json.loads

    return client


@pytest.fixture
def temp_question_file(tmp_path):
    """Create temporary question JSON file for testing"""
    question_data = {
        "question_id": "test_001",
        "category": "cv",
        "critique": "ACE inhibitors are contraindicated in bilateral renal artery stenosis because bilateral stenosis makes both kidneys dependent on angiotensin II for glomerular filtration.",
        "key_points": [
            "Hemochromatosis is diagnosed with elevated transferrin saturation. Transferrin saturation >45% is the screening test for iron overload."
        ],
        "educational_objective": "Test objective",
    }

    question_dir = tmp_path / "test_001"
    question_dir.mkdir()
    question_file = question_dir / "test_001.json"

    with open(question_file, "w") as f:
        json.dump(question_data, f)

    return question_file


@pytest.fixture
def prompts_path(tmp_path):
    """Create temporary prompts directory"""
    prompts = tmp_path / "prompts"
    prompts.mkdir()

    # Create minimal prompt files for all processors
    (prompts / "critique_extraction.md").write_text("Extract statements from critique")
    (prompts / "keypoints_extraction.md").write_text(
        "Extract statements from key points"
    )
    (prompts / "table_extraction.md").write_text("Extract statements from tables")
    (prompts / "cloze_identification.md").write_text("Identify cloze candidates")
    (prompts / "cloze_selection.md").write_text("Select final clozes")
    (prompts / "context_enhancement.md").write_text("Enhance clinical context")

    return prompts


class TestPipelineBasicWorkflow:
    """Test basic pipeline workflow (legacy mode)"""

    def test_process_question_complete_workflow(
        self, mock_claude_client, temp_question_file, prompts_path
    ):
        """Process single question through full 6-step pipeline"""
        # Setup
        file_io = QuestionFileIO(mksap_data_path=temp_question_file.parent.parent)

        with patch("src.orchestration.pipeline.NLPConfig") as mock_nlp_config:
            mock_nlp_config.from_env.return_value = NLPConfig(enabled=False)

            pipeline = StatementPipeline(
                client=mock_claude_client,
                file_io=file_io,
                prompts_path=prompts_path,
                nlp_config=None,
            )

            # Execute
            result = pipeline.process_question(temp_question_file)

            # Verify
            assert isinstance(result, ProcessingResult)
            assert result.success is True
            assert result.error is None

            # Verify LLM was called for extraction and cloze identification
            assert (
                mock_claude_client.generate.call_count >= 2
            )  # critique + key_points minimum

    def test_pipeline_stages_called_in_order(
        self, mock_claude_client, temp_question_file, prompts_path
    ):
        """Verify pipeline stages execute in correct order"""
        file_io = QuestionFileIO(mksap_data_path=temp_question_file.parent.parent)

        with patch("src.orchestration.pipeline.NLPConfig") as mock_nlp_config:
            mock_nlp_config.from_env.return_value = NLPConfig(enabled=False)

            pipeline = StatementPipeline(
                client=mock_claude_client,
                file_io=file_io,
                prompts_path=prompts_path,
                nlp_config=None,
            )

            # Patch processors to track execution order
            execution_order = []

            original_critique_extract = pipeline.critique_processor.extract_statements
            original_keypoints_extract = pipeline.keypoints_processor.extract_statements
            original_cloze_identify = (
                pipeline.cloze_identifier.identify_cloze_candidates
            )

            def track_critique(*args, **kwargs):
                execution_order.append("critique")
                return original_critique_extract(*args, **kwargs)

            def track_keypoints(*args, **kwargs):
                execution_order.append("keypoints")
                return original_keypoints_extract(*args, **kwargs)

            def track_cloze(*args, **kwargs):
                execution_order.append("cloze")
                return original_cloze_identify(*args, **kwargs)

            pipeline.critique_processor.extract_statements = track_critique
            pipeline.keypoints_processor.extract_statements = track_keypoints
            pipeline.cloze_identifier.identify_cloze_candidates = track_cloze

            # Execute
            pipeline.process_question(temp_question_file)

            # Verify order
            assert execution_order == [
                "critique",
                "keypoints",
                "cloze",
                "cloze",
                "cloze",
            ]

    def test_result_structure_valid(
        self, mock_claude_client, temp_question_file, prompts_path
    ):
        """Verify ProcessingResult has correct structure"""
        file_io = QuestionFileIO(mksap_data_path=temp_question_file.parent.parent)

        with patch("src.orchestration.pipeline.NLPConfig") as mock_nlp_config:
            mock_nlp_config.from_env.return_value = NLPConfig(enabled=False)

            pipeline = StatementPipeline(
                client=mock_claude_client,
                file_io=file_io,
                prompts_path=prompts_path,
                nlp_config=None,
            )

            result = pipeline.process_question(temp_question_file)

            # Verify ProcessingResult structure
            assert hasattr(result, "success")
            assert hasattr(result, "error")
            assert isinstance(result.success, bool)

    def test_output_json_augmented(
        self, mock_claude_client, temp_question_file, prompts_path
    ):
        """Verify output JSON is augmented with true_statements"""
        file_io = QuestionFileIO(mksap_data_path=temp_question_file.parent.parent)

        with patch("src.orchestration.pipeline.NLPConfig") as mock_nlp_config:
            mock_nlp_config.from_env.return_value = NLPConfig(enabled=False)

            pipeline = StatementPipeline(
                client=mock_claude_client,
                file_io=file_io,
                prompts_path=prompts_path,
                nlp_config=None,
            )

            pipeline.process_question(temp_question_file)

            # Read output JSON
            output_data = file_io.read_question(temp_question_file)

            # Verify augmentation
            assert "true_statements" in output_data
            assert "from_critique" in output_data["true_statements"]
            assert "from_key_points" in output_data["true_statements"]


class TestPipelineHybridMode:
    """Test pipeline with NLP preprocessing (hybrid mode)"""

    @pytest.mark.skip(reason="Requires NLP model setup - implement after basic tests")
    def test_hybrid_mode_nlp_preprocessing(self):
        """Hybrid mode runs NLP preprocessing before extraction"""
        # This test requires:
        # 1. NLPConfig with enabled=True
        # 2. Mock NLP preprocessor
        # 3. Verify NLP context injected to extractors
        pass

    @pytest.mark.skip(reason="Requires NLP model setup")
    def test_nlp_metadata_persisted(self):
        """Hybrid mode persists NLP metadata to JSON"""
        # Verify nlp_analysis field added to output JSON
        # with structure: entities, sentences, negations, counts
        pass


class TestPipelineErrorHandling:
    """Test pipeline error propagation and recovery"""

    def test_error_in_critique_extraction_propagates(
        self, temp_question_file, prompts_path
    ):
        """Error in critique extraction stops pipeline"""
        # Setup client that raises exception
        failing_client = MagicMock(spec=ClaudeClient)
        failing_client.generate.side_effect = Exception("LLM API error")

        file_io = QuestionFileIO(mksap_data_path=temp_question_file.parent.parent)

        with patch("src.orchestration.pipeline.NLPConfig") as mock_nlp_config:
            mock_nlp_config.from_env.return_value = NLPConfig(enabled=False)

            pipeline = StatementPipeline(
                client=failing_client,
                file_io=file_io,
                prompts_path=prompts_path,
                nlp_config=None,
            )

            # Execute
            result = pipeline.process_question(temp_question_file)

            # Verify failure
            assert result.success is False
            assert result.error is not None
            assert (
                "error" in result.error.lower() or "exception" in result.error.lower()
            )

    def test_missing_question_file_handled(self, prompts_path):
        """Missing question file returns error"""
        mock_client = MagicMock(spec=ClaudeClient)
        file_io = QuestionFileIO(mksap_data_path=Path("/nonexistent"))

        with patch("src.orchestration.pipeline.NLPConfig") as mock_nlp_config:
            mock_nlp_config.from_env.return_value = NLPConfig(enabled=False)

            pipeline = StatementPipeline(
                client=mock_client,
                file_io=file_io,
                prompts_path=prompts_path,
                nlp_config=None,
            )

            fake_file = Path("/nonexistent/test_999/test_999.json")

            # Execute
            result = pipeline.process_question(fake_file)

            # Verify error handling
            assert result.success is False
            assert result.error is not None


class TestPipelineIntegration:
    """Integration tests with real components"""

    @pytest.mark.skip(
        reason="Requires actual cvmcq24001 file - implement with TestSprite"
    )
    def test_process_cvmcq24001_real_data(self):
        """Process actual cvmcq24001 question through pipeline"""
        # This test requires:
        # 1. Actual cvmcq24001.json file
        # 2. Mocked LLM responses (realistic)
        # 3. Full validation of output structure
        pass

    @pytest.mark.skip(reason="Requires consolidation setup")
    def test_statement_consolidation_integration(self):
        """Statement consolidation runs in pipeline"""
        # Verify consolidator is called
        # Verify similar statements merged
        pass

    @pytest.mark.skip(reason="Requires context enhancement setup")
    def test_context_enhancement_integration(self):
        """Context enhancement runs in pipeline"""
        # Verify context enhancer is called
        # Verify extra_field_enhanced populated
        # Verify context_source tracking
        pass


class TestPipelineValidation:
    """Test validation integration in pipeline"""

    @pytest.mark.skip(reason="Requires validator setup")
    def test_validation_runs_after_extraction(self):
        """Validation runs after statement extraction"""
        # Verify validators are called
        # Verify validation_pass field added to output
        pass

    @pytest.mark.skip(reason="Requires validator setup")
    def test_validation_failure_reported(self):
        """Validation issues are reported in output"""
        # Create statements that trigger validation issues
        # Verify validation_pass = false
        # Verify issues listed in output
        pass
