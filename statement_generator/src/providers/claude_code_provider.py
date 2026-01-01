"""
Claude Code CLI provider.

Uses the Claude Code CLI to generate responses, leveraging existing paid subscription.
"""

import logging
import subprocess
import time
from typing import Optional

from .base import BaseLLMProvider
from ..provider_exceptions import ProviderLimitError, ProviderAuthError

logger = logging.getLogger(__name__)


class ClaudeCodeProvider(BaseLLMProvider):
    """Provider for Claude Code CLI (subscription-based)"""

    def __init__(
        self,
        model: str = "sonnet",
        temperature: float = 0.2,
        cli_path: str = "claude",
    ):
        """
        Initialize Claude Code provider.

        Args:
            model: Claude model name (sonnet, opus, haiku)
            temperature: Default temperature (0.0-1.0)
            cli_path: Path to claude CLI executable
        """
        self.model = model
        self.default_temperature = temperature
        self.cli_path = cli_path
        self._verify_cli_available()

    def _verify_cli_available(self):
        """Verify Claude CLI is installed and accessible"""
        try:
            result = subprocess.run(
                [self.cli_path, "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode != 0:
                raise RuntimeError(
                    f"Claude CLI not accessible at '{self.cli_path}'. "
                    "Please install Claude Code CLI or update cli_path."
                )
            logger.info(f"Claude CLI found: {result.stdout.strip()}")
        except FileNotFoundError:
            raise RuntimeError(
                f"Claude CLI not found at '{self.cli_path}'. "
                "Please install Claude Code CLI: https://docs.claude.com/en/docs/claude-code/"
            )
        except subprocess.TimeoutExpired:
            raise RuntimeError("Claude CLI verification timed out")

    def generate(
        self, prompt: str, temperature: Optional[float] = None, max_retries: int = 3
    ) -> str:
        """
        Generate response using Claude Code CLI.

        Note: Claude CLI doesn't support temperature or max_tokens parameters.
        These are ignored when using this provider.
        """
        for attempt in range(max_retries):
            try:
                # Call Claude CLI in non-interactive mode
                # Format: claude --print --model sonnet "prompt text"
                # Note: Claude CLI doesn't support --temperature or --max-tokens
                cmd = [
                    self.cli_path,
                    "--print",  # Non-interactive mode
                    "--model",
                    self.model,
                    prompt,  # Pass prompt directly as argument
                ]

                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=120,  # 2 minute timeout
                )

                if result.returncode != 0:
                    error_output = result.stderr or result.stdout

                    # Detect specific error types
                    if "rate limit" in error_output.lower() or "too many requests" in error_output.lower():
                        raise ProviderLimitError(
                            "claude-code",
                            "Rate limit reached. You may have exceeded your usage quota.",
                            retryable=False,
                        )
                    elif "budget" in error_output.lower() or "quota" in error_output.lower():
                        raise ProviderLimitError(
                            "claude-code",
                            "Usage budget exceeded",
                            retryable=False,
                        )
                    elif "unauthorized" in error_output.lower() or "authentication" in error_output.lower():
                        raise ProviderAuthError(
                            "claude-code",
                            "Authentication failed. Please check your Claude Code login.",
                        )
                    else:
                        raise RuntimeError(
                            f"Claude CLI failed: {error_output}"
                        )

                response_text = result.stdout.strip()
                logger.debug(
                    f"Claude Code CLI response ({len(response_text)} chars): {response_text[:200]}..."
                )

                return response_text

            except subprocess.TimeoutExpired:
                logger.warning(
                    f"Claude CLI timed out (attempt {attempt + 1}/{max_retries})"
                )
                if attempt < max_retries - 1:
                    delay = 2**attempt
                    logger.info(f"Retrying in {delay}s...")
                    time.sleep(delay)
                else:
                    raise RuntimeError("Claude CLI timed out after all retries")

            except Exception as e:
                logger.warning(
                    f"Claude CLI call failed (attempt {attempt + 1}/{max_retries}): {e}"
                )

                if attempt < max_retries - 1:
                    delay = 2**attempt
                    logger.info(f"Retrying in {delay}s...")
                    time.sleep(delay)
                else:
                    logger.error(f"Claude CLI call failed after {max_retries} attempts")
                    raise

    def get_provider_name(self) -> str:
        """Get provider name"""
        return "claude-code"
