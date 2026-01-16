"""
NLP Preprocessor - Orchestrates scispaCy analysis pipeline.

Main entry point for NLP processing in the hybrid pipeline.
Converts raw text into structured NLP artifacts with:
- Sentence segmentation
- Entity extraction with type mapping
- Negation detection
- Atomicity analysis
- Fact candidate generation
"""

import logging
from typing import List, Optional

from ...infrastructure.config.settings import NLPConfig
from ...infrastructure.models.nlp_artifacts import (
    EntityType,
    MedicalEntity,
    NLPArtifacts,
    SentenceSpan,
)
from ...infrastructure.models.fact_candidates import EnrichedPromptContext
from .negation_detector import NegationDetector
from .atomicity_analyzer import AtomicityAnalyzer
from .fact_candidate_generator import FactCandidateGenerator

# Import spaCy utilities from validation module (ensures .env is loaded)
from ...validation.nlp_utils import get_nlp

logger = logging.getLogger(__name__)


# Mapping from scispaCy entity labels to our EntityType enum
SPACY_LABEL_TO_ENTITY_TYPE = {
    # scispaCy en_core_sci_* labels
    "ENTITY": EntityType.OTHER,  # Generic entity from sci models
    "DISEASE": EntityType.DISEASE,
    "CHEMICAL": EntityType.CHEMICAL,
    "DRUG": EntityType.MEDICATION,
    "GENE_OR_GENE_PRODUCT": EntityType.OTHER,
    "CELL_LINE": EntityType.OTHER,
    "CELL_TYPE": EntityType.ANATOMY,
    "DNA": EntityType.OTHER,
    "RNA": EntityType.OTHER,
    "PROTEIN": EntityType.CHEMICAL,
    "ORGANISM": EntityType.ORGANISM,
    "ANATOMY": EntityType.ANATOMY,
    "PROCEDURE": EntityType.PROCEDURE,

    # If using en_ner_bc5cdr_md
    "CHEMICAL": EntityType.MEDICATION,  # Override for drug-focused model

    # Standard spaCy labels (fallback)
    "ORG": EntityType.OTHER,
    "PERSON": EntityType.OTHER,
    "GPE": EntityType.OTHER,
    "DATE": EntityType.OTHER,
    "CARDINAL": EntityType.QUANTITY,
    "QUANTITY": EntityType.QUANTITY,
    "PERCENT": EntityType.QUANTITY,
}


