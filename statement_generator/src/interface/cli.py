"""
CLI entry point for MKSAP statement generator.

Provides commands for processing questions and managing state.
"""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import click

from .orchestration.checkpoint import CheckpointManager
from .infrastructure.config.settings import Config
from .infrastructure.io.file_handler import QuestionFileIO
from .infrastructure.llm.client import ClaudeClient
from .infrastructure.models.data_models import ProcessingResult
from .orchestration.pipeline import StatementPipeline
from .infrastructure.llm.provider_manager import ProviderManager
from .infrastructure.llm.exceptions import ProviderLimitError, ProviderAuthError


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


def resolve_data_root(
    paths: "PathsConfig",
    data_root: Optional[str],
    mode: Optional[str],
    default_to_test: bool,
) -> Path:
    if data_root:
        root_path = Path(data_root)
        if not root_path.is_absolute():
            root_path = paths.project_root / root_path
        return root_path
    if default_to_test or mode == "test":
        return paths.test_mksap_data
    return paths.mksap_data


def _parse_python_version(value: str) -> Optional[tuple[int, ...]]:
    cleaned = value.strip()
    if not cleaned:
        return None
    parts = cleaned.split(".")
    if len(parts) > 3 or any(not part.isdigit() for part in parts):
        return None
    return tuple(int(part) for part in parts)


def ensure_python_version() -> None:
    expected_raw = os.getenv("MKSAP_PYTHON_VERSION")
    if not expected_raw:
        return
    expected = _parse_python_version(expected_raw)
    if not expected:
        raise click.ClickException(
            "Invalid MKSAP_PYTHON_VERSION value. Expected format like 3.11 or 3.11.9."
        )
    current = sys.version_info[: len(expected)]
    if current != expected:
        expected_str = ".".join(str(part) for part in expected)
        current_str = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        raise click.ClickException(
            f"Python {expected_str} required (from MKSAP_PYTHON_VERSION), "
            f"but running {current_str}. Update .env or switch interpreters."
        )


@click.group()
def cli():
    """MKSAP Statement Generator - Phase 2"""
    ensure_python_version()


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
@click.option(
    "--skip-existing/--overwrite",
    default=False,
    help="Overwrite existing true_statements by default; use --skip-existing to skip",
)
@click.option("--force", is_flag=True, default=False, help="Re-process even if already completed (ignores checkpoint)")
@click.option("--dry-run", is_flag=True, default=False, help="Preview what would be processed")
@click.option(
    "--data-root",
    type=click.Path(),
    default=None,
    help="Override data root (defaults to test_mksap_data in test mode, mksap_data in production)",
)
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
    data_root: Optional[str],
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

    data_root_path = resolve_data_root(config.paths, data_root, mode, default_to_test=False)
    if not data_root_path.exists():
        logger.error(f"Data root not found: {data_root_path}")
        return

    logger.info(f"Data root: {data_root_path}")

    file_io = QuestionFileIO(data_root_path)
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
    from .infrastructure.config.settings import PathsConfig
    checkpoint = CheckpointManager(PathsConfig().checkpoints)

    print(f"Processed questions: {checkpoint.get_processed_count()}")
    print(f"Failed questions: {checkpoint.get_failed_count()}")


@cli.command()
@click.confirmation_option(prompt="Are you sure you want to reset checkpoints?")
def reset():
    """Reset checkpoint state"""
    # Reset doesn't need LLM provider, just use default config
    from .infrastructure.config.settings import PathsConfig
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
    from .infrastructure.config.settings import PathsConfig

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
    from .infrastructure.config.settings import PathsConfig

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


