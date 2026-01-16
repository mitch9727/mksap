"""
Test suite for Phase 1 NLP components (scispaCy integration).

Tests cover:
- NLPPreprocessor: Main orchestrator for NLP pipeline
- NegationDetector: Negation detection using patterns and dependency parsing
- AtomicityAnalyzer: Sentence atomicity analysis for split recommendations
- FactCandidateGenerator: Fact candidate generation from NLP artifacts

Target: Verify Phase 1 scaffolding works without changing pipeline behavior.
"""

import pytest
from typing import List

# Skip all tests if spaCy is not available
spacy = pytest.importorskip("spacy")

from src.infrastructure.config.settings import NLPConfig
from src.infrastructure.models.nlp_artifacts import (
    EntityType,
    MedicalEntity,
    NLPArtifacts,
    SentenceSpan,
)
from src.infrastructure.models.fact_candidates import (
    AtomicityRecommendation,
    EnrichedPromptContext,
)
from src.processing.nlp.negation_detector import NegationDetector
from src.processing.nlp.atomicity_analyzer import AtomicityAnalyzer
from src.processing.nlp.fact_candidate_generator import FactCandidateGenerator
from src.processing.nlp.preprocessor import NLPPreprocessor


# Clear NLP cache before tests to ensure fresh model loading
@pytest.fixture(autouse=True)
def clear_nlp_cache():
    """Clear NLP model cache before each test."""
    from src.validation.nlp_utils import get_nlp
    get_nlp.cache_clear()
    yield
    get_nlp.cache_clear()


class TestNegationDetector:
    """Test negation detection functionality."""

    def setup_method(self):
        self.detector = NegationDetector()
        # Create blank model with sentencizer for testing
        self.nlp = spacy.blank("en")
        self.nlp.add_pipe("sentencizer")

    def test_simple_negation_no_diabetes(self):
        """'no diabetes' should be detected as negated."""
        doc = self.nlp("Patient has no diabetes.")
        # Create fake entity span
        from spacy.tokens import Span
        span = Span(doc, 3, 4, label="DISEASE")
        doc.ents = [span]

        is_negated, trigger = self.detector.is_negated(
            doc.ents[0], use_dependency_parse=False
        )

        assert is_negated is True
        assert trigger == "no"

    def test_simple_negation_without(self):
        """'without fever' should be detected as negated."""
        doc = self.nlp("Patient presents without fever.")
        from spacy.tokens import Span
        span = Span(doc, 3, 4, label="SYMPTOM")
        doc.ents = [span]

        is_negated, trigger = self.detector.is_negated(
            doc.ents[0], use_dependency_parse=False
        )

        assert is_negated is True
        assert trigger == "without"

    def test_no_negation_positive_statement(self):
        """'has diabetes' should not be negated."""
        doc = self.nlp("Patient has diabetes.")
        from spacy.tokens import Span
        span = Span(doc, 2, 3, label="DISEASE")
        doc.ents = [span]

        is_negated, trigger = self.detector.is_negated(
            doc.ents[0], use_dependency_parse=False
        )

        assert is_negated is False
        assert trigger is None

    def test_phrase_negation_no_evidence_of(self):
        """'no evidence of malignancy' should be detected."""
        doc = self.nlp("CT scan shows no evidence of malignancy.")
        from spacy.tokens import Span
        span = Span(doc, 6, 7, label="DISEASE")
        doc.ents = [span]

        is_negated, trigger = self.detector.is_negated(
            doc.ents[0], use_dependency_parse=False
        )

        assert is_negated is True
        assert trigger == "no evidence of"

    def test_phrase_negation_negative_for(self):
        """'negative for infection' should be detected."""
        doc = self.nlp("Blood cultures negative for infection.")
        from spacy.tokens import Span
        span = Span(doc, 3, 4, label="DISEASE")
        doc.ents = [span]

        is_negated, trigger = self.detector.is_negated(
            doc.ents[0], use_dependency_parse=False
        )

        assert is_negated is True
        # May detect "negative" or "negative for" depending on phrase matching
        assert "negative" in trigger

    def test_negation_same_sentence_only(self):
        """Negation in same sentence should be detected."""
        doc = self.nlp("Patient has no diabetes.")
        from spacy.tokens import Span
        span = Span(doc, 3, 4, label="DISEASE")
        doc.ents = [span]

        is_negated, trigger = self.detector.is_negated(
            doc.ents[0], use_dependency_parse=False
        )

        assert is_negated is True
        assert trigger == "no"

    def test_find_negation_spans(self):
        """Should find all negation spans in document."""
        doc = self.nlp("No fever, no cough. Patient does not have diabetes.")

        spans = self.detector.find_negation_spans(doc)

        # Should find "no" twice and "does not"
        assert len(spans) >= 2

    def test_negation_triggers_frozenset(self):
        """NEGATION_TRIGGERS should be a frozenset for performance."""
        assert isinstance(self.detector.NEGATION_TRIGGERS, frozenset)
        assert "no" in self.detector.NEGATION_TRIGGERS
        assert "not" in self.detector.NEGATION_TRIGGERS
        assert "without" in self.detector.NEGATION_TRIGGERS


