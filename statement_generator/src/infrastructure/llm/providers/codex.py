"""
Codex CLI provider.

Uses the Codex CLI to generate responses with existing subscription credentials.
"""

import logging
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Optional

from ..base_provider import BaseLLMProvider

logger = logging.getLogger(__name__)


class CodexProvider(BaseLLMProvider):
    """Provider for OpenAI Codex CLI (subscription-based)"""

    def __init__(
        self,
        model: str = "",
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
        """Verify Codex CLI is installed and accessible"""
        try:
            result = subprocess.run(
                [self.cli_path, "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode != 0:
                raise RuntimeError(
                    f"Codex CLI not accessible at '{self.cli_path}'. "
                    "Please install Codex CLI or update cli_path."
                )
            logger.info(f"Codex CLI found: {result.stdout.strip()}")
        except FileNotFoundError:
            raise RuntimeError(
                f"Codex CLI not found at '{self.cli_path}'. "
                "Please install Codex CLI: https://github.com/openai/codex"
            )
        except subprocess.TimeoutExpired:
            raise RuntimeError("Codex CLI verification timed out")

    def generate(
        self, prompt: str, temperature: Optional[float] = None, max_retries: int = 3
    ) -> str:
        """Generate response using Codex CLI"""
        _ = temperature if temperature is not None else self.default_temperature

        for attempt in range(max_retries):
            try:
                # Capture last message to a temp file for clean JSON parsing
                with tempfile.NamedTemporaryFile(
                    mode="w", suffix=".txt", delete=False
                ) as output_file:
                    output_path = Path(output_file.name)

                try:
                    # Codex CLI exec reads prompt from stdin when "-" is provided.
                    cmd = [
                        self.cli_path,
                        "exec",
                        "-",
                        "--output-last-message",
                        str(output_path),
                    ]
                    if self.model:
                        cmd.extend(["-m", self.model])

                    result = subprocess.run(
                        cmd,
                        input=prompt,
                        capture_output=True,
                        text=True,
                        timeout=120,  # 2 minute timeout
                    )

                    if result.returncode != 0:
                        raise RuntimeError(
                            f"Codex CLI failed: {result.stderr or result.stdout}"
                        )

                    response_text = output_path.read_text().strip()
                    if not response_text:
                        raise RuntimeError("Codex CLI returned empty response")
                    logger.debug(
                        f"Codex CLI response ({len(response_text)} chars): {response_text[:200]}..."
                    )

                    return response_text

                finally:
                    output_path.unlink(missing_ok=True)

            except subprocess.TimeoutExpired:
                logger.warning(
                    f"Codex CLI timed out (attempt {attempt + 1}/{max_retries})"
                )
                if attempt < max_retries - 1:
                    delay = 2**attempt
                    logger.info(f"Retrying in {delay}s...")
                    time.sleep(delay)
                else:
                    raise RuntimeError("Codex CLI timed out after all retries")

            except Exception as e:
                logger.warning(
                    f"Codex CLI call failed (attempt {attempt + 1}/{max_retries}): {e}"
                )

                if attempt < max_retries - 1:
                    delay = 2**attempt
                    logger.info(f"Retrying in {delay}s...")
                    time.sleep(delay)
                else:
                    logger.error(f"Codex CLI call failed after {max_retries} attempts")
                    raise

    def get_provider_name(self) -> str:
        """Get provider name"""
        return "codex"
