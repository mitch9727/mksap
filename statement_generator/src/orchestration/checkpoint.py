"""
Checkpoint system for resumable processing.

Tracks which questions have been processed and which failed.
"""

import json
import logging
from datetime import datetime
from pathlib import Path

from ..infrastructure.models.data_models import CheckpointData

logger = logging.getLogger(__name__)


class CheckpointManager:
    """Manage processing checkpoints for resumability"""

    def __init__(self, checkpoint_path: Path):
        self.checkpoint_file = checkpoint_path / "processed_questions.json"
        self.checkpoint_file.parent.mkdir(parents=True, exist_ok=True)
        self._data = self._load()

    def _load(self) -> CheckpointData:
        """Load checkpoint from disk"""
        if self.checkpoint_file.exists():
            try:
                with open(self.checkpoint_file, "r") as f:
                    data = json.load(f)
                return CheckpointData(**data)
            except Exception as e:
                logger.warning(f"Failed to load checkpoint: {e}. Starting fresh.")

        return CheckpointData()

    def _save(self) -> None:
        """Save checkpoint to disk"""
        self._data.last_updated = datetime.now().isoformat()
        with open(self.checkpoint_file, "w") as f:
            json.dump(self._data.model_dump(), f, indent=2)

    def is_processed(self, question_id: str) -> bool:
        """Check if question already processed"""
        return question_id in self._data.processed_questions

    def mark_processed(self, question_id: str, batch_save: bool = False) -> None:
        """Mark question as processed and clear from failed list"""
        if question_id not in self._data.processed_questions:
            self._data.processed_questions.append(question_id)

        # Clear from failed list if present (question succeeded after previous failure)
        if question_id in self._data.failed_questions:
            self._data.failed_questions.remove(question_id)
            logger.info(f"Cleared {question_id} from failed list (now succeeded)")

        if not batch_save:
            self._save()

    def mark_failed(self, question_id: str) -> None:
        """Mark question as failed"""
        if question_id not in self._data.failed_questions:
            self._data.failed_questions.append(question_id)
        self._save()

    def batch_save(self) -> None:
        """Explicitly save checkpoint (for batch processing)"""
        self._save()

    def get_processed_count(self) -> int:
        """Get count of processed questions"""
        return len(self._data.processed_questions)

    def get_failed_count(self) -> int:
        """Get count of failed questions"""
        return len(self._data.failed_questions)

    def reset(self) -> None:
        """Clear checkpoint (for testing)"""
        self._data = CheckpointData()
        self._save()
        logger.info("Checkpoint reset")
