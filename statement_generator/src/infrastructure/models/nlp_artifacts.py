"""
NLP artifacts data models for hybrid scispaCy pipeline.

Defines Pydantic models for NLP preprocessing outputs:
- MedicalEntity: Named entity with negation and modifier info
- SentenceSpan: Sentence boundary with linguistic features
- SplitRecommendation: How to split complex sentences
- NLPArtifacts: Complete NLP analysis of source text
"""

from enum import Enum
from typing import List, Optional, Tuple

from pydantic import BaseModel, Field


class EntityType(str, Enum):
    """Medical entity types from scispaCy + custom clinical types."""

    # scispaCy entity labels (en_core_sci_sm)
    DISEASE = "DISEASE"
    CHEMICAL = "CHEMICAL"  # Includes medications

    # Custom clinical types for better categorization
    MEDICATION = "MEDICATION"
    PROCEDURE = "PROCEDURE"
    LAB_VALUE = "LAB_VALUE"
    ANATOMY = "ANATOMY"
    ORGANISM = "ORGANISM"

    # Linguistic types
    MODIFIER = "MODIFIER"  # "severe", "acute", "chronic"
    QUANTITY = "QUANTITY"  # "5 mg", ">250", "twice daily"

    # Fallback
    OTHER = "OTHER"


class MedicalEntity(BaseModel):
    """Single entity extracted by scispaCy with negation and modifier info."""

    text: str = Field(..., description="Entity text as it appears in source")
    entity_type: EntityType = Field(..., description="Categorized entity type")
    start_char: int = Field(..., description="Start character offset in source text")
    end_char: int = Field(..., description="End character offset in source text")
    sentence_index: int = Field(..., description="Index of sentence containing entity")

    # Negation info
    is_negated: bool = Field(default=False, description="Whether entity is negated in context")
    negation_trigger: Optional[str] = Field(
        default=None,
        description="Negation word/phrase (e.g., 'no', 'without', 'absence of')"
    )

    # Modifiers
    modifiers: List[str] = Field(
        default_factory=list,
        description="Adjective modifiers (e.g., ['severe', 'acute'])"
    )

    # Confidence (for entity classification)
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Confidence score for entity classification"
    )

    # Original scispaCy label (for debugging)
    spacy_label: Optional[str] = Field(
        default=None,
        description="Original spaCy entity label before mapping"
    )


class SentenceSpan(BaseModel):
    """Sentence boundary with linguistic features for atomicity analysis."""

    text: str = Field(..., description="Full sentence text")
    start_char: int = Field(..., description="Start character offset in source text")
    end_char: int = Field(..., description="End character offset in source text")
    index: int = Field(..., description="Sentence index in source (0-based)")

    # Linguistic features
    has_negation: bool = Field(default=False, description="Contains negation trigger")
    verb_count: int = Field(default=0, description="Number of verbs (for multi-verb detection)")
    is_complex: bool = Field(
        default=False,
        description="Has multiple clauses, conjunctions, or complex structure"
    )

    # Entity references (indices into NLPArtifacts.entities)
    entity_indices: List[int] = Field(
        default_factory=list,
        description="Indices of entities contained in this sentence"
    )


class SplitRecommendation(BaseModel):
    """Recommendation for how to split a complex sentence into atomic statements."""

    sentence_index: int = Field(..., description="Index of sentence to split")
    reason: str = Field(
        ...,
        description="Why splitting is recommended (e.g., 'Multiple diseases', 'Multiple verbs')"
    )
    proposed_splits: List[str] = Field(
        default_factory=list,
        description="Suggested atomic statement texts"
    )
    entity_groups: List[List[int]] = Field(
        default_factory=list,
        description="Entity indices grouped by proposed split"
    )
    confidence: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="Confidence in split recommendation"
    )


class NLPArtifacts(BaseModel):
    """Complete NLP analysis of source text for hybrid pipeline."""

    source_text: str = Field(..., description="Original source text that was analyzed")
    source_field: str = Field(
        ...,
        description="Source field name ('critique', 'keypoints', 'table')"
    )

    # Sentence segmentation
    sentences: List[SentenceSpan] = Field(
        default_factory=list,
        description="Sentence spans with linguistic features"
    )

    # Named entities
    entities: List[MedicalEntity] = Field(
        default_factory=list,
        description="All extracted medical entities"
    )

    # Negation spans (for validation)
    negation_spans: List[Tuple[str, int, int]] = Field(
        default_factory=list,
        description="Negation triggers with char spans: (trigger_text, start, end)"
    )

    # Atomicity recommendations
    split_recommendations: List[SplitRecommendation] = Field(
        default_factory=list,
        description="Recommendations for splitting complex sentences"
    )

    # Processing metadata
    model_name: Optional[str] = Field(
        default=None,
        description="scispaCy model used for analysis (set by preprocessor from config)"
    )
    parser_enabled: bool = Field(
        default=False,
        description="Whether dependency parser was enabled"
    )

    def get_entities_for_sentence(self, sentence_index: int) -> List[MedicalEntity]:
        """Get all entities in a specific sentence."""
        return [e for e in self.entities if e.sentence_index == sentence_index]

    def get_negated_entities(self) -> List[MedicalEntity]:
        """Get all negated entities."""
        return [e for e in self.entities if e.is_negated]

    def get_entities_by_type(self, entity_type: EntityType) -> List[MedicalEntity]:
        """Get entities of a specific type."""
        return [e for e in self.entities if e.entity_type == entity_type]