@cli.command()
@click.option(
    "--question-id",
    "question_ids",
    multiple=True,
    help="Question ID(s) to copy into test_mksap_data (repeatable)",
)
@click.option("--system", type=str, help="Copy all questions in system (e.g., cv, en)")
@click.option("--all", "copy_all", is_flag=True, help="Copy all questions into test_mksap_data")
@click.option(
    "--overwrite/--skip-existing",
    default=False,
    help="Overwrite existing question folders in test_mksap_data",
)
def prepare_test(question_ids, system, copy_all, overwrite):
    """Copy questions into test_mksap_data for safe iteration"""
    import shutil
    from .infrastructure.config.settings import PathsConfig

    paths = PathsConfig()
    source_root = paths.mksap_data
    target_root = paths.test_mksap_data

    if not source_root.exists():
        print(f"Source data root not found: {source_root}")
        return

    target_root.mkdir(parents=True, exist_ok=True)
    file_io = QuestionFileIO(source_root)

    questions = []
    if question_ids:
        for question_id in question_ids:
            question_path = file_io.get_question_path(question_id)
            if not question_path:
                print(f"Question not found: {question_id}")
                continue
            questions.append(question_path)
    elif system:
        questions = file_io.discover_system_questions(system)
    elif copy_all:
        questions = file_io.discover_all_questions()
    else:
        print("Error: Must specify --question-id, --system, or --all")
        return

    copied = 0
    skipped = 0
    for question_file in questions:
        question_dir = question_file.parent
        system_dir = question_dir.parent.name
        dest_dir = target_root / system_dir / question_dir.name
        dest_dir.parent.mkdir(parents=True, exist_ok=True)

        if dest_dir.exists() and not overwrite:
            print(f"Skipping existing: {dest_dir}")
            skipped += 1
            continue
        if dest_dir.exists() and overwrite:
            shutil.rmtree(dest_dir)

        shutil.copytree(question_dir, dest_dir)
        copied += 1
        print(f"Copied: {question_dir.name} -> {dest_dir}")

    print(f"Done. Copied {copied}, skipped {skipped}.")


@cli.command()
@click.option("--question-id", type=str, help="Validate single question by ID")
@click.option("--system", type=str, help="Validate all questions in system (e.g., cv, en)")
@click.option("--all", "validate_all", is_flag=True, help="Validate all 2,198 questions")
@click.option(
    "--severity",
    type=click.Choice(["error", "warning", "all"]),
    default="all",
    help="Filter by severity level"
)
@click.option(
    "--category",
    multiple=True,
    help="Filter by category (structure, quality, cloze, hallucination)"
)
@click.option(
    "--output",
    type=click.Path(),
    help="Save report to file (relative paths go under statement_generator/artifacts/validation/)",
)
@click.option("--detailed", is_flag=True, help="Show detailed issues for each question")
@click.option(
    "--data-root",
    type=click.Path(),
    default=None,
    help="Override data root (default: test_mksap_data)",
)
def validate(question_id, system, validate_all, severity, category, output, detailed, data_root):
    """Validate extracted statements for quality and correctness"""
    from .infrastructure.config.settings import PathsConfig
    from .validation import StatementValidator
    from .validation.reporter import generate_summary_report, generate_detailed_report, export_to_json

    # Validation doesn't need LLM provider, just use default config
    paths = PathsConfig()
    data_root_path = resolve_data_root(paths, data_root, mode=None, default_to_test=True)
    if not data_root_path.exists():
        print(f"Data root not found: {data_root_path}")
        return

    file_io = QuestionFileIO(data_root_path)
    validator = StatementValidator()

    # Discover questions to validate
    if question_id:
        question_path = file_io.get_question_path(question_id)
        if not question_path:
            print(f"Error: Question not found: {question_id}")
            return
        questions = [question_path]
    elif system:
        questions = file_io.discover_system_questions(system)
    elif validate_all:
        questions = file_io.discover_all_questions()
    else:
        print("Error: Must specify --question-id, --system, or --all")
        return

    print(f"Validating {len(questions)} questions...")
    print()

    # Validate each question
    results = []
    for i, question_file in enumerate(questions):
        if len(questions) > 1 and (i + 1) % 10 == 0:
            print(f"Progress: {i + 1}/{len(questions)}")

        try:
            data = file_io.read_question(question_file)
            result = validator.validate_question(data)
            results.append(result)
        except Exception as e:
            print(f"Error validating {question_file.stem}: {e}")

    print()
    print("=" * 70)

    # Filter results by severity if requested
    if severity != "all":
        filtered_results = []
        for result in results:
            if severity == "error" and result.errors:
                filtered_results.append(result)
            elif severity == "warning" and (result.errors or result.warnings):
                filtered_results.append(result)
        results = filtered_results

    # Filter by category if requested
    if category:
        category_set = set(category)
        filtered_results = []
        for result in results:
            all_issues = result.errors + result.warnings + result.info
            if any(issue.category in category_set for issue in all_issues):
                filtered_results.append(result)
        results = filtered_results

    # Generate and print report
    if detailed:
        report = generate_detailed_report(results)
    else:
        report = generate_summary_report(results)

    print(report)

    # Save to file if requested
    if output:
        output_path = Path(output)
        if not output_path.is_absolute():
            output_path = paths.validation_reports / output_path

        output_path.parent.mkdir(parents=True, exist_ok=True)

        if output_path.suffix == ".json":
            export_to_json(results, output_path)
            print(f"\nDetailed report saved to: {output_path}")
        else:
            # Save text report
            output_path.write_text(report)
            print(f"\nReport saved to: {output_path}")


if __name__ == "__main__":
    cli()