class TestAtomicityAnalyzer:
    """Test atomicity analysis functionality."""

    def setup_method(self):
        self.analyzer = AtomicityAnalyzer()

    def _make_sentence(
        self, text: str, verb_count: int = 1, is_complex: bool = False
    ) -> SentenceSpan:
        return SentenceSpan(
            text=text,
            start_char=0,
            end_char=len(text),
            index=0,
            has_negation=False,
            verb_count=verb_count,
            is_complex=is_complex,
            entity_indices=[],
        )

    def _make_entity(
        self, text: str, entity_type: EntityType, is_negated: bool = False
    ) -> MedicalEntity:
        return MedicalEntity(
            text=text,
            entity_type=entity_type,
            start_char=0,
            end_char=len(text),
            sentence_index=0,
            is_negated=is_negated,
            negation_trigger=None,
            modifiers=[],
            confidence=1.0,
            spacy_label="ENTITY",
        )

    def test_single_entity_atomic(self):
        """Single entity sentence should be ATOMIC_SINGLE."""
        sentence = self._make_sentence("Diabetes causes nephropathy.")
        entities = [self._make_entity("Diabetes", EntityType.DISEASE)]

        result = self.analyzer.analyze_sentence(sentence, entities)

        assert result == AtomicityRecommendation.ATOMIC_SINGLE

    def test_multiple_diseases_should_split(self):
        """Multiple independent diseases should trigger SHOULD_SPLIT."""
        sentence = self._make_sentence(
            "Patient has diabetes, hypertension, and hyperlipidemia.",
            verb_count=1,
            is_complex=True,
        )
        entities = [
            self._make_entity("diabetes", EntityType.DISEASE),
            self._make_entity("hypertension", EntityType.DISEASE),
            self._make_entity("hyperlipidemia", EntityType.DISEASE),
        ]

        result = self.analyzer.analyze_sentence(sentence, entities)

        assert result == AtomicityRecommendation.SHOULD_SPLIT

    def test_medication_with_disease_multi_cloze(self):
        """Medication + disease (mechanism) should be MULTI_CLOZE_OK."""
        sentence = self._make_sentence(
            "Metformin is first-line treatment for type 2 diabetes."
        )
        entities = [
            self._make_entity("Metformin", EntityType.MEDICATION),
            self._make_entity("type 2 diabetes", EntityType.DISEASE),
        ]

        result = self.analyzer.analyze_sentence(sentence, entities)

        assert result == AtomicityRecommendation.MULTI_CLOZE_OK

    def test_complex_sentence_multiple_verbs(self):
        """Complex sentence with multiple verbs may need context."""
        sentence = self._make_sentence(
            "ACE inhibitors reduce proteinuria and slow CKD progression when used early.",
            verb_count=3,
            is_complex=True,
        )
        entities = [
            self._make_entity("ACE inhibitors", EntityType.MEDICATION),
            self._make_entity("proteinuria", EntityType.DISEASE),
            self._make_entity("CKD", EntityType.DISEASE),
        ]

        result = self.analyzer.analyze_sentence(sentence, entities)

        # Should recognize this needs context or splitting
        assert result in (
            AtomicityRecommendation.COMPLEX_NEEDS_CONTEXT,
            AtomicityRecommendation.SHOULD_SPLIT,
        )

    def test_generate_split_recommendation_none_for_atomic(self):
        """Atomic sentences should not generate split recommendations."""
        sentence = self._make_sentence("Diabetes is common.")
        entities = [self._make_entity("Diabetes", EntityType.DISEASE)]
        atomicity = AtomicityRecommendation.ATOMIC_SINGLE

        rec = self.analyzer.generate_split_recommendation(sentence, entities, atomicity)

        assert rec is None

    def test_generate_split_recommendation_for_should_split(self):
        """SHOULD_SPLIT sentences should generate recommendations."""
        sentence = self._make_sentence(
            "Patient has diabetes and hypertension.",
            is_complex=True,
        )
        entities = [
            self._make_entity("diabetes", EntityType.DISEASE),
            self._make_entity("hypertension", EntityType.DISEASE),
        ]
        atomicity = AtomicityRecommendation.SHOULD_SPLIT

        rec = self.analyzer.generate_split_recommendation(sentence, entities, atomicity)

        assert rec is not None
        assert rec.sentence_index == 0
        assert len(rec.reason) > 0
        assert "disease" in rec.reason.lower() or "independent" in rec.reason.lower()


