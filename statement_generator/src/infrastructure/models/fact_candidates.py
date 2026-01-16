"""
Fact candidate data models for hybrid scispaCy pipeline.

Defines Pydantic models for fact candidate generation:
- AtomicityRecommendation: How to handle statement atomicity
- FactCandidate: Structured fact ready for LLM generation
- EnrichedPromptContext: NLP-annotated context for LLM prompts
"""

from enum import Enum
from typing import List, Optional, Tuple

from pydantic import BaseModel, Field

from .nlp_artifacts import MedicalEntity, NLPArtifacts, SentenceSpan, SplitRecommendation


class AtomicityRecommendation(str, Enum):
    """How should a fact be represented in the final output?

    Guides the LLM on whether to keep, split, or enhance a statement.
    """

    ATOMIC_SINGLE = "atomic_single"
    """Simple fact with one entity/concept - keep as single statement."""

    SHOULD_SPLIT = "should_split"
    """Multiple independent facts - split into separate atomic statements."""

    MULTI_CLOZE_OK = "multi_cloze_ok"
    """Related concepts that benefit from being tested together - keep as multi-cloze."""

    COMPLEX_NEEDS_CONTEXT = "complex_needs_context"
    """Complex fact requiring additional clinical context for clarity."""


class FactCandidate(BaseModel):
    """Structured fact candidate ready for LLM statement generation.

    Represents a single factual unit extracted from source text,
    annotated with NLP analysis and atomicity recommendations.
    """

    # Source information
    source_sentence: SentenceSpan = Field(
        ..., description="The sentence this fact came from"
    )
    source_char_span: Tuple[int, int] = Field(
        ..., description="Character span in original text (start, end)"
    )

    # Entity information
    entities: List[MedicalEntity] = Field(
        default_factory=list,
        description="Medical entities involved in this fact"
    )

    # Atomicity
    atomicity: AtomicityRecommendation = Field(
        ..., description="How this fact should be represented"
    )
    split_recommendation: Optional[SplitRecommendation] = Field(
        default=None,
        description="Details on how to split (if atomicity is SHOULD_SPLIT)"
    )

    # Clinical context
    clinical_context: Optional[str] = Field(
        default=None,
        description="Additional clinical context needed for clarity"
    )

    # Confidence
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Confidence in fact extraction"
    )

    def get_entity_texts(self) -> List[str]:
        """Get list of entity text strings."""
        return [e.text for e in self.entities]

    def has_negated_entity(self) -> bool:
        """Check if any entity in this fact is negated."""
        return any(e.is_negated for e in self.entities)

    def get_negation_info(self) -> Optional[str]:
        """Get formatted negation info for prompt injection."""
        negated = [e for e in self.entities if e.is_negated]
        if not negated:
            return None

        parts = []
        for e in negated:
            trigger = e.negation_trigger or "negated"
            parts.append(f"'{e.text}' ({trigger})")
        return ", ".join(parts)


class EnrichedPromptContext(BaseModel):
    """NLP-annotated context for enhanced LLM prompts.

    Provides structured NLP analysis to guide LLM statement generation,
    improving consistency and factual fidelity.
    """

    # Raw source
    source_text: str = Field(..., description="Original source text")
    source_field: str = Field(
        ..., description="Source field name ('critique', 'keypoints', 'table')"
    )

    # NLP analysis
    nlp_artifacts: NLPArtifacts = Field(
        ..., description="Complete NLP analysis of source text"
    )

    # Fact candidates
    fact_candidates: List[FactCandidate] = Field(
        default_factory=list,
        description="Structured fact candidates for LLM generation"
    )

    # Summaries for prompt injection (human-readable)
    entity_summary: str = Field(
        default="",
        description="Summary of found entities (e.g., 'Found 5 diseases, 3 medications')"
    )
    negation_summary: str = Field(
        default="",
        description="Summary of negated findings (e.g., '2 negated: no fever, without rash')"
    )
    atomicity_summary: str = Field(
        default="",
        description="Summary of atomicity recommendations"
    )

    @classmethod
    def create_empty(cls, source_text: str, source_field: str) -> "EnrichedPromptContext":
        """Create an empty context (for when NLP is disabled)."""
        return cls(
            source_text=source_text,
            source_field=source_field,
            nlp_artifacts=NLPArtifacts(
                source_text=source_text,
                source_field=source_field,
            ),
            fact_candidates=[],
            entity_summary="NLP disabled",
            negation_summary="NLP disabled",
            atomicity_summary="NLP disabled",
        )

    def format_for_prompt(self) -> str:
        """Format context as markdown section for LLM prompt injection.

        Returns a formatted string ready to be inserted into LLM prompts.
        """
        if not self.fact_candidates:
            return ""

        lines = [
            "## NLP Analysis",
            "",
            self.entity_summary,
            self.negation_summary if self.negation_summary else "",
            "",
            "### Fact Candidates with Atomicity",
            "",
        ]

        for i, fact in enumerate(self.fact_candidates, 1):
            entities_str = ", ".join(fact.get_entity_texts()) or "none detected"
            lines.append(f"{i}. Sentence: \"{fact.source_sentence.text}\"")
            lines.append(f"   - Entities: {entities_str}")
            lines.append(f"   - Atomicity: {fact.atomicity.value}")

            # Add recommendation based on atomicity
            if fact.atomicity == AtomicityRecommendation.SHOULD_SPLIT:
                if fact.split_recommendation:
                    lines.append(f"   - Recommendation: Split - {fact.split_recommendation.reason}")
                else:
                    lines.append("   - Recommendation: Split into separate statements")
            elif fact.atomicity == AtomicityRecommendation.MULTI_CLOZE_OK:
                lines.append("   - Recommendation: Keep together (related concepts)")
            elif fact.atomicity == AtomicityRecommendation.COMPLEX_NEEDS_CONTEXT:
                context = fact.clinical_context or "Add clinical context"
                lines.append(f"   - Recommendation: {context}")

            # Add negation warning
            neg_info = fact.get_negation_info()
            if neg_info:
                lines.append(f"   - NEGATION: {neg_info}")

            lines.append("")

        # Critical negation handling section
        negated_entities = self.nlp_artifacts.get_negated_entities()
        if negated_entities:
            lines.append("## CRITICAL: Negation Handling")
            lines.append("")
            for e in negated_entities:
                trigger = e.negation_trigger or "negated"
                lines.append(
                    f"'{e.text}' is NEGATED by '{trigger}'. You MUST preserve this negation."
                )
            lines.append("")

        return "\n".join(lines)
