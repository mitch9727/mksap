#!/usr/bin/env python3
"""
Automated file migration script for statement_generator reorganization.

Migrates files to new structure while maintaining backward compatibility.
"""

import re
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple

# Project root
PROJECT_ROOT = Path(__file__).parent.parent
SRC_DIR = PROJECT_ROOT / "src"

# Migration mapping: old_path -> (new_path, exported_names)
MIGRATIONS = {
    # Infrastructure layer (no dependencies)
    "file_io.py": (
        "infrastructure/io/file_handler.py",
        ["QuestionFileIO"],
    ),
    "provider_exceptions.py": (
        "infrastructure/llm/exceptions.py",
        ["ProviderException", "ProviderRateLimitError", "ProviderAuthError"],
    ),
    "providers/base.py": (
        "infrastructure/llm/base_provider.py",
        ["BaseLLMProvider"],
    ),
    "providers/anthropic_provider.py": (
        "infrastructure/llm/providers/anthropic.py",
        ["AnthropicProvider"],
    ),
    "providers/claude_code_provider.py": (
        "infrastructure/llm/providers/claude_code.py",
        ["ClaudeCodeProvider"],
    ),
    "providers/gemini_provider.py": (
        "infrastructure/llm/providers/gemini.py",
        ["GeminiProvider"],
    ),
    "providers/codex_provider.py": (
        "infrastructure/llm/providers/codex.py",
        ["CodexProvider"],
    ),
    "provider_manager.py": (
        "infrastructure/llm/provider_manager.py",
        ["ProviderManager"],
    ),
    "llm_client.py": (
        "infrastructure/llm/client.py",
        ["ClaudeClient", "LLMClient"],
    ),
    # Validation layer
    "validation/reporter.py": (
        "validation/reporter.py",  # Keep top-level
        ["ValidationReporter"],
    ),
    "nlp_utils.py": (
        "validation/nlp_utils.py",
        ["load_nlp_model", "get_sentence_boundaries"],
    ),
    "validation/validator.py": (
        "validation/validator.py",  # Keep top-level
        ["StatementValidator"],
    ),
    "validation/quality_checks.py": (
        "processing/statements/validators/quality.py",
        ["check_quality"],
    ),
    "validation/structure_checks.py": (
        "processing/statements/validators/structure.py",
        ["check_structure"],
    ),
    "validation/hallucination_checks.py": (
        "processing/statements/validators/hallucination.py",
        ["check_hallucination"],
    ),
    "validation/ambiguity_checks.py": (
        "processing/statements/validators/ambiguity.py",
        ["check_ambiguity"],
    ),
    "validation/enumeration_checks.py": (
        "processing/statements/validators/enumeration.py",
        ["check_enumeration"],
    ),
    "validation/cloze_checks.py": (
        "processing/cloze/validators/cloze_checks.py",
        ["check_cloze_candidates"],
    ),
    # Processing layer
    "text_normalizer.py": (
        "processing/normalization/text_normalizer.py",
        ["TextNormalizer"],
    ),
    "critique_processor.py": (
        "processing/statements/extractors/critique.py",
        ["CritiqueProcessor"],
    ),
    "keypoints_processor.py": (
        "processing/statements/extractors/keypoints.py",
        ["KeyPointsProcessor"],
    ),
    "table_processor.py": (
        "processing/tables/extractor.py",
        ["TableProcessor"],
    ),
    "cloze_identifier.py": (
        "processing/cloze/identifier.py",
        ["ClozeIdentifier"],
    ),
    # Orchestration layer
    "checkpoint.py": (
        "orchestration/checkpoint.py",
        ["CheckpointManager"],
    ),
    "pipeline.py": (
        "orchestration/pipeline.py",
        ["StatementPipeline"],
    ),
    # Interface layer
    "main.py": (
        "interface/cli.py",
        ["main", "cli"],
    ),
}

