"""
Base provider interface for LLM providers.

All providers must implement the generate() method.
"""

from abc import ABC, abstractmethod
from typing import Optional


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers"""

    @abstractmethod
    def generate(
        self, prompt: str, temperature: Optional[float] = None, max_retries: int = 3
    ) -> str:
        """
        Generate response from LLM.

        Args:
            prompt: The prompt to send
            temperature: Override default temperature (0.0-1.0)
            max_retries: Number of retry attempts

        Returns:
            Response text from LLM

        Raises:
            Exception: If all retries fail
        """
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """
        Get the name of this provider.

        Returns:
            Provider name (e.g., "anthropic", "claude-code", "gemini", "codex")
        """
        pass
