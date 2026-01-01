"""
LLM client wrapper with multi-provider support.

Handles API/CLI calls with retry logic and JSON response parsing.
Supports: Anthropic API, Claude Code CLI, Gemini CLI, Codex CLI
"""

import json
import logging
import re
from typing import Any, Dict

from .config import LLMConfig
from .providers import (
    AnthropicProvider,
    BaseLLMProvider,
    ClaudeCodeProvider,
    CodexProvider,
    GeminiProvider,
)

logger = logging.getLogger(__name__)


class ClaudeClient:
    """
    Multi-provider LLM client wrapper.

    Supports multiple providers:
    - anthropic: Anthropic API (requires API key)
    - claude-code: Claude Code CLI (uses existing subscription)
    - gemini: Google Gemini CLI (uses existing subscription)
    - codex: OpenAI CLI (uses existing subscription)
    """

    def __init__(self, config: LLMConfig):
        """
        Initialize LLM client with provider.

        Args:
            config: LLM configuration

        Raises:
            ValueError: If provider is unsupported
        """
        self.config = config
        self.provider = self._create_provider(config)
        logger.info(f"Initialized {self.provider.get_provider_name()} provider")

    def _create_provider(self, config: LLMConfig) -> BaseLLMProvider:
        """
        Create provider instance based on config.

        Args:
            config: LLM configuration

        Returns:
            Provider instance

        Raises:
            ValueError: If provider is unsupported
        """
        if config.provider == "anthropic":
            if not config.api_key:
                raise ValueError("ANTHROPIC_API_KEY required for anthropic provider")
            return AnthropicProvider(
                api_key=config.api_key,
                model=config.model,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
                timeout=config.timeout,
            )

        elif config.provider == "claude-code":
            return ClaudeCodeProvider(
                model=config.model,
                temperature=config.temperature,
                cli_path=config.cli_path or "claude",
            )

        elif config.provider == "gemini":
            return GeminiProvider(
                model=config.model,
                temperature=config.temperature,
                cli_path=config.cli_path or "gemini",
            )

        elif config.provider == "codex":
            return CodexProvider(
                model=config.model,
                temperature=config.temperature,
                cli_path=config.cli_path or "openai",
            )

        else:
            raise ValueError(
                f"Unsupported provider: {config.provider}. "
                "Supported: anthropic, claude-code, gemini, codex"
            )

    def generate(
        self, prompt: str, temperature: float = None, max_retries: int = 3
    ) -> str:
        """
        Generate response with automatic retry.

        Args:
            prompt: The prompt to send
            temperature: Override default temperature
            max_retries: Number of retry attempts

        Returns:
            Response text from LLM

        Raises:
            Exception: If all retries fail
        """
        return self.provider.generate(prompt, temperature, max_retries)

    def parse_json_response(self, response: str) -> Dict[str, Any]:
        """
        Parse JSON from LLM response (handle markdown code blocks).

        Args:
            response: Raw LLM response

        Returns:
            Parsed JSON dictionary

        Raises:
            json.JSONDecodeError: If parsing fails
        """
        # Remove markdown code blocks if present
        cleaned = re.sub(r"```json\s*", "", response)
        cleaned = re.sub(r"```\s*$", "", cleaned)
        cleaned = cleaned.strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.debug(f"Response was: {response}")
            raise
