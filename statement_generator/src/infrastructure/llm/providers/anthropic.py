"""
Anthropic API provider (existing implementation).

Uses the Anthropic API directly with API key authentication.
"""

import logging
import time
from typing import Optional

from anthropic import Anthropic, RateLimitError, AuthenticationError

from ..base_provider import BaseLLMProvider
from ..exceptions import ProviderLimitError, ProviderAuthError

logger = logging.getLogger(__name__)


class AnthropicProvider(BaseLLMProvider):
    """Provider for Anthropic API (direct API calls)"""

    def __init__(
        self,
        api_key: str,
        model: str = "claude-sonnet-4-20250514",
        temperature: float = 0.2,
        max_tokens: int = 4096,
        timeout: int = 60,
    ):
        """
        Initialize Anthropic provider.

        Args:
            api_key: Anthropic API key
            model: Claude model name
            temperature: Default temperature (0.0-1.0)
            max_tokens: Maximum tokens in response
            timeout: API timeout in seconds
        """
        self.api_key = api_key
        self.model = model
        self.default_temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.client = Anthropic(api_key=api_key)

    def generate(
        self, prompt: str, temperature: Optional[float] = None, max_retries: int = 3
    ) -> str:
        """Generate response using Anthropic API"""
        temperature = temperature if temperature is not None else self.default_temperature

        for attempt in range(max_retries):
            try:
                message = self.client.messages.create(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    temperature=temperature,
                    messages=[{"role": "user", "content": prompt}],
                )

                response_text = message.content[0].text
                logger.debug(
                    f"Anthropic API response ({len(response_text)} chars): {response_text[:200]}..."
                )

                return response_text

            except RateLimitError as e:
                logger.warning("Anthropic API rate limit reached")
                raise ProviderLimitError(
                    "anthropic",
                    "Rate limit exceeded. Consider upgrading your plan or waiting.",
                    retryable=False,
                )

            except AuthenticationError as e:
                logger.error("Anthropic API authentication failed")
                raise ProviderAuthError(
                    "anthropic",
                    "Invalid API key. Please check ANTHROPIC_API_KEY.",
                )

            except Exception as e:
                logger.warning(
                    f"Anthropic API call failed (attempt {attempt + 1}/{max_retries}): {e}"
                )

                # Check for budget/quota errors in message
                error_str = str(e).lower()
                if "quota" in error_str or "budget" in error_str or "limit" in error_str:
                    raise ProviderLimitError(
                        "anthropic",
                        f"Usage limit exceeded: {e}",
                        retryable=False,
                    )

                if attempt < max_retries - 1:
                    delay = 2**attempt
                    logger.info(f"Retrying in {delay}s...")
                    time.sleep(delay)
                else:
                    logger.error(f"Anthropic API call failed after {max_retries} attempts")
                    raise

    def get_provider_name(self) -> str:
        """Get provider name"""
        return "anthropic"