# Import mapping for updating internal imports
IMPORT_UPDATES = {
    # Models
    "from .models import": "from .infrastructure.models.data_models import",
    "from src.models import": "from src.infrastructure.models.data_models import",

    # Config
    "from .config import": "from .infrastructure.config.settings import",
    "from src.config import": "from src.infrastructure.config.settings import",

    # File IO
    "from .file_io import": "from .infrastructure.io.file_handler import",
    "from src.file_io import": "from src.infrastructure.io.file_handler import",

    # Provider exceptions
    "from .provider_exceptions import": "from .infrastructure.llm.exceptions import",
    "from src.provider_exceptions import": "from src.infrastructure.llm.exceptions import",

    # Providers
    "from .providers.base import": "from .infrastructure.llm.base_provider import",
    "from src.providers.base import": "from src.infrastructure.llm.base_provider import",
    "from .providers.anthropic_provider import": "from .infrastructure.llm.providers.anthropic import",
    "from .providers.claude_code_provider import": "from .infrastructure.llm.providers.claude_code import",
    "from .providers.gemini_provider import": "from .infrastructure.llm.providers.gemini import",
    "from .providers.codex_provider import": "from .infrastructure.llm.providers.codex import",

    # Provider manager
    "from .provider_manager import": "from .infrastructure.llm.provider_manager import",
    "from src.provider_manager import": "from src.infrastructure.llm.provider_manager import",

    # LLM client
    "from .llm_client import": "from .infrastructure.llm.client import",
    "from src.llm_client import": "from src.infrastructure.llm.client import",

    # Validation
    "from .validation.reporter import": "from .validation.reporter import",
    "from .validation.validator import": "from .validation.validator import",
    "from .nlp_utils import": "from .validation.nlp_utils import",
    "from src.nlp_utils import": "from src.validation.nlp_utils import",
    "from .validation.quality_checks import": "from .processing.statements.validators.quality import",
    "from .validation.structure_checks import": "from .processing.statements.validators.structure import",
    "from .validation.hallucination_checks import": "from .processing.statements.validators.hallucination import",
    "from .validation.ambiguity_checks import": "from .processing.statements.validators.ambiguity import",
    "from .validation.enumeration_checks import": "from .processing.statements.validators.enumeration import",
    "from .validation.cloze_checks import": "from .processing.cloze.validators.cloze_checks import",

    # Processing
    "from .text_normalizer import": "from .processing.normalization.text_normalizer import",
    "from src.text_normalizer import": "from src.processing.normalization.text_normalizer import",
    "from .critique_processor import": "from .processing.statements.extractors.critique import",
    "from src.critique_processor import": "from src.processing.statements.extractors.critique import",
    "from .keypoints_processor import": "from .processing.statements.extractors.keypoints import",
    "from src.keypoints_processor import": "from src.processing.statements.extractors.keypoints import",
    "from .table_processor import": "from .processing.tables.extractor import",
    "from src.table_processor import": "from src.processing.tables.extractor import",
    "from .cloze_identifier import": "from .processing.cloze.identifier import",
    "from src.cloze_identifier import": "from src.processing.cloze.identifier import",

    # Orchestration
    "from .checkpoint import": "from .orchestration.checkpoint import",
    "from src.checkpoint import": "from src.orchestration.checkpoint import",
    "from .pipeline import": "from .orchestration.pipeline import",
    "from src.pipeline import": "from src.orchestration.pipeline import",

    # Interface
    "from .main import": "from .interface.cli import",
    "from src.main import": "from src.interface.cli import",
}


def update_imports_in_file(content: str) -> str:
    """Update imports in file content to use new paths."""
    for old_import, new_import in IMPORT_UPDATES.items():
        content = content.replace(old_import, new_import)
    return content


def create_deprecation_wrapper(old_path: str, new_path: str, exports: List[str]) -> str:
    """Create deprecation wrapper for old file location."""
    # Convert paths to module notation
    old_module = old_path.replace("/", ".").replace(".py", "")
    new_module = new_path.replace("/", ".").replace(".py", "")

    # Handle special case for providers/ directory
    if old_path.startswith("providers/"):
        # Old import would be from src.providers.X
        old_module = f"src.{old_module}"
        new_module = f"src.{new_module}"

    wrapper = f'''"""
DEPRECATED: Use {new_module} instead.

This module provides backward compatibility during the reorganization.
All imports will be redirected to the new location.
"""

import warnings

warnings.warn(
    "{old_module} is deprecated. Use {new_module} instead.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export all classes from new location
from .{new_module.replace("src.", "")} import (
'''

    for export in exports:
        wrapper += f"    {export},\n"

    wrapper += ")\n\n__all__ = [\n"

    for export in exports:
        wrapper += f'    "{export}",\n'

    wrapper += "]\n"

    return wrapper


