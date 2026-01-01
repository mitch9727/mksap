"""
CLI entry point for MKSAP statement generator.

Provides commands for processing questions and managing state.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import click

from .checkpoint import CheckpointManager
from .config import Config
from .file_io import QuestionFileIO
from .llm_client import ClaudeClient
from .models import ProcessingResult
from .pipeline import StatementPipeline
from .provider_manager import ProviderManager
from .provider_exceptions import ProviderLimitError, ProviderAuthError


def setup_logging(log_level: str, log_dir: Path):
    """Configure logging to file and console"""
    log_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"statement_gen_{timestamp}.log"

    logging.basicConfig(
        level=getattr(logging, log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler(log_file), logging.StreamHandler()],
    )

    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized: {log_file}")


@click.group()
def cli():
    """MKSAP Statement Generator - Phase 2"""
    pass


@cli.command()
@click.option(
    "--mode",
    type=click.Choice(["test", "production"]),
    default="test",
    help="Test processes 1-2 questions, production processes all",
)
@click.option("--question-id", type=str, default=None, help="Process specific question by ID")
@click.option("--system", type=str, default=None, help="Process all questions in system (e.g., cv, en)")
@click.option("--temperature", type=float, default=None, help="LLM temperature (default: 0.2)")
@click.option("--model", type=str, default=None, help="Model name (default varies by provider)")
@click.option(
    "--provider",
    type=click.Choice(["anthropic", "claude-code", "gemini", "codex"]),
    default=None,
    help="LLM provider (default: anthropic). CLI providers use existing subscription.",
)
@click.option("--resume/--no-resume", default=True, help="Resume from checkpoint")
@click.option("--skip-existing/--overwrite", default=True, help="Skip questions with true_statements or overwrite")
@click.option("--force", is_flag=True, default=False, help="Re-process even if already completed (ignores checkpoint)")
@click.option("--dry-run", is_flag=True, default=False, help="Preview what would be processed")
@click.option(
    "--log-level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"]),
    default="INFO",
    help="Logging verbosity",
)
@click.option("--batch-size", type=int, default=10, help="Questions per checkpoint save")
def process(
    mode: str,
    question_id: Optional[str],
    system: Optional[str],
    temperature: Optional[float],
    model: Optional[str],
    provider: Optional[str],
    resume: bool,
    skip_existing: bool,
    force: bool,
    dry_run: bool,
    log_level: str,
    batch_size: int,
):
    """Process questions and generate statements"""

    # Load config
    config = Config.from_env(temperature=temperature, model=model, provider=provider)
    config.processing.batch_size = batch_size
    config.processing.skip_existing = skip_existing

    # Setup logging
    setup_logging(log_level, config.paths.logs)
    logger = logging.getLogger(__name__)

    logger.info(f"Starting statement generation - Mode: {mode}")
    logger.info(f"Config: model={config.llm.model}, temp={config.llm.temperature}")

    # Initialize components with provider fallback support
    try:
        provider_manager = ProviderManager(config)
        logger.info(f"Using provider: {provider_manager.get_current_provider()}")
    except Exception as e:
        logger.error(f"Failed to initialize provider: {e}")
        return

    file_io = QuestionFileIO(config.paths.mksap_data)
    checkpoint = CheckpointManager(config.paths.checkpoints)
    # Use provider_manager as client (it has same interface with fallback support)
    pipeline = StatementPipeline(provider_manager, file_io, config.paths.prompts)

    # Discover questions to process
    if question_id:
        question_path = file_io.get_question_path(question_id)
        if not question_path:
            logger.error(f"Question not found: {question_id}")
            return
        questions = [question_path]
    elif system:
        questions = file_io.discover_system_questions(system)
        if mode == "test":
            questions = questions[:2]
    else:
        questions = file_io.discover_all_questions()
        if mode == "test":
            questions = questions[:2]

    logger.info(f"Discovered {len(questions)} questions to process")

    # Filter if resuming and skipping existing (unless --force)
    if resume and skip_existing and not force:
        original_count = len(questions)
        questions = [q for q in questions if not checkpoint.is_processed(q.stem)]
        logger.info(f"Filtered {original_count - len(questions)} already processed questions")
    elif force:
        logger.info("--force flag enabled: Will re-process all questions")

    if dry_run:
        logger.info("DRY RUN - Would process:")
        for q in questions[:10]:
            logger.info(f"  - {q.stem}")
        if len(questions) > 10:
            logger.info(f"  ... and {len(questions) - 10} more")
        return

    # Process questions
    results: List[ProcessingResult] = []
    batch_counter = 0

    for i, question_file in enumerate(questions):
        logger.info(f"Processing {i+1}/{len(questions)}: {question_file.stem}")

        # Check if already has true_statements (if skip_existing and not force)
        if skip_existing and not force:
            data = file_io.read_question(question_file)
            if file_io.has_true_statements(data):
                logger.info(f"Skipping {question_file.stem} - already has true_statements")
                checkpoint.mark_processed(question_file.stem, batch_save=True)
                continue

        # Process
        result = pipeline.process_question(question_file)
        results.append(result)

        if result.success:
            checkpoint.mark_processed(result.question_id, batch_save=True)
        else:
            checkpoint.mark_failed(result.question_id)

        # Batch checkpoint save
        batch_counter += 1
        if batch_counter >= config.processing.batch_size:
            checkpoint.batch_save()
            logger.info(f"Checkpoint saved at {i+1}/{len(questions)}")
            batch_counter = 0

    # Final checkpoint save
    checkpoint.batch_save()

    # Print summary
    successful = [r for r in results if r.success]
    failed = [r for r in results if not r.success]

    total_statements = sum(r.statements_extracted for r in successful)
    total_api_calls = sum(r.api_calls for r in successful)

    logger.info("=" * 60)
    logger.info("PROCESSING COMPLETE")
    logger.info(f"Total processed: {len(results)}")
    logger.info(f"Successful: {len(successful)}")
    logger.info(f"Failed: {len(failed)}")
    logger.info(f"Total statements extracted: {total_statements}")
    logger.info(f"Total API calls: {total_api_calls}")
    logger.info("=" * 60)


@cli.command()
def stats():
    """Show processing statistics"""
    # Stats doesn't need LLM provider, just use default config
    from .config import PathsConfig
    checkpoint = CheckpointManager(PathsConfig().checkpoints)

    print(f"Processed questions: {checkpoint.get_processed_count()}")
    print(f"Failed questions: {checkpoint.get_failed_count()}")


@cli.command()
@click.confirmation_option(prompt="Are you sure you want to reset checkpoints?")
def reset():
    """Reset checkpoint state"""
    # Reset doesn't need LLM provider, just use default config
    from .config import PathsConfig
    checkpoint = CheckpointManager(PathsConfig().checkpoints)
    checkpoint.reset()
    print("Checkpoints reset")


@cli.command()
@click.option(
    "--keep-days",
    type=int,
    default=7,
    help="Keep logs from the last N days (default: 7)",
)
@click.option("--dry-run", is_flag=True, help="Preview what would be deleted")
def clean_logs(keep_days: int, dry_run: bool):
    """Clean old log files to save space and reduce clutter"""
    from datetime import datetime, timedelta
    from .config import PathsConfig

    # Clean-logs doesn't need LLM provider, just use default config
    log_dir = PathsConfig().logs

    if not log_dir.exists():
        print(f"No log directory found at {log_dir}")
        return

    cutoff_date = datetime.now() - timedelta(days=keep_days)
    deleted_count = 0
    deleted_size = 0

    print(f"Scanning for logs older than {keep_days} days...")
    print(f"Cutoff date: {cutoff_date.strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    for log_file in sorted(log_dir.glob("*.log")):
        # Parse timestamp from filename: statement_gen_YYYYMMDD_HHMMSS.log
        try:
            timestamp_str = log_file.stem.split("_")[-2] + log_file.stem.split("_")[-1]
            file_date = datetime.strptime(timestamp_str, "%Y%m%d%H%M%S")

            if file_date < cutoff_date:
                file_size = log_file.stat().st_size
                deleted_size += file_size
                deleted_count += 1

                if dry_run:
                    print(f"Would delete: {log_file.name} ({file_size:,} bytes, {file_date.strftime('%Y-%m-%d')})")
                else:
                    print(f"Deleting: {log_file.name} ({file_size:,} bytes, {file_date.strftime('%Y-%m-%d')})")
                    log_file.unlink()
        except (ValueError, IndexError):
            # Skip files that don't match expected format
            continue

    print()
    if dry_run:
        print(f"Would delete {deleted_count} log files ({deleted_size:,} bytes)")
        print("Run without --dry-run to actually delete files")
    else:
        print(f"Deleted {deleted_count} log files ({deleted_size:,} bytes)")


@cli.command()
@click.confirmation_option(
    prompt="This will delete ALL logs and reset checkpoints. Are you sure?"
)
def clean_all():
    """Clean all logs and reset checkpoints (fresh start)"""
    import shutil
    from .config import PathsConfig

    # Clean-all doesn't need LLM provider, just use default config
    paths = PathsConfig()
    log_dir = paths.logs
    if log_dir.exists():
        file_count = len(list(log_dir.glob("*.log")))
        shutil.rmtree(log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)
        print(f"✓ Deleted {file_count} log files")

    # Reset checkpoints
    checkpoint = CheckpointManager(paths.checkpoints)
    checkpoint.reset()
    print("✓ Reset checkpoints")

    print("\nFresh start! All logs and checkpoints cleared.")


if __name__ == "__main__":
    cli()
