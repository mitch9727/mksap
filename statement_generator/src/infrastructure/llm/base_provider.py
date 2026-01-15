"""
Enhanced base provider interface with retry, rate limiting, and monitoring.

All LLM providers must implement this interface.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import time
import logging

logger = logging.getLogger(__name__)


class BaseLLMProvider(ABC):
    """
    Abstract base class for LLM providers.

    Provides common functionality for retries, rate limiting, and monitoring.
    """

    def __init__(self, model: str, temperature: float = 0.2):
        """
        Initialize provider.

        Args:
            model: Model name/identifier
            temperature: Default temperature (0.0-1.0)
        """
        self.model = model
        self.default_temperature = temperature
        self._call_count = 0
        self._total_tokens = 0

    @abstractmethod
    def _generate_impl(
        self,
        prompt: str,
        temperature: float,
        **kwargs
    ) -> str:
        """
        Provider-specific generation implementation.

        This method must be implemented by all providers.

        Args:
            prompt: The prompt to send
            temperature: Temperature for generation
            **kwargs: Provider-specific parameters

        Returns:
            Response text from LLM

        Raises:
            Exception: If generation fails
        """
        pass

    def generate(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_retries: int = 3,
        **kwargs
    ) -> str:
        """
        Generate response with automatic retry and monitoring.

        Args:
            prompt: The prompt to send
            temperature: Override default temperature
            max_retries: Number of retry attempts
            **kwargs: Provider-specific parameters

        Returns:
            Response text from LLM

        Raises:
            Exception: If all retries fail
        """
        temp = temperature if temperature is not None else self.default_temperature

        last_exception = None
        for attempt in range(max_retries):
            try:
                response = self._generate_impl(prompt, temp, **kwargs)
                self._call_count += 1
                logger.debug(
                    f"{self.get_provider_name()}: Call #{self._call_count} succeeded"
                )
                return response

            except Exception as e:
                last_exception = e
                logger.warning(
                    f"{self.get_provider_name()}: Attempt {attempt + 1}/{max_retries} failed: {e}"
                )

                if attempt < max_retries - 1:
                    delay = 2 ** attempt  # Exponential backoff
                    logger.info(f"Retrying in {delay}s...")
                    time.sleep(delay)

        logger.error(
            f"{self.get_provider_name()}: All {max_retries} attempts failed"
        )
        raise last_exception

    @abstractmethod
    def get_provider_name(self) -> str:
        """
        Get the name of this provider.

        Returns:
            Provider name (e.g., "anthropic", "claude-code")
        """
        pass

    def get_stats(self) -> Dict[str, Any]:
        """
        Get provider usage statistics.

        Returns:
            Dictionary with call count and other metrics
        """
        return {
            "provider": self.get_provider_name(),
            "model": self.model,
            "call_count": self._call_count,
            "total_tokens": self._total_tokens,
        }
