"""
AnKing Analysis Pipeline Data Models

Pydantic models for the entire AnKing analysis pipeline, including:
- Raw card extraction (AnkingCard)
- Structure analysis (CardStructureMetrics)
- Cloze pattern analysis (CardClozeMetrics)
- Context preservation analysis (CardContextMetrics)
- Formatting analysis (CardFormattingMetrics)
- Analysis recommendations (Recommendation)
- Deck sampling (DeckSample)
- Aggregated analysis results (AnalysisReport)

All models use Pydantic BaseModel for validation and serialization.
"""

from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field


class AnkingCard(BaseModel):
    """
    Single extracted AnKing flashcard.

    Represents a raw flashcard extracted from the Anki deck, with all
    original fields and metadata preserved from the SQLite database.
    """
    note_id: int = Field(..., description="Unique note ID from Anki")
    deck_path: str = Field(..., description="Full deck path (e.g., 'MKSAP::Cardiovascular::HF')")
    deck_name: str = Field(..., description="Human-readable deck name")
    text: str = Field(..., description="Front side of card (question/statement with HTML)")
    text_plain: str = Field(..., description="Front side without HTML markup")
    extra: str = Field(..., description="Back side of card (answer/extra info with HTML)")
    extra_plain: str = Field(..., description="Back side without HTML markup")
    cloze_deletions: List[str] = Field(default_factory=list, description="List of cloze deletion patterns found")
    cloze_count: int = Field(..., description="Total number of cloze deletions in the card")
    tags: List[str] = Field(default_factory=list, description="Card tags from Anki")
    html_features: Dict[str, bool] = Field(
        default_factory=dict,
        description="Detected HTML features (bold, italic, lists, tables, etc.)"
    )


class CardStructureMetrics(BaseModel):
    """
    Structure analysis results for a single card.

    Measures structural properties like length, complexity, sentence structure,
    and atomicity (whether the statement tests a single concept).
    """
    card_id: int = Field(..., description="Reference to AnkingCard note_id")
    text_length: int = Field(..., description="Character count of plain text (front)")
    text_word_count: int = Field(..., description="Word count of plain text")
    sentence_count: int = Field(..., description="Number of sentences detected")
    avg_sentence_length: float = Field(..., description="Average words per sentence")
    has_lists: bool = Field(..., description="Whether text contains list markup")
    has_formatting: bool = Field(..., description="Whether text uses bold/italic/other formatting")
    atomicity_score: float = Field(
        ...,
        description="Score 0.0-1.0 measuring whether statement tests single concept"
    )
    compound_indicators: List[str] = Field(
        default_factory=list,
        description="Indicators suggesting compound statements (e.g., 'and', 'but', 'despite')"
    )


class CardClozeMetrics(BaseModel):
    """
    Cloze pattern analysis results for a single card.

    Analyzes cloze deletion patterns including frequency, types, positioning,
    and quality issues like nested or trivial clozes.
    """
    card_id: int = Field(..., description="Reference to AnkingCard note_id")
    cloze_count: int = Field(..., description="Total number of cloze deletions")
    unique_cloze_count: int = Field(..., description="Number of unique cloze patterns")
    cloze_types: List[str] = Field(
        default_factory=list,
        description="Types of clozes detected (e.g., 'deletion', 'formatting', 'nested')"
    )
    avg_cloze_length: float = Field(..., description="Average length of cloze deletions")
    cloze_positions: List[int] = Field(
        default_factory=list,
        description="Character positions of cloze deletions in text"
    )
    has_nested_clozes: bool = Field(..., description="Whether any clozes are nested/overlapping")
    has_trivial_clozes: bool = Field(
        ...,
        description="Whether any clozes are trivial (single letter, punctuation, etc.)"
    )


class CardContextMetrics(BaseModel):
    """
    Context preservation analysis for a single card.

    Measures how well clinical context is preserved and whether the extra field
    provides necessary background information.
    """
    card_id: int = Field(..., description="Reference to AnkingCard note_id")
    has_extra_field: bool = Field(..., description="Whether extra field is present and non-empty")
    extra_field_length: int = Field(..., description="Character count of extra field")
    requires_extra: bool = Field(
        ...,
        description="Whether understanding the front requires reading the extra field"
    )
    context_embedded: bool = Field(
        ...,
        description="Whether sufficient context is embedded in the front text"
    )
    context_types: List[str] = Field(
        default_factory=list,
        description="Types of context found (e.g., 'clinical', 'diagnostic', 'therapeutic')"
    )


