"""
Atomicity analysis for statement generation.

Determines whether sentences should be:
- Split into multiple atomic statements (SHOULD_SPLIT)
- Kept as multi-cloze statements (MULTI_CLOZE_OK)
- Kept as simple atomic statements (ATOMIC_SINGLE)
- Enhanced with clinical context (COMPLEX_NEEDS_CONTEXT)
"""

from typing import List, Optional

from ...infrastructure.models.nlp_artifacts import (
    EntityType,
    MedicalEntity,
    SentenceSpan,
    SplitRecommendation,
)
from ...infrastructure.models.fact_candidates import AtomicityRecommendation


class AtomicityAnalyzer:
    """Analyze sentences to determine optimal atomicity for flashcard generation.

    Rules:
    1. Multiple independent diseases → SHOULD_SPLIT
    2. Related concepts (medication + mechanism/indication) → MULTI_CLOZE_OK
    3. Clinically-significant modifiers (dose + frequency) → MULTI_CLOZE_OK
    4. Multiple verbs with different subjects → SHOULD_SPLIT
    5. Single entity, simple structure → ATOMIC_SINGLE
    6. Complex multi-clause sentences → COMPLEX_NEEDS_CONTEXT

    User Requirement: Help determine "when atomicity is needed, but also when
    more complex, multi-cloze deletion style statements may be more beneficial"
    """

    # Entity types that are typically independent (split when multiple)
    INDEPENDENT_ENTITY_TYPES = frozenset({
        EntityType.DISEASE,
        EntityType.PROCEDURE,
    })

    # Entity type pairs that are clinically related (keep together)
    RELATED_ENTITY_PAIRS = [
        # (type1, type2) - keep statements with both types together
        (EntityType.MEDICATION, EntityType.DISEASE),  # Drug treats disease
        (EntityType.MEDICATION, EntityType.CHEMICAL),  # Drug mechanism
        (EntityType.LAB_VALUE, EntityType.QUANTITY),  # Lab with threshold
        (EntityType.DISEASE, EntityType.LAB_VALUE),  # Disease with diagnostic criteria
        (EntityType.MEDICATION, EntityType.QUANTITY),  # Drug with dose
    ]

    # Minimum entities to consider splitting
    MIN_ENTITIES_FOR_SPLIT = 2

    # Maximum verb count before considering complex
    MAX_SIMPLE_VERBS = 1

    def analyze_sentence(
        self,
        sentence: SentenceSpan,
        entities: List[MedicalEntity]
    ) -> AtomicityRecommendation:
        """Determine atomicity recommendation for a sentence.

        Args:
            sentence: SentenceSpan with linguistic features
            entities: List of MedicalEntity objects in this sentence

        Returns:
            AtomicityRecommendation enum value
        """
        # No entities or single entity → simple atomic
        if len(entities) <= 1:
            return AtomicityRecommendation.ATOMIC_SINGLE

        # Check for multiple independent entities (should split)
        if self._has_multiple_independent_entities(entities):
            return AtomicityRecommendation.SHOULD_SPLIT

        # Check for related entity pairs (keep together)
        if self._has_related_entity_pair(entities):
            return AtomicityRecommendation.MULTI_CLOZE_OK

        # Multi-verb sentences with multiple entities → likely should split
        if sentence.verb_count > self.MAX_SIMPLE_VERBS and len(entities) >= 2:
            return AtomicityRecommendation.SHOULD_SPLIT

        # Complex sentence structure → needs context
        if sentence.is_complex and len(entities) >= 2:
            return AtomicityRecommendation.COMPLEX_NEEDS_CONTEXT

        # Default: multiple entities with no clear pattern → keep together
        return AtomicityRecommendation.MULTI_CLOZE_OK

    def _has_multiple_independent_entities(self, entities: List[MedicalEntity]) -> bool:
        """Check if sentence has multiple independent entities that should be split."""
        independent_count = {}

        for entity in entities:
            if entity.entity_type in self.INDEPENDENT_ENTITY_TYPES:
                independent_count[entity.entity_type] = (
                    independent_count.get(entity.entity_type, 0) + 1
                )

        # Multiple diseases or multiple procedures → split
        for entity_type, count in independent_count.items():
            if count >= self.MIN_ENTITIES_FOR_SPLIT:
                return True

        return False

    def _has_related_entity_pair(self, entities: List[MedicalEntity]) -> bool:
        """Check if sentence has a clinically related entity pair."""
        entity_types = {e.entity_type for e in entities}

        for type1, type2 in self.RELATED_ENTITY_PAIRS:
            if type1 in entity_types and type2 in entity_types:
                return True

        return False

    def generate_split_recommendation(
        self,
        sentence: SentenceSpan,
        entities: List[MedicalEntity],
        atomicity: AtomicityRecommendation
    ) -> Optional[SplitRecommendation]:
        """Generate detailed split recommendation for SHOULD_SPLIT sentences.

        Args:
            sentence: The sentence to potentially split
            entities: Entities in the sentence
            atomicity: The atomicity recommendation

        Returns:
            SplitRecommendation if atomicity is SHOULD_SPLIT, None otherwise
        """
        if atomicity != AtomicityRecommendation.SHOULD_SPLIT:
            return None

        # Determine reason for split
        reason = self._determine_split_reason(entities, sentence)

        # Group entities by type for proposed splits
        entity_groups = self._group_entities_for_split(entities)

        # Generate proposed split texts (simplified - LLM will refine)
        proposed_splits = self._generate_proposed_splits(sentence, entity_groups)

        return SplitRecommendation(
            sentence_index=sentence.index,
            reason=reason,
            proposed_splits=proposed_splits,
            entity_groups=[[i for i, e in enumerate(entities) if e in group]
                          for group in entity_groups],
            confidence=0.7,  # Conservative confidence for rule-based splits
        )

    def _determine_split_reason(
        self,
        entities: List[MedicalEntity],
        sentence: SentenceSpan
    ) -> str:
        """Determine why a sentence should be split."""
        # Count entity types
        type_counts = {}
        for e in entities:
            type_counts[e.entity_type] = type_counts.get(e.entity_type, 0) + 1

        # Multiple diseases
        if type_counts.get(EntityType.DISEASE, 0) >= 2:
            return "Multiple independent diseases"

        # Multiple procedures
        if type_counts.get(EntityType.PROCEDURE, 0) >= 2:
            return "Multiple independent procedures"

        # Multiple medications without clear relationship
        if type_counts.get(EntityType.MEDICATION, 0) >= 2:
            return "Multiple medications (consider splitting unless comparing)"

        # Multi-verb
        if sentence.verb_count > 1:
            return "Multiple verbs with different subjects"

        return "Multiple independent facts"

    def _group_entities_for_split(
        self,
        entities: List[MedicalEntity]
    ) -> List[List[MedicalEntity]]:
        """Group entities into logical units for splitting.

        Groups related entities together (e.g., medication + its dose).
        """
        groups: List[List[MedicalEntity]] = []
        used = set()

        # First pass: group related pairs
        for i, e1 in enumerate(entities):
            if i in used:
                continue

            group = [e1]
            used.add(i)

            # Find related entities
            for j, e2 in enumerate(entities):
                if j in used:
                    continue

                if self._are_entities_related(e1, e2):
                    group.append(e2)
                    used.add(j)

            groups.append(group)

        # Add any remaining entities as single groups
        for i, e in enumerate(entities):
            if i not in used:
                groups.append([e])

        return groups

    def _are_entities_related(self, e1: MedicalEntity, e2: MedicalEntity) -> bool:
        """Check if two entities are clinically related and should stay together."""
        pair = (e1.entity_type, e2.entity_type)
        reverse_pair = (e2.entity_type, e1.entity_type)

        for related_pair in self.RELATED_ENTITY_PAIRS:
            if pair == related_pair or reverse_pair == related_pair:
                return True

        return False

    def _generate_proposed_splits(
        self,
        sentence: SentenceSpan,
        entity_groups: List[List[MedicalEntity]]
    ) -> List[str]:
        """Generate proposed split texts.

        Note: These are simplified suggestions. The LLM will generate
        the final properly-phrased statements.
        """
        if len(entity_groups) <= 1:
            return [sentence.text]

        # Simple approach: suggest one statement per entity group
        splits = []
        for group in entity_groups:
            entity_names = [e.text for e in group]
            splits.append(f"[Statement about: {', '.join(entity_names)}]")

        return splits

    def get_clinical_context_suggestion(
        self,
        entities: List[MedicalEntity]
    ) -> Optional[str]:
        """Suggest clinical context for COMPLEX_NEEDS_CONTEXT sentences.

        Returns:
            Suggested clinical context string, or None
        """
        # Find medication entities
        medications = [e for e in entities if e.entity_type == EntityType.MEDICATION]
        diseases = [e for e in entities if e.entity_type == EntityType.DISEASE]

        if medications and not diseases:
            return "Add indication or mechanism of action"

        if diseases and not medications:
            return "Add diagnostic criteria or treatment context"

        if len(entities) > 3:
            return "Consider which entities are most testable"

        return None
