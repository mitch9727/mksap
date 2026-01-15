"""
Claude Code CLI provider.

Uses the Claude Code CLI to generate responses, leveraging existing paid subscription.
"""

import logging
import subprocess
import time
from typing import Optional

from ..base_provider import BaseLLMProvider
from ..exceptions import ProviderLimitError, ProviderAuthError

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
                # Call Claude CLI with prompt via stdin
                # Format: echo "prompt" | claude --print --model sonnet
                # Note: Claude CLI doesn't support --temperature or --max-tokens
                cmd = [
                    self.cli_path,
                    "--print",  # Non-interactive mode
                    "--model",
                    self.model,
                    "--no-session-persistence",  # Don't save sessions
                ]

                result = subprocess.run(
                    cmd,
                    input=prompt,
                    capture_output=True,
                    text=True,
                    timeout=120,  # 2 minute timeout
                )

                if result.returncode != 0:
                    error_output = result.stderr or result.stdout
                    error_lower = error_output.lower()

                    # Detect specific error types
                    if "eperm" in error_lower or "operation not permitted" in error_lower:
                        raise ProviderLimitError(
                            "claude-code",
                            "Claude CLI unavailable (permission denied).",
                            retryable=False,
                        )
                    elif any(
                        marker in error_lower
                        for marker in [
                            "rate limit",
                            "too many requests",
                            "usage limit",
                            "usage quota",
                            "usage exceeded",
                            "out of extra usage",
                            "budget",
                            "quota",
                            "usage cap",
                        ]
                    ):
                        raise ProviderLimitError(
                            "claude-code",
                            "Usage limit reached. You may have exceeded your Claude Code quota.",
                            retryable=False,
                        )
                    elif "unauthorized" in error_lower or "authentication" in error_lower:
                        raise ProviderAuthError(
                            "claude-code",
                            "Authentication failed. Please check your Claude Code login.",
                        )
                    else:
                        raise RuntimeError(f"Claude CLI failed: {error_output}")

                response_text = result.stdout.strip()
                logger.debug(
                    f"Claude Code CLI response ({len(response_text)} chars): {response_text[:200]}..."
                )

                # Extract JSON from markdown code blocks if present
                # Claude CLI often wraps JSON in ```json ... ``` blocks
                if response_text.startswith("```json"):
                    logger.debug("Extracting JSON from markdown code block")
                    start = response_text.find("```json") + 7
                    end = response_text.find("```", start)
                    if end != -1:
                        response_text = response_text[start:end].strip()
                        logger.debug(f"Extracted JSON ({len(response_text)} chars)")
                elif response_text.startswith("```"):
                    logger.debug("Extracting JSON from generic code block")
                    start = response_text.find("```") + 3
                    # Skip language identifier if present
                    if response_text[start] == '\n':
                        start += 1
                    end = response_text.find("```", start)
                    if end != -1:
                        response_text = response_text[start:end].strip()
                        logger.debug(f"Extracted JSON ({len(response_text)} chars)")

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
