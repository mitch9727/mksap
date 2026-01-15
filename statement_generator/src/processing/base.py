"""
Base processor interface for all statement extraction stages.

Provides consistent interface for extraction, validation, and error handling.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional, Generic, TypeVar, Any

T = TypeVar('T')  # Return type for extraction


class BaseProcessor(ABC, Generic[T]):
    """
    Abstract base class for all processors.

    Processors extract or transform data using LLM calls.
    All processors must implement extract() method.
    """

    def __init__(self, client: Any, prompt_path: Optional[Path] = None):
        """
        Initialize processor.

        Args:
            client: LLM client for API calls
            prompt_path: Path to prompt template file (optional)
        """
        self.client = client
        self.prompt_template = None
        if prompt_path:
            self.prompt_template = self._load_prompt(prompt_path)

    def _load_prompt(self, path: Path) -> str:
        """Load prompt template from file."""
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    @abstractmethod
    def extract(self, *args, **kwargs) -> T:
        """
        Extract data from input.

        This method must be implemented by all subclasses.

        Returns:
            Extracted data (type varies by processor)
        """
        pass

    def _call_llm(self, prompt: str, description: str = "") -> str:
        """
        Call LLM with error handling.

        Args:
            prompt: Formatted prompt string
            description: Description for logging

        Returns:
            LLM response text
        """
        import logging
        logger = logging.getLogger(self.__class__.__name__)
        logger.debug(f"Calling LLM: {description}")
        return self.client.generate(prompt)

    def _parse_json_response(self, response: str) -> dict:
        """
        Parse JSON from LLM response.

        Args:
            response: Raw LLM response

        Returns:
            Parsed JSON dictionary
        """
        return self.client.parse_json_response(response)


class StatementExtractor(BaseProcessor[List[Any]]):
    """
    Base class for statement extraction processors.

    Specialized for processors that extract Statement objects.
    """

    @abstractmethod
    def extract(self, *args, **kwargs) -> List[Any]:
        """
        Extract statements from source data.

        Returns:
            List of Statement objects
        """
        pass


class StatementTransformer(BaseProcessor[List[Any]]):
    """
    Base class for statement transformation processors.

    Specialized for processors that transform existing statements.
    """

    @abstractmethod
    def transform(self, statements: List[Any]) -> List[Any]:
        """
        Transform existing statements.

        Args:
            statements: Input statements

        Returns:
            Transformed statements
        """
        pass
