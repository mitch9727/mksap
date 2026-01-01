"""
OpenAI Codex CLI provider.

Uses the OpenAI CLI to generate responses with Codex, leveraging existing paid subscription.
"""

import logging
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Optional

from .base import BaseLLMProvider

logger = logging.getLogger(__name__)


class CodexProvider(BaseLLMProvider):
    """Provider for OpenAI Codex CLI (subscription-based)"""

    def __init__(
        self,
        model: str = "gpt-4",
        temperature: float = 0.2,
        cli_path: str = "codex",
    ):
        """
        Initialize Codex provider.

        Args:
            model: OpenAI model name (gpt-4, gpt-3.5-turbo, etc.)
            temperature: Default temperature (0.0-1.0)
            cli_path: Path to openai CLI executable
        """
        self.model = model
        self.default_temperature = temperature
        self.cli_path = cli_path
        self._verify_cli_available()

    def _verify_cli_available(self):
        """Verify OpenAI CLI is installed and accessible"""
        try:
            result = subprocess.run(
                [self.cli_path, "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode != 0:
                raise RuntimeError(
                    f"OpenAI CLI not accessible at '{self.cli_path}'. "
                    "Please install OpenAI CLI or update cli_path."
                )
            logger.info(f"OpenAI CLI found: {result.stdout.strip()}")
        except FileNotFoundError:
            raise RuntimeError(
                f"OpenAI CLI not found at '{self.cli_path}'. "
                "Please install OpenAI CLI: https://platform.openai.com/docs/guides/cli"
            )
        except subprocess.TimeoutExpired:
            raise RuntimeError("OpenAI CLI verification timed out")

    def generate(
        self, prompt: str, temperature: Optional[float] = None, max_retries: int = 3
    ) -> str:
        """Generate response using OpenAI CLI"""
        temperature = temperature if temperature is not None else self.default_temperature

        for attempt in range(max_retries):
            try:
                # Write prompt to temporary file
                with tempfile.NamedTemporaryFile(
                    mode="w", suffix=".txt", delete=False
                ) as f:
                    f.write(prompt)
                    prompt_file = Path(f.name)

                try:
                    # Call OpenAI CLI with prompt file
                    # Format: openai api completions.create --model gpt-4 --temperature 0.2 --file prompt.txt
                    cmd = [
                        self.cli_path,
                        "api",
                        "chat.completions.create",
                        "-m",
                        self.model,
                        "-t",
                        str(temperature),
                        "--file",
                        str(prompt_file),
                    ]

                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=120,  # 2 minute timeout
                    )

                    if result.returncode != 0:
                        raise RuntimeError(
                            f"OpenAI CLI failed: {result.stderr or result.stdout}"
                        )

                    response_text = result.stdout.strip()
                    logger.debug(
                        f"OpenAI CLI response ({len(response_text)} chars): {response_text[:200]}..."
                    )

                    return response_text

                finally:
                    # Clean up temporary file
                    prompt_file.unlink(missing_ok=True)

            except subprocess.TimeoutExpired:
                logger.warning(
                    f"OpenAI CLI timed out (attempt {attempt + 1}/{max_retries})"
                )
                if attempt < max_retries - 1:
                    delay = 2**attempt
                    logger.info(f"Retrying in {delay}s...")
                    time.sleep(delay)
                else:
                    raise RuntimeError("OpenAI CLI timed out after all retries")

            except Exception as e:
                logger.warning(
                    f"OpenAI CLI call failed (attempt {attempt + 1}/{max_retries}): {e}"
                )

                if attempt < max_retries - 1:
                    delay = 2**attempt
                    logger.info(f"Retrying in {delay}s...")
                    time.sleep(delay)
                else:
                    logger.error(f"OpenAI CLI call failed after {max_retries} attempts")
                    raise

    def get_provider_name(self) -> str:
        """Get provider name"""
        return "codex"