class CardFormattingMetrics(BaseModel):
    """
    Formatting and readability analysis for a single card.

    Measures use of formatting (bold, italic, lists, tables) and readability features.
    """
    card_id: int = Field(..., description="Reference to AnkingCard note_id")
    uses_bold: bool = Field(..., description="Whether text uses bold markup")
    uses_italic: bool = Field(..., description="Whether text uses italic markup")
    uses_lists: bool = Field(..., description="Whether text contains bullet/numbered lists")
    uses_tables: bool = Field(..., description="Whether text contains table markup")
    markdown_compatible: bool = Field(
        ...,
        description="Whether card can be represented in Markdown"
    )
    emphasis_count: int = Field(
        ...,
        description="Total number of emphasized elements (bold, italic, etc.)"
    )
    has_clear_hierarchy: bool = Field(
        ...,
        description="Whether formatting creates clear visual hierarchy"
    )


class Recommendation(BaseModel):
    """
    Single actionable recommendation for statement_generator improvement.

    Represents a prioritized improvement suggestion with supporting evidence
    and estimated effort to implement.
    """
    priority: str = Field(
        ...,
        description="Priority level: 'high', 'medium', or 'low'"
    )
    category: str = Field(
        ...,
        description="Recommendation category: 'structure', 'cloze', 'context', or 'formatting'"
    )
    finding: str = Field(..., description="Description of the problem/pattern found")
    mksap_current: str = Field(
        ...,
        description="How current MKSAP statement_generator handles this"
    )
    recommendation: str = Field(
        ...,
        description="Recommended approach or change"
    )
    target_files: List[str] = Field(
        default_factory=list,
        description="Files in statement_generator that would need modification"
    )
    code_snippet: Optional[str] = Field(
        default=None,
        description="Optional code example showing recommended approach"
    )
    expected_impact: str = Field(
        ...,
        description="Expected impact on quality/usability if implemented"
    )
    effort_estimate: str = Field(
        ...,
        description="Estimated effort to implement: 'low', 'medium', or 'high'"
    )


class DeckSample(BaseModel):
    """
    Sample of cards extracted from a single deck.

    Groups cards that were extracted from the same AnKing deck, with metadata
    about the sampling method and deck characteristics.
    """
    deck_path: str = Field(..., description="Full deck path (e.g., 'MKSAP::Cardiovascular')")
    deck_name: str = Field(..., description="Human-readable deck name")
    total_cards: int = Field(..., description="Total number of cards in deck")
    sampled_cards: int = Field(..., description="Number of cards included in sample")
    sampling_method: str = Field(
        ...,
        description="Sampling method used (e.g., 'random', 'first_n', 'systematic')"
    )
    cards: List[AnkingCard] = Field(
        default_factory=list,
        description="List of AnkingCard objects in this sample"
    )


class AnalysisReport(BaseModel):
    """
    Complete analysis results across all sampled cards.

    Aggregated analysis report containing structure, cloze, context, and formatting
    metrics across all analyzed cards, plus comparison with MKSAP data.
    """
    total_cards_analyzed: int = Field(..., description="Total number of cards analyzed")
    decks_sampled: int = Field(..., description="Number of unique decks sampled")
    structure: Dict[str, Any] = Field(
        ...,
        description="Aggregated structure metrics (min, max, avg, std dev)"
    )
    cloze: Dict[str, Any] = Field(
        ...,
        description="Aggregated cloze metrics"
    )
    context: Dict[str, Any] = Field(
        ...,
        description="Aggregated context metrics"
    )
    formatting: Dict[str, Any] = Field(
        ...,
        description="Aggregated formatting metrics"
    )
    deck_metrics: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Per-deck analysis summaries"
    )
    mksap_comparison: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Comparison analysis between AnKing and MKSAP statement_generator output"
    )