class TestFactCandidateGenerator:
    """Test fact candidate generation functionality."""

    def setup_method(self):
        self.atomicity_analyzer = AtomicityAnalyzer()
        self.generator = FactCandidateGenerator(self.atomicity_analyzer)

    def _make_artifacts(self) -> NLPArtifacts:
        """Create sample NLP artifacts for testing."""
        return NLPArtifacts(
            source_text="Diabetes causes nephropathy. Metformin reduces blood glucose.",
            source_field="critique",
            sentences=[
                SentenceSpan(
                    text="Diabetes causes nephropathy.",
                    start_char=0,
                    end_char=28,
                    index=0,
                    has_negation=False,
                    verb_count=1,
                    is_complex=False,
                    entity_indices=[0, 1],
                ),
                SentenceSpan(
                    text="Metformin reduces blood glucose.",
                    start_char=29,
                    end_char=61,
                    index=1,
                    has_negation=False,
                    verb_count=1,
                    is_complex=False,
                    entity_indices=[2],
                ),
            ],
            entities=[
                MedicalEntity(
                    text="Diabetes",
                    entity_type=EntityType.DISEASE,
                    start_char=0,
                    end_char=8,
                    sentence_index=0,
                    is_negated=False,
                    negation_trigger=None,
                    modifiers=[],
                    confidence=1.0,
                    spacy_label="DISEASE",
                ),
                MedicalEntity(
                    text="nephropathy",
                    entity_type=EntityType.DISEASE,
                    start_char=16,
                    end_char=27,
                    sentence_index=0,
                    is_negated=False,
                    negation_trigger=None,
                    modifiers=[],
                    confidence=1.0,
                    spacy_label="DISEASE",
                ),
                MedicalEntity(
                    text="Metformin",
                    entity_type=EntityType.MEDICATION,
                    start_char=29,
                    end_char=38,
                    sentence_index=1,
                    is_negated=False,
                    negation_trigger=None,
                    modifiers=[],
                    confidence=1.0,
                    spacy_label="CHEMICAL",
                ),
            ],
            negation_spans=[],
            split_recommendations=[],
            model_name="test",
            parser_enabled=False,
        )

    def test_generate_returns_enriched_context(self):
        """Generator should return EnrichedPromptContext."""
        artifacts = self._make_artifacts()

        result = self.generator.generate(artifacts)

        assert isinstance(result, EnrichedPromptContext)

    def test_generate_creates_fact_candidates(self):
        """Generator should create fact candidates from sentences."""
        artifacts = self._make_artifacts()

        result = self.generator.generate(artifacts)

        assert len(result.fact_candidates) == 2  # Two sentences

    def test_fact_candidates_have_atomicity(self):
        """Each fact candidate should have atomicity recommendation."""
        artifacts = self._make_artifacts()

        result = self.generator.generate(artifacts)

        for candidate in result.fact_candidates:
            assert candidate.atomicity in list(AtomicityRecommendation)

    def test_entity_summary_generated(self):
        """Entity summary should be generated."""
        artifacts = self._make_artifacts()

        result = self.generator.generate(artifacts)

        assert len(result.entity_summary) > 0
        # Should mention count of entities
        assert any(char.isdigit() for char in result.entity_summary)

    def test_negation_summary_generated(self):
        """Negation summary should be generated when negated entities exist."""
        artifacts = self._make_artifacts_with_negation()

        result = self.generator.generate(artifacts)

        assert len(result.negation_summary) > 0
        assert "negated" in result.negation_summary.lower()

    def _make_artifacts_with_negation(self) -> NLPArtifacts:
        """Create artifacts with negated entities for testing."""
        return NLPArtifacts(
            source_text="Patient has no evidence of diabetes.",
            source_field="critique",
            sentences=[
                SentenceSpan(
                    text="Patient has no evidence of diabetes.",
                    start_char=0,
                    end_char=36,
                    index=0,
                    has_negation=True,
                    verb_count=1,
                    is_complex=False,
                    entity_indices=[0],
                ),
            ],
            entities=[
                MedicalEntity(
                    text="diabetes",
                    entity_type=EntityType.DISEASE,
                    start_char=27,
                    end_char=35,
                    sentence_index=0,
                    is_negated=True,
                    negation_trigger="no evidence of",
                    modifiers=[],
                    confidence=1.0,
                    spacy_label="DISEASE",
                ),
            ],
            negation_spans=[("no evidence of", 12, 26)],
            split_recommendations=[],
            model_name="test",
            parser_enabled=False,
        )

    def test_negation_summary_empty_when_no_negations(self):
        """Negation summary should be empty when no negated entities."""
        artifacts = self._make_artifacts()

        result = self.generator.generate(artifacts)

        # Empty string for no negations
        assert result.negation_summary == ""


