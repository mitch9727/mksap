"""
Fact candidate generation from NLP artifacts.

Converts NLP analysis (sentences, entities, negations) into structured
fact candidates with atomicity recommendations for LLM prompts.
"""

from typing import List

from ...infrastructure.models.nlp_artifacts import (
    EntityType,
    MedicalEntity,
    NLPArtifacts,
    SentenceSpan,
)
from ...infrastructure.models.fact_candidates import (
    AtomicityRecommendation,
    EnrichedPromptContext,
    FactCandidate,
)
from .atomicity_analyzer import AtomicityAnalyzer


class FactCandidateGenerator:
    """Generate structured fact candidates from NLP artifacts.

    Converts NLPArtifacts into FactCandidate objects with:
    - Atomicity recommendations (split vs multi-cloze)
    - Clinical context suggestions
    - Entity and negation summaries for prompt injection
    """

    def __init__(self, atomicity_analyzer: AtomicityAnalyzer = None):
        """Initialize generator with optional atomicity analyzer.

        Args:
            atomicity_analyzer: AtomicityAnalyzer instance (created if None)
        """
        self.atomicity_analyzer = atomicity_analyzer or AtomicityAnalyzer()

    def generate(self, nlp_artifacts: NLPArtifacts) -> EnrichedPromptContext:
        """Generate enriched prompt context from NLP artifacts.

        Args:
            nlp_artifacts: Complete NLP analysis of source text

        Returns:
            EnrichedPromptContext with fact candidates and summaries
        """
        fact_candidates = []

        for sentence in nlp_artifacts.sentences:
            # Get entities for this sentence
            sentence_entities = nlp_artifacts.get_entities_for_sentence(sentence.index)

            # Analyze atomicity
            atomicity = self.atomicity_analyzer.analyze_sentence(
                sentence, sentence_entities
            )

            # Generate split recommendation if needed
            split_rec = self.atomicity_analyzer.generate_split_recommendation(
                sentence, sentence_entities, atomicity
            )

            # Get clinical context suggestion if needed
            clinical_context = None
            if atomicity == AtomicityRecommendation.COMPLEX_NEEDS_CONTEXT:
                clinical_context = self.atomicity_analyzer.get_clinical_context_suggestion(
                    sentence_entities
                )

            # Create fact candidate
            fact_candidate = FactCandidate(
                source_sentence=sentence,
                source_char_span=(sentence.start_char, sentence.end_char),
                entities=sentence_entities,
                atomicity=atomicity,
                split_recommendation=split_rec,
                clinical_context=clinical_context,
                confidence=self._calculate_confidence(sentence, sentence_entities),
            )

            fact_candidates.append(fact_candidate)

        # Generate summaries
        entity_summary = self._generate_entity_summary(nlp_artifacts.entities)
        negation_summary = self._generate_negation_summary(nlp_artifacts.entities)
        atomicity_summary = self._generate_atomicity_summary(fact_candidates)

        return EnrichedPromptContext(
            source_text=nlp_artifacts.source_text,
            source_field=nlp_artifacts.source_field,
            nlp_artifacts=nlp_artifacts,
            fact_candidates=fact_candidates,
            entity_summary=entity_summary,
            negation_summary=negation_summary,
            atomicity_summary=atomicity_summary,
        )

    def _calculate_confidence(
        self,
        sentence: SentenceSpan,
        entities: List[MedicalEntity]
    ) -> float:
        """Calculate confidence score for fact candidate.

        Higher confidence for:
        - Sentences with clear entity boundaries
        - Simpler sentence structures
        - High-confidence entities
        """
        if not entities:
            return 0.5  # No entities = uncertain

        # Start with average entity confidence
        avg_entity_conf = sum(e.confidence for e in entities) / len(entities)

        # Adjust for sentence complexity
        if sentence.is_complex:
            avg_entity_conf *= 0.9

        # Adjust for verb count
        if sentence.verb_count > 2:
            avg_entity_conf *= 0.85

        return min(1.0, max(0.0, avg_entity_conf))

    def _generate_entity_summary(self, entities: List[MedicalEntity]) -> str:
        """Generate human-readable entity summary for prompt injection."""
        if not entities:
            return "No medical entities detected."

        # Count by type
        type_counts: dict[EntityType, int] = {}
        for entity in entities:
            type_counts[entity.entity_type] = type_counts.get(entity.entity_type, 0) + 1

        # Format as readable string
        parts = []
        type_names = {
            EntityType.DISEASE: "diseases",
            EntityType.MEDICATION: "medications",
            EntityType.CHEMICAL: "chemicals",
            EntityType.PROCEDURE: "procedures",
            EntityType.LAB_VALUE: "lab values",
            EntityType.ANATOMY: "anatomical terms",
            EntityType.ORGANISM: "organisms",
            EntityType.QUANTITY: "quantities",
            EntityType.MODIFIER: "modifiers",
            EntityType.OTHER: "other entities",
        }

        for entity_type, count in sorted(type_counts.items(), key=lambda x: -x[1]):
            name = type_names.get(entity_type, entity_type.value)
            parts.append(f"{count} {name}")

        return f"Found {', '.join(parts)}."

    def _generate_negation_summary(self, entities: List[MedicalEntity]) -> str:
        """Generate summary of negated entities for prompt injection."""
        negated = [e for e in entities if e.is_negated]

        if not negated:
            return ""

        parts = []
        for entity in negated:
            trigger = entity.negation_trigger or "negated"
            parts.append(f"'{entity.text}' ({trigger})")

        count = len(negated)
        findings = "finding" if count == 1 else "findings"
        return f"{count} negated {findings}: {', '.join(parts)}"

    def _generate_atomicity_summary(self, candidates: List[FactCandidate]) -> str:
        """Generate summary of atomicity recommendations."""
        if not candidates:
            return ""

        counts = {rec: 0 for rec in AtomicityRecommendation}
        for candidate in candidates:
            counts[candidate.atomicity] += 1

        parts = []

        split_count = counts[AtomicityRecommendation.SHOULD_SPLIT]
        if split_count > 0:
            parts.append(f"{split_count} sentence(s) should split")

        multi_count = counts[AtomicityRecommendation.MULTI_CLOZE_OK]
        if multi_count > 0:
            parts.append(f"{multi_count} multi-cloze candidate(s)")

        atomic_count = counts[AtomicityRecommendation.ATOMIC_SINGLE]
        if atomic_count > 0:
            parts.append(f"{atomic_count} simple atomic")

        complex_count = counts[AtomicityRecommendation.COMPLEX_NEEDS_CONTEXT]
        if complex_count > 0:
            parts.append(f"{complex_count} need(s) context")

        if not parts:
            return ""

        return f"Atomicity: {', '.join(parts)}."