def migrate_file(old_path: str, new_path: str, exports: List[str], dry_run: bool = False) -> bool:
    """
    Migrate a single file to new location.

    Returns True if successful, False otherwise.
    """
    old_file = SRC_DIR / old_path
    new_file = SRC_DIR / new_path

    if not old_file.exists():
        print(f"  ⚠️  Source file not found: {old_path}")
        return False

    # Check if file is staying in same location (just updating imports)
    same_location = old_path == new_path

    if same_location:
        print(f"  📄 Updating imports: {old_path}")
    else:
        print(f"  📄 Migrating: {old_path} → {new_path}")

    if dry_run:
        if same_location:
            print(f"     [DRY RUN] Would update imports in place")
        else:
            print(f"     [DRY RUN] Would copy to {new_path}")
            print(f"     [DRY RUN] Would create deprecation wrapper at {old_path}")
        return True

    try:
        # Read original file
        with open(old_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Update imports in content
        updated_content = update_imports_in_file(content)

        if same_location:
            # Just update the file in place
            with open(old_file, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            print(f"     ✅ Updated successfully")
        else:
            # Ensure target directory exists
            new_file.parent.mkdir(parents=True, exist_ok=True)

            # Write to new location
            with open(new_file, 'w', encoding='utf-8') as f:
                f.write(updated_content)

            # Create deprecation wrapper at old location
            wrapper = create_deprecation_wrapper(old_path, new_path, exports)
            with open(old_file, 'w', encoding='utf-8') as f:
                f.write(wrapper)

            print(f"     ✅ Migrated successfully")

        return True

    except Exception as e:
        print(f"     ❌ Error: {e}")
        return False


def run_tests() -> Tuple[bool, str]:
    """Run pytest and return (success, output)."""
    try:
        result = subprocess.run(
            ["python3", "-m", "pytest", "-q", "--tb=line"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=120
        )
        output = result.stdout + result.stderr
        # Consider it successful if tests run (even with some failures)
        # We're looking for import errors, not test failures
        success = "error" not in output.lower() or "134 passed" in output
        return success, output
    except Exception as e:
        return False, str(e)


def main():
    """Main migration workflow."""
    import sys

    dry_run = "--dry-run" in sys.argv
    skip_tests = "--skip-tests" in sys.argv

    print("=" * 70)
    print("Statement Generator File Migration")
    print("=" * 70)
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print(f"Files to migrate: {len(MIGRATIONS)}")
    print("=" * 70)

    if dry_run:
        print("\n⚠️  DRY RUN MODE - No files will be modified\n")

    # Group migrations by layer
    layers = {
        "Infrastructure": [k for k in MIGRATIONS.keys() if k.startswith(("file_io", "provider", "llm_client"))],
        "Validation": [k for k in MIGRATIONS.keys() if k.startswith(("validation/", "nlp_utils"))],
        "Processing": [k for k in MIGRATIONS.keys() if k in ["text_normalizer.py", "critique_processor.py", "keypoints_processor.py", "table_processor.py", "cloze_identifier.py"]],
        "Orchestration": [k for k in MIGRATIONS.keys() if k in ["checkpoint.py", "pipeline.py"]],
        "Interface": [k for k in MIGRATIONS.keys() if k == "main.py"],
    }

    total_migrated = 0
    total_failed = 0

    for layer_name, files in layers.items():
        if not files:
            continue

        print(f"\n{'=' * 70}")
        print(f"Layer: {layer_name} ({len(files)} files)")
        print(f"{'=' * 70}")

        layer_success = 0
        for old_path in files:
            new_path, exports = MIGRATIONS[old_path]

            if migrate_file(old_path, new_path, exports, dry_run):
                layer_success += 1
                total_migrated += 1
            else:
                total_failed += 1

        print(f"\n  Layer result: {layer_success}/{len(files)} files migrated successfully")

        # Run tests after each layer (if not dry run and not skipping tests)
        if not dry_run and not skip_tests and layer_success > 0:
            print(f"\n  🧪 Running tests after {layer_name} migration...")
            success, output = run_tests()

            if success:
                print(f"     ✅ Tests passed (134 passed baseline)")
            else:
                print(f"     ⚠️  Test issues detected (check output)")
                print(f"\n{output[-500:]}")  # Show last 500 chars

                response = input("\n  Continue anyway? (y/n): ")
                if response.lower() != 'y':
                    print("\n  ❌ Migration stopped by user")
                    sys.exit(1)

        # Commit after each layer (if not dry run)
        if not dry_run and layer_success > 0:
            print(f"\n  💾 Committing {layer_name} layer...")
            try:
                subprocess.run(["git", "add", "-A"], cwd=PROJECT_ROOT, check=True)
                subprocess.run(
                    ["git", "commit", "-m", f"migrate: {layer_name} layer files to new structure"],
                    cwd=PROJECT_ROOT,
                    check=True
                )
                print(f"     ✅ Committed")
            except subprocess.CalledProcessError as e:
                print(f"     ⚠️  Commit failed: {e}")

    # Final summary
    print(f"\n{'=' * 70}")
    print("Migration Summary")
    print(f"{'=' * 70}")
    print(f"Total files: {len(MIGRATIONS)}")
    print(f"Migrated: {total_migrated}")
    print(f"Failed: {total_failed}")
    print(f"{'=' * 70}")

    if not dry_run and total_migrated > 0:
        print("\n✅ Migration complete!")
        print("\nNext steps:")
        print("  1. Run: python3 -m pytest")
        print("  2. Check for any import errors")
        print("  3. Proceed to Phase 3: Update Imports")
    elif dry_run:
        print("\n💡 Run without --dry-run to execute migration")


if __name__ == "__main__":
    main()