class TestNLPPreprocessor:
    """Test the main NLP preprocessor orchestrator."""

    @pytest.fixture
    def preprocessor(self):
        """Create preprocessor with default config."""
        config = NLPConfig.from_env()
        return NLPPreprocessor(config)

    def test_process_returns_nlp_artifacts(self, preprocessor):
        """process() should return NLPArtifacts."""
        text = "Patient has diabetes."

        result = preprocessor.process(text, "critique")

        assert isinstance(result, NLPArtifacts)

    def test_process_extracts_sentences(self, preprocessor):
        """Should extract sentences from text."""
        text = "First sentence. Second sentence."

        result = preprocessor.process(text, "critique")

        assert len(result.sentences) >= 2

    def test_process_extracts_entities(self, preprocessor):
        """Should extract entities from medical text."""
        text = "Patient has diabetes and hypertension."

        result = preprocessor.process(text, "critique")

        # Should find at least some entities
        assert len(result.entities) > 0

    def test_process_detects_negation(self, preprocessor):
        """Should detect negation in text."""
        text = "Patient has no evidence of diabetes."

        result = preprocessor.process(text, "critique")

        # Should have negation spans
        assert len(result.negation_spans) > 0

    def test_process_empty_text(self, preprocessor):
        """Empty text should return empty artifacts without crash."""
        result = preprocessor.process("", "critique")

        assert result.source_text == ""
        assert len(result.sentences) == 0
        assert len(result.entities) == 0

    def test_process_whitespace_text(self, preprocessor):
        """Whitespace-only text should return empty artifacts."""
        result = preprocessor.process("   \n\t  ", "critique")

        assert len(result.sentences) == 0
        assert len(result.entities) == 0

    def test_generate_prompt_context(self, preprocessor):
        """Should generate prompt context from artifacts."""
        text = "Metformin is used for diabetes."
        artifacts = preprocessor.process(text, "critique")

        context = preprocessor.generate_prompt_context(artifacts)

        assert isinstance(context, EnrichedPromptContext)
        assert len(context.fact_candidates) > 0

    def test_process_and_enrich_convenience_method(self, preprocessor):
        """process_and_enrich() should combine process and generate."""
        text = "Metformin is used for diabetes."

        context = preprocessor.process_and_enrich(text, "critique")

        assert isinstance(context, EnrichedPromptContext)

    def test_source_field_preserved(self, preprocessor):
        """Source field should be preserved in artifacts."""
        text = "Test text."

        result = preprocessor.process(text, "keypoints")

        assert result.source_field == "keypoints"

    def test_model_name_set(self, preprocessor):
        """Model name should be set in artifacts."""
        text = "Test text."

        result = preprocessor.process(text, "critique")

        assert result.model_name is not None


