"""
Configuration management for statement generator.

Loads settings from project-level .env file and provides Pydantic models
for type-safe configuration access.
"""

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field


# Load environment variables from project root .env
PROJECT_ROOT = Path(__file__).parent.parent.parent.absolute()
ENV_PATH = PROJECT_ROOT / ".env"

if ENV_PATH.exists():
    load_dotenv(ENV_PATH)


class LLMConfig(BaseModel):
    """LLM configuration (supports multiple providers)"""

    provider: str = Field(default="codex", description="LLM provider (anthropic, claude-code, gemini, codex)")
    api_key: Optional[str] = Field(default=None, description="API key (only for anthropic provider)")
    model: str = Field(default="claude-sonnet-4-20250514")
    temperature: float = Field(default=0.2, ge=0.0, le=1.0)
    max_tokens: int = Field(default=4096)
    timeout: int = Field(default=60)  # seconds
    cli_path: Optional[str] = Field(default=None, description="CLI path for CLI-based providers")


class ProcessingConfig(BaseModel):
    """Processing behavior configuration"""

    batch_size: int = Field(default=10)
    max_retries: int = Field(default=3)
    retry_delay: float = Field(default=2.0)  # seconds
    skip_existing: bool = Field(default=False)


class PathsConfig(BaseModel):
    """File path configuration"""

    project_root: Path = Field(default_factory=lambda: PROJECT_ROOT)

    def _resolve_env_data_root(self) -> Optional[Path]:
        env_root = os.getenv("MKSAP_DATA_ROOT")
        if not env_root:
            return None
        data_root = Path(env_root)
        if not data_root.is_absolute():
            data_root = self.project_root / data_root
        return data_root

    @property
    def mksap_data(self) -> Path:
        env_root = self._resolve_env_data_root()
        if env_root:
            return env_root
        return self.project_root / "mksap_data"

    @property
    def test_mksap_data(self) -> Path:
        return self.project_root / "test_mksap_data"

    @property
    def statement_generator(self) -> Path:
        return self.project_root / "statement_generator"

    @property
    def artifacts(self) -> Path:
        return self.statement_generator / "artifacts"

    @property
    def checkpoints(self) -> Path:
        return self.artifacts / "checkpoints"

    @property
    def logs(self) -> Path:
        return self.artifacts / "logs"

    @property
    def validation_reports(self) -> Path:
        return self.artifacts / "validation"

    @property
    def prompts(self) -> Path:
        return self.statement_generator / "prompts"


class Config(BaseModel):
    """Master configuration"""

    llm: LLMConfig
    processing: ProcessingConfig
    paths: PathsConfig = Field(default_factory=PathsConfig)

    @classmethod
    def from_env(
        cls,
        temperature: Optional[float] = None,
        model: Optional[str] = None,
        provider: Optional[str] = None,
    ) -> "Config":
        """
        Load config from environment with optional overrides.

        Args:
            temperature: Override default temperature
            model: Override default model
            provider: Override default provider (anthropic, claude-code, gemini, codex)

        Returns:
            Config instance

        Raises:
            ValueError: If required configuration is missing
        """
        # Determine provider
        provider = provider or os.getenv("LLM_PROVIDER", "codex")

        # Build LLM config based on provider
        if provider == "anthropic":
            # Anthropic requires API key
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError(
                    "ANTHROPIC_API_KEY environment variable required for anthropic provider. "
                    f"Please set it in {ENV_PATH}"
                )

            llm_config = LLMConfig(
                provider=provider,
                api_key=api_key,
                model=os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514"),
                temperature=float(os.getenv("TEMPERATURE", "0.2")),
                max_tokens=int(os.getenv("MAX_TOKENS", "4096")),
            )

        elif provider == "claude-code":
            # Claude Code uses CLI (no API key needed)
            llm_config = LLMConfig(
                provider=provider,
                model=os.getenv("CLAUDE_MODEL", "sonnet"),
                temperature=float(os.getenv("TEMPERATURE", "0.2")),
                max_tokens=int(os.getenv("MAX_TOKENS", "4096")),
                cli_path=os.getenv("CLAUDE_CLI_PATH", "claude"),
            )

        elif provider == "gemini":
            # Gemini uses CLI (no API key needed)
            llm_config = LLMConfig(
                provider=provider,
                model=os.getenv("GEMINI_MODEL", "gemini-pro"),
                temperature=float(os.getenv("TEMPERATURE", "0.2")),
                max_tokens=int(os.getenv("MAX_TOKENS", "4096")),
                cli_path=os.getenv("GEMINI_CLI_PATH", "gemini"),
            )

        elif provider == "codex":
            # Codex (OpenAI) uses CLI (no API key needed)
            llm_config = LLMConfig(
                provider=provider,
                model=os.getenv("OPENAI_MODEL", ""),
                temperature=float(os.getenv("TEMPERATURE", "0.2")),
                max_tokens=int(os.getenv("MAX_TOKENS", "4096")),
                cli_path=os.getenv("OPENAI_CLI_PATH", "codex"),
            )

        else:
            raise ValueError(
                f"Unknown provider: {provider}. "
                "Supported providers: anthropic, claude-code, gemini, codex"
            )

        # Apply CLI overrides if provided
        if temperature is not None:
            llm_config.temperature = temperature
        if model is not None:
            llm_config.model = model

        # Build processing config with environment overrides
        processing_config = ProcessingConfig(
            batch_size=int(os.getenv("BATCH_SIZE", "10")),
            max_retries=int(os.getenv("MAX_RETRIES", "3")),
        )

        return cls(llm=llm_config, processing=processing_config, paths=PathsConfig())