class NLPPreprocessor:
    """Orchestrates NLP analysis pipeline for hybrid statement generation.

    Provides the main interface for converting source text into structured
    NLP artifacts that guide LLM statement generation.

    Usage:
        preprocessor = NLPPreprocessor()
        artifacts = preprocessor.process(critique_text, "critique")
        context = preprocessor.generate_prompt_context(artifacts)
    """

    def __init__(self, config: Optional[NLPConfig] = None):
        """Initialize preprocessor with optional config.

        Args:
            config: NLPConfig instance. If None, loads from environment.
        """
        self.config = config or NLPConfig.from_env()
        self._nlp = None  # Lazy-loaded
        self.negation_detector = NegationDetector()
        self.atomicity_analyzer = AtomicityAnalyzer()
        self.fact_generator = FactCandidateGenerator(self.atomicity_analyzer)

    @property
    def nlp(self):
        """Lazy-load spaCy model."""
        if self._nlp is None:
            self._nlp = get_nlp()
            if self._nlp is None:
                raise RuntimeError(
                    "NLP model not available. Check MKSAP_USE_NLP and MKSAP_NLP_MODEL settings."
                )
        return self._nlp

    @property
    def parser_enabled(self) -> bool:
        """Check if dependency parser is enabled."""
        return "parser" not in self.config.disabled_components

    def process(self, text: str, source_field: str) -> NLPArtifacts:
        """Process text through full NLP pipeline.

        Args:
            text: Source text to analyze
            source_field: Field name ("critique", "keypoints", "table")

        Returns:
            NLPArtifacts with sentences, entities, negations, and recommendations
        """
        if not text or not text.strip():
            logger.warning(f"Empty text provided for {source_field}")
            return NLPArtifacts(
                source_text=text or "",
                source_field=source_field,
                model_name=self.config.model,
                parser_enabled=self.parser_enabled,
            )

        logger.debug(f"Processing {source_field} text ({len(text)} chars)")

        # Parse with spaCy
        doc = self.nlp(text)

        # Extract sentences
        sentences = self._extract_sentences(doc)
        logger.debug(f"Extracted {len(sentences)} sentences")

        # Extract entities with negation detection
        entities = self._extract_entities(doc, sentences)
        logger.debug(f"Extracted {len(entities)} entities")

        # Find negation spans for validation
        negation_spans = self.negation_detector.find_negation_spans(doc)

        # Generate split recommendations
        split_recommendations = []
        for sentence in sentences:
            sent_entities = [e for e in entities if e.sentence_index == sentence.index]
            atomicity = self.atomicity_analyzer.analyze_sentence(sentence, sent_entities)

            rec = self.atomicity_analyzer.generate_split_recommendation(
                sentence, sent_entities, atomicity
            )
            if rec:
                split_recommendations.append(rec)

        # Update sentence entity indices
        for sentence in sentences:
            sentence.entity_indices = [
                i for i, e in enumerate(entities)
                if e.sentence_index == sentence.index
            ]

        artifacts = NLPArtifacts(
            source_text=text,
            source_field=source_field,
            sentences=sentences,
            entities=entities,
            negation_spans=negation_spans,
            split_recommendations=split_recommendations,
            model_name=self.config.model,
            parser_enabled=self.parser_enabled,
        )

        logger.info(
            f"NLP analysis complete: {len(sentences)} sentences, "
            f"{len(entities)} entities, {len([e for e in entities if e.is_negated])} negated"
        )

        return artifacts

    def generate_prompt_context(self, artifacts: NLPArtifacts) -> EnrichedPromptContext:
        """Generate enriched prompt context from NLP artifacts.

        Args:
            artifacts: NLPArtifacts from process()

        Returns:
            EnrichedPromptContext ready for LLM prompt injection
        """
        return self.fact_generator.generate(artifacts)

    def process_and_enrich(self, text: str, source_field: str) -> EnrichedPromptContext:
        """Convenience method: process text and generate prompt context in one call.

        Args:
            text: Source text to analyze
            source_field: Field name ("critique", "keypoints", "table")

        Returns:
            EnrichedPromptContext ready for LLM prompt injection
        """
        artifacts = self.process(text, source_field)
        return self.generate_prompt_context(artifacts)

    def _extract_sentences(self, doc) -> List[SentenceSpan]:
        """Extract sentence spans with linguistic features."""
        sentences = []

        for i, sent in enumerate(doc.sents):
            # Count verbs
            verb_count = sum(1 for token in sent if token.pos_ == "VERB")

            # Detect complexity (multiple clauses, conjunctions)
            has_conj = any(token.dep_ in ("conj", "cc") for token in sent)
            has_advcl = any(token.dep_ == "advcl" for token in sent)
            is_complex = verb_count > 1 or has_conj or has_advcl

            # Check for negation
            has_negation = any(
                token.text.lower() in self.negation_detector.NEGATION_TRIGGERS
                for token in sent
            )

            sentences.append(SentenceSpan(
                text=sent.text.strip(),
                start_char=sent.start_char,
                end_char=sent.end_char,
                index=i,
                has_negation=has_negation,
                verb_count=verb_count,
                is_complex=is_complex,
                entity_indices=[],  # Filled in later
            ))

        return sentences

    def _extract_entities(self, doc, sentences: List[SentenceSpan]) -> List[MedicalEntity]:
        """Extract entities with negation and modifier detection."""
        entities = []

        for ent in doc.ents:
            # Find sentence index
            sent_idx = self._find_sentence_index(ent.start_char, sentences)

            # Map entity type
            entity_type = SPACY_LABEL_TO_ENTITY_TYPE.get(ent.label_, EntityType.OTHER)

            # Detect negation
            is_negated, neg_trigger = self.negation_detector.is_negated(
                ent,
                use_dependency_parse=self.parser_enabled
            )

            # Extract modifiers (adjectives before entity)
            modifiers = self._extract_modifiers(ent)

            entities.append(MedicalEntity(
                text=ent.text,
                entity_type=entity_type,
                start_char=ent.start_char,
                end_char=ent.end_char,
                sentence_index=sent_idx,
                is_negated=is_negated,
                negation_trigger=neg_trigger,
                modifiers=modifiers,
                confidence=1.0,  # scispaCy doesn't provide confidence scores
                spacy_label=ent.label_,
            ))

        # Add custom entity detection for quantities/lab values
        custom_entities = self._extract_custom_entities(doc, sentences)
        entities.extend(custom_entities)

        return entities

    def _find_sentence_index(self, char_pos: int, sentences: List[SentenceSpan]) -> int:
        """Find which sentence contains a character position."""
        for sent in sentences:
            if sent.start_char <= char_pos < sent.end_char:
                return sent.index
        return 0  # Default to first sentence

    def _extract_modifiers(self, ent) -> List[str]:
        """Extract adjective modifiers for an entity."""
        modifiers = []

        # Look for adjectives in the entity span
        for token in ent:
            if token.pos_ == "ADJ":
                modifiers.append(token.text.lower())

        # Look for adjectives immediately before the entity
        if ent.start > 0:
            prev_token = ent.doc[ent.start - 1]
            if prev_token.pos_ == "ADJ":
                modifiers.insert(0, prev_token.text.lower())

        return modifiers

    def _extract_custom_entities(self, doc, sentences: List[SentenceSpan]) -> List[MedicalEntity]:
        """Extract custom entities not caught by scispaCy NER.

        Focuses on:
        - Lab values with units (e.g., "250 mg/dL", ">60 mL/min")
        - Numeric thresholds with comparators
        """
        import re

        custom_entities = []

        # Pattern for lab values with units
        lab_pattern = r'([<>≤≥]?\s*\d+(?:\.\d+)?)\s*(mg/dL|mmol/L|mL/min(?:/1\.73\s*m[²2])?|%|mmHg|ng/mL|U/L|g/dL|mcg/dL)'

        for match in re.finditer(lab_pattern, doc.text, re.IGNORECASE):
            start_char = match.start()
            end_char = match.end()
            sent_idx = self._find_sentence_index(start_char, sentences)

            # Check if this span is already covered by an entity
            if not self._is_covered_by_entity(start_char, end_char, doc.ents):
                custom_entities.append(MedicalEntity(
                    text=match.group(0),
                    entity_type=EntityType.QUANTITY,
                    start_char=start_char,
                    end_char=end_char,
                    sentence_index=sent_idx,
                    is_negated=False,
                    negation_trigger=None,
                    modifiers=[],
                    confidence=0.9,
                    spacy_label="CUSTOM_LAB_VALUE",
                ))

        return custom_entities

    def _is_covered_by_entity(self, start: int, end: int, ents) -> bool:
        """Check if a span is already covered by an existing entity."""
        for ent in ents:
            if ent.start_char <= start and end <= ent.end_char:
                return True
        return False
