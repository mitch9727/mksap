"""
Provider manager with automatic fallback support.

Manages multiple LLM providers with automatic fallback when limits are hit.
"""

import logging
from typing import List, Optional

from .config import Config, LLMConfig
from .llm_client import ClaudeClient
from .provider_exceptions import ProviderLimitError

logger = logging.getLogger(__name__)


class ProviderManager:
    """
    Manages multiple LLM providers with fallback support.

    Fallback order:
    1. claude-code (CLI, free with subscription)
    2. codex (CLI/API, OpenAI)
    3. anthropic (API, pay-per-use)
    4. gemini (CLI, if available)
    """

    def __init__(self, config: Config, provider_order: Optional[List[str]] = None):
        """
        Initialize provider manager.

        Args:
            config: Configuration object
            provider_order: Override default provider order (optional)
        """
        self.config = config
        self.provider_order = provider_order or [
            "claude-code",
            "codex",
            "anthropic",
            "gemini",
        ]

        # Start with primary provider
        self.current_provider_index = 0
        self.current_provider_name = self.provider_order[0]

        # Initialize current client
        self.client: Optional[ClaudeClient] = None
        self._initialize_current_provider()

    def _initialize_current_provider(self) -> None:
        """Initialize the current provider client"""
        provider_name = self.current_provider_name

        # Create LLM config for this provider
        try:
            if provider_name == "claude-code":
                llm_config = LLMConfig(
                    provider="claude-code",
                    model=self.config.llm.model
                    if self.config.llm.provider == "claude-code"
                    else "sonnet",
                    temperature=self.config.llm.temperature,
                    cli_path="claude",
                )
            elif provider_name == "anthropic":
                import os

                api_key = os.getenv("ANTHROPIC_API_KEY")
                if not api_key:
                    logger.warning(
                        "ANTHROPIC_API_KEY not set - skipping anthropic provider"
                    )
                    raise ValueError("API key required for anthropic")

                llm_config = LLMConfig(
                    provider="anthropic",
                    api_key=api_key,
                    model="claude-sonnet-4-20250514",
                    temperature=self.config.llm.temperature,
                )
            elif provider_name == "gemini":
                llm_config = LLMConfig(
                    provider="gemini",
                    model="gemini-pro",
                    temperature=self.config.llm.temperature,
                    cli_path="gemini",
                )
            elif provider_name == "codex":
                llm_config = LLMConfig(
                    provider="codex",
                    model="gpt-4",
                    temperature=self.config.llm.temperature,
                    cli_path="openai",
                )
            else:
                raise ValueError(f"Unknown provider: {provider_name}")

            self.client = ClaudeClient(llm_config)
            logger.info(f"Initialized provider: {provider_name}")

        except Exception as e:
            logger.warning(
                f"Failed to initialize {provider_name}: {e}. Trying next provider..."
            )
            if not self._try_next_provider():
                raise RuntimeError("All providers failed to initialize")

    def _try_next_provider(self) -> bool:
        """
        Try to switch to next provider in fallback chain.

        Returns:
            True if switched successfully, False if no more providers
        """
        self.current_provider_index += 1

        if self.current_provider_index >= len(self.provider_order):
            logger.error("No more providers available in fallback chain")
            return False

        self.current_provider_name = self.provider_order[self.current_provider_index]
        logger.info(f"Switching to provider: {self.current_provider_name}")

        try:
            self._initialize_current_provider()
            return True
        except Exception as e:
            logger.error(f"Failed to initialize {self.current_provider_name}: {e}")
            return self._try_next_provider()

    def prompt_user_for_fallback(self) -> bool:
        """
        Ask user if they want to fall back to next provider.

        Returns:
            True if user confirms, False if user declines
        """
        if self.current_provider_index >= len(self.provider_order) - 1:
            print("\n⚠️  No more providers available in fallback chain.")
            return False

        next_provider = self.provider_order[self.current_provider_index + 1]

        print("\n" + "=" * 60)
        print(f"⚠️  PROVIDER LIMIT REACHED: {self.current_provider_name}")
        print(f"   Next provider: {next_provider}")
        print("=" * 60)

        # Add cost/usage info
        if next_provider == "anthropic":
            print("⚠️  Note: Anthropic API is pay-per-use (approximately $0.01-0.02 per question)")
        elif next_provider in ["gemini", "codex"]:
            print(f"ℹ️  Note: {next_provider} may have its own rate limits")

        response = input("\nSwitch to next provider? [y/N]: ").strip().lower()
        return response in ["y", "yes"]

    def generate(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_retries: int = 3,
        allow_fallback: bool = True,
    ) -> str:
        """
        Generate response with automatic fallback on limit errors.

        Args:
            prompt: The prompt to send
            temperature: Override default temperature
            max_retries: Number of retry attempts per provider
            allow_fallback: Allow automatic provider fallback

        Returns:
            Response text from LLM

        Raises:
            ProviderLimitError: If all providers exhausted
            Exception: If generation fails
        """
        while True:
            try:
                if self.client is None:
                    raise RuntimeError("No provider available")

                return self.client.generate(prompt, temperature, max_retries)

            except ProviderLimitError as e:
                logger.warning(f"Provider limit reached: {e}")

                if not allow_fallback:
                    raise

                # Ask user for permission to fallback
                if self.prompt_user_for_fallback():
                    if not self._try_next_provider():
                        raise ProviderLimitError(
                            "all",
                            "All providers exhausted",
                            retryable=False,
                        )
                else:
                    logger.info("User declined provider fallback")
                    raise

            except Exception as e:
                logger.error(f"Generation failed with {self.current_provider_name}: {e}")
                raise

    def get_current_provider(self) -> str:
        """Get name of current provider"""
        return self.current_provider_name

    def get_remaining_providers(self) -> List[str]:
        """Get list of remaining providers in fallback chain"""
        return self.provider_order[self.current_provider_index + 1 :]

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
