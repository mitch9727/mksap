"""
Provider manager without automatic fallback.

Uses the configured LLM provider and surfaces any errors to the caller.
"""

import logging
from typing import Optional

from .infrastructure.config.settings import Config
from .infrastructure.llm.client import ClaudeClient

logger = logging.getLogger(__name__)


class ProviderManager:
    """
    Manages a single configured LLM provider.
    """

    def __init__(self, config: Config):
        """
        Initialize provider manager.

        Args:
            config: Configuration object
        """
        self.config = config
        self.client: Optional[ClaudeClient] = ClaudeClient(config.llm)
        self.current_provider_name = config.llm.provider
        logger.info(f"Initialized provider: {self.current_provider_name}")

    def generate(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_retries: int = 3,
    ) -> str:
        """
        Generate response using the configured provider.

        Args:
            prompt: The prompt to send
            temperature: Override default temperature
            max_retries: Number of retry attempts per provider
        Returns:
            Response text from LLM

        Raises:
            Exception: If generation fails
        """
        if self.client is None:
            raise RuntimeError("No provider available")

        return self.client.generate(prompt, temperature, max_retries)

    def get_current_provider(self) -> str:
        """Get name of current provider"""
        return self.current_provider_name

    def parse_json_response(self, response: str) -> dict:
        """
        Parse JSON response from LLM (delegate to client).

        Args:
            response: Raw LLM response text

        Returns:
            Parsed JSON dict

        Raises:
            ValueError: If response is not valid JSON
        """
        if self.client is None:
            raise RuntimeError("No client available")
        return self.client.parse_json_response(response)
