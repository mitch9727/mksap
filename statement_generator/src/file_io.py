"""
File I/O operations for reading and writing question JSON files.

Handles discovering questions, reading/writing JSONs, and augmenting with statements.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from .models import TrueStatements

logger = logging.getLogger(__name__)


class QuestionFileIO:
    """Handle reading and writing question JSON files"""

    def __init__(self, mksap_data_path: Path):
        self.mksap_data = mksap_data_path

    def discover_all_questions(self) -> List[Path]:
        """Find all question JSON files"""
        questions = []
        for system_dir in self.mksap_data.iterdir():
            if not system_dir.is_dir():
                continue
            if system_dir.name.startswith("."):
                continue

            for question_dir in system_dir.iterdir():
                if not question_dir.is_dir():
                    continue

                json_file = question_dir / f"{question_dir.name}.json"
                if json_file.exists():
                    questions.append(json_file)

        return sorted(questions)

    def discover_system_questions(self, system: str) -> List[Path]:
        """Find questions for specific system"""
        system_dir = self.mksap_data / system
        if not system_dir.exists():
            raise ValueError(f"System directory not found: {system}")

        questions = []
        for question_dir in system_dir.iterdir():
            if not question_dir.is_dir():
                continue

            json_file = question_dir / f"{question_dir.name}.json"
            if json_file.exists():
                questions.append(json_file)

        return sorted(questions)

    def get_question_path(self, question_id: str) -> Optional[Path]:
        """Find JSON file for specific question ID"""
        # Extract system code (first 2 chars)
        if len(question_id) < 2:
            return None

        system = question_id[:2]
        question_file = self.mksap_data / system / question_id / f"{question_id}.json"

        return question_file if question_file.exists() else None

    def read_question(self, file_path: Path) -> Dict[str, Any]:
        """Read question JSON file"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to read {file_path}: {e}")
            raise

    def has_true_statements(self, data: Dict[str, Any]) -> bool:
        """Check if question already has true_statements"""
        return "true_statements" in data and data["true_statements"]

    def write_question(self, file_path: Path, data: Dict[str, Any]) -> None:
        """Write augmented question JSON (preserve formatting)"""
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to write {file_path}: {e}")
            raise

    def augment_with_statements(
        self, data: Dict[str, Any], true_statements: TrueStatements
    ) -> Dict[str, Any]:
        """Add true_statements to question data"""
        data["true_statements"] = true_statements.model_dump()
        return data