class TestNLPConfigIntegration:
    """Test NLP configuration integration."""

    def test_config_from_env(self):
        """NLPConfig should load from environment."""
        config = NLPConfig.from_env()

        assert config.enabled is True
        assert len(config.model) > 0

    def test_hybrid_pipeline_default_false(self):
        """Hybrid pipeline should be disabled by default."""
        # This depends on env var not being set
        import os
        original = os.environ.get("USE_HYBRID_PIPELINE")
        if original:
            del os.environ["USE_HYBRID_PIPELINE"]

        config = NLPConfig.from_env()

        # Restore
        if original:
            os.environ["USE_HYBRID_PIPELINE"] = original

        # Default should be False
        assert config.use_hybrid_pipeline is False


class TestEntityTypeMappings:
    """Test entity type mapping from spaCy labels."""

    def test_disease_mapping(self):
        from src.processing.nlp.preprocessor import SPACY_LABEL_TO_ENTITY_TYPE

        assert SPACY_LABEL_TO_ENTITY_TYPE.get("DISEASE") == EntityType.DISEASE

    def test_chemical_mapping(self):
        from src.processing.nlp.preprocessor import SPACY_LABEL_TO_ENTITY_TYPE

        # CHEMICAL maps to MEDICATION when using bc5cdr model
        # or CHEMICAL for other models
        assert SPACY_LABEL_TO_ENTITY_TYPE.get("CHEMICAL") in (
            EntityType.MEDICATION,
            EntityType.CHEMICAL,
        )

    def test_unknown_label_defaults_to_other(self):
        from src.processing.nlp.preprocessor import SPACY_LABEL_TO_ENTITY_TYPE

        # Unknown labels should not be in mapping
        unknown = SPACY_LABEL_TO_ENTITY_TYPE.get("UNKNOWN_LABEL")
        assert unknown is None  # Falls back to OTHER in code


class TestPhase1NoRegressionBehavior:
    """Tests to verify Phase 1 doesn't change pipeline behavior."""

    def test_preprocessor_does_not_modify_input(self):
        """Preprocessor should not modify input text."""
        config = NLPConfig.from_env()
        preprocessor = NLPPreprocessor(config)

        original_text = "Patient has diabetes."
        result = preprocessor.process(original_text, "critique")

        # Source text should be unchanged
        assert result.source_text == original_text

    def test_hybrid_mode_graceful_failure(self):
        """If NLP fails, should not crash pipeline."""
        config = NLPConfig.from_env()
        preprocessor = NLPPreprocessor(config)

        # Edge case: very long text
        long_text = "word " * 10000
        result = preprocessor.process(long_text, "critique")

        # Should still return valid artifacts
        assert isinstance(result, NLPArtifacts)
