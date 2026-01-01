"""
Data models for statement generator.

Defines Pydantic models for statements, processing results, and checkpoints.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class Statement(BaseModel):
    """Single extracted statement with cloze candidates"""

    statement: str = Field(..., description="Single sentence or brief question + list")
    extra_field: Optional[str] = Field(
        None, description="Clinical context (why this matters) - null if not in source"
    )
    cloze_candidates: List[str] = Field(
        default_factory=list, description="Testable terms/phrases"
    )


class TrueStatements(BaseModel):
    """Container for all extracted statements"""

    from_critique: List[Statement] = Field(default_factory=list)
    from_key_points: List[Statement] = Field(default_factory=list)


class QuestionData(BaseModel):
    """Subset of question JSON fields we read"""

    question_id: str
    category: str
    critique: str
    key_points: List[str]
    educational_objective: Optional[str] = None

    class Config:
        # Allow extra fields (preserve all other question data)
        extra = "allow"


class ProcessingResult(BaseModel):
    """Result of processing a single question"""

    question_id: str
    success: bool
    statements_extracted: int
    error: Optional[str] = None
    api_calls: int = 0


class CheckpointData(BaseModel):
    """Resume checkpoint state"""

    processed_questions: List[str] = Field(default_factory=list)
    failed_questions: List[str] = Field(default_factory=list)
    last_updated: str = Field(
        default_factory=lambda: datetime.now().isoformat()
    )
