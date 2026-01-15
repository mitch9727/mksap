#!/usr/bin/env python3
"""
Update all imports to use new module structure.

Scans all Python files and updates import statements to use new paths.
"""

import re
from pathlib import Path
from typing import Dict, List, Tuple

# Project root
PROJECT_ROOT = Path(__file__).parent.parent
SRC_DIR = PROJECT_ROOT / "src"

# Import mapping: old import pattern → new import pattern
IMPORT_MAPPINGS = {
    # Models
    "from src.models import": "from src.infrastructure.models.data_models import",
    "from .models import": "from .infrastructure.models.data_models import",

    # Config
    "from src.config import": "from src.infrastructure.config.settings import",
    "from .config import": "from .infrastructure.config.settings import",

    # File IO
    "from src.file_io import": "from src.infrastructure.io.file_handler import",
    "from .file_io import": "from .infrastructure.io.file_handler import",

    # Provider exceptions
    "from src.provider_exceptions import": "from src.infrastructure.llm.exceptions import",
    "from .provider_exceptions import": "from .infrastructure.llm.exceptions import",

    # Providers (base)
    "from src.providers.base import": "from src.infrastructure.llm.base_provider import",
    "from .providers.base import": "from .infrastructure.llm.base_provider import",

    # Providers (implementations)
    "from src.providers.anthropic_provider import": "from src.infrastructure.llm.providers.anthropic import",
    "from .providers.anthropic_provider import": "from .infrastructure.llm.providers.anthropic import",
    "from src.providers.claude_code_provider import": "from src.infrastructure.llm.providers.claude_code import",
    "from .providers.claude_code_provider import": "from .infrastructure.llm.providers.claude_code import",
    "from src.providers.gemini_provider import": "from src.infrastructure.llm.providers.gemini import",
    "from .providers.gemini_provider import": "from .infrastructure.llm.providers.gemini import",
    "from src.providers.codex_provider import": "from src.infrastructure.llm.providers.codex import",
    "from .providers.codex_provider import": "from .infrastructure.llm.providers.codex import",

    # Provider manager
    "from src.provider_manager import": "from src.infrastructure.llm.provider_manager import",
    "from .provider_manager import": "from .infrastructure.llm.provider_manager import",

    # LLM client
    "from src.llm_client import": "from src.infrastructure.llm.client import",
    "from .llm_client import": "from .infrastructure.llm.client import",

    # Validation (files staying in place)
    "from src.validation.reporter import": "from src.validation.reporter import",
    "from .validation.reporter import": "from .validation.reporter import",
    "from src.validation.validator import": "from src.validation.validator import",
    "from .validation.validator import": "from .validation.validator import",

    # NLP utils (moving to validation)
    "from src.nlp_utils import": "from src.validation.nlp_utils import",
    "from .nlp_utils import": "from .validation.nlp_utils import",

    # Validation checks (moving to processing)
    "from src.validation.quality_checks import": "from src.processing.statements.validators.quality import",
    "from .validation.quality_checks import": "from .processing.statements.validators.quality import",
    "from src.validation.structure_checks import": "from src.processing.statements.validators.structure import",
    "from .validation.structure_checks import": "from .processing.statements.validators.structure import",
    "from src.validation.hallucination_checks import": "from src.processing.statements.validators.hallucination import",
    "from .validation.hallucination_checks import": "from .processing.statements.validators.hallucination import",
    "from src.validation.ambiguity_checks import": "from src.processing.statements.validators.ambiguity import",
    "from .validation.ambiguity_checks import": "from .processing.statements.validators.ambiguity import",
    "from src.validation.enumeration_checks import": "from src.processing.statements.validators.enumeration import",
    "from .validation.enumeration_checks import": "from .processing.statements.validators.enumeration import",
    "from src.validation.cloze_checks import": "from src.processing.cloze.validators.cloze_checks import",
    "from .validation.cloze_checks import": "from .processing.cloze.validators.cloze_checks import",

    # Processing
    "from src.text_normalizer import": "from src.processing.normalization.text_normalizer import",
    "from .text_normalizer import": "from .processing.normalization.text_normalizer import",
    "from src.critique_processor import": "from src.processing.statements.extractors.critique import",
    "from .critique_processor import": "from .processing.statements.extractors.critique import",
    "from src.keypoints_processor import": "from src.processing.statements.extractors.keypoints import",
    "from .keypoints_processor import": "from .processing.statements.extractors.keypoints import",
    "from src.table_processor import": "from src.processing.tables.extractor import",
    "from .table_processor import": "from .processing.tables.extractor import",
    "from src.cloze_identifier import": "from src.processing.cloze.identifier import",
    "from .cloze_identifier import": "from .processing.cloze.identifier import",

    # Orchestration
    "from src.checkpoint import": "from src.orchestration.checkpoint import",
    "from .checkpoint import": "from .orchestration.checkpoint import",
    "from src.pipeline import": "from src.orchestration.pipeline import",
    "from .pipeline import": "from .orchestration.pipeline import",

    # Interface
    "from src.main import": "from src.interface.cli import",
    "from .main import": "from .interface.cli import",
}


def update_imports_in_content(content: str) -> Tuple[str, int]:
    """
    Update imports in file content.

    Returns: (updated_content, number_of_changes)
    """
    updated = content
    changes = 0

    for old_import, new_import in IMPORT_MAPPINGS.items():
        if old_import in updated:
            count = updated.count(old_import)
            updated = updated.replace(old_import, new_import)
            changes += count

    return updated, changes


def update_file(file_path: Path, dry_run: bool = False) -> Tuple[bool, int]:
    """
    Update imports in a single file.

    Returns: (success, number_of_changes)
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            original = f.read()

        updated, changes = update_imports_in_content(original)

        if changes > 0:
            if not dry_run:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(updated)
            return True, changes
        else:
            return True, 0

    except Exception as e:
        print(f"     ❌ Error updating {file_path}: {e}")
        return False, 0


def find_python_files(directory: Path) -> List[Path]:
    """Find all Python files in directory (recursive)."""
    return list(directory.rglob("*.py"))


def main():
    """Main import update workflow."""
    import sys
    import subprocess

    dry_run = "--dry-run" in sys.argv

    print("=" * 70)
    print("Import Update Script")
    print("=" * 70)
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print("=" * 70)

    if dry_run:
        print("\n⚠️  DRY RUN MODE - No files will be modified\n")

    # Find all Python files
    src_files = find_python_files(SRC_DIR)
    test_files = find_python_files(PROJECT_ROOT / "tests")
    tool_files = find_python_files(PROJECT_ROOT / "tools")

    all_files = src_files + test_files + tool_files

    print(f"\nFound {len(all_files)} Python files")
    print(f"  - src/: {len(src_files)}")
    print(f"  - tests/: {len(test_files)}")
    print(f"  - tools/: {len(tool_files)}")

    # Update files
    print("\n" + "=" * 70)
    print("Updating imports...")
    print("=" * 70)

    total_changes = 0
    files_updated = 0

    for file_path in all_files:
        rel_path = file_path.relative_to(PROJECT_ROOT)
        success, changes = update_file(file_path, dry_run)

        if changes > 0:
            files_updated += 1
            total_changes += changes
            status = "[DRY RUN]" if dry_run else "✅"
            print(f"{status} {rel_path}: {changes} imports updated")

    print("\n" + "=" * 70)
    print("Summary")
    print("=" * 70)
    print(f"Files processed: {len(all_files)}")
    print(f"Files updated: {files_updated}")
    print(f"Total import changes: {total_changes}")
    print("=" * 70)

    if not dry_run and total_changes > 0:
        print("\n🧪 Running tests...")
        try:
            result = subprocess.run(
                ["python3", "-m", "pytest", "-q", "--tb=line"],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                timeout=120
            )
            output = result.stdout + result.stderr

            if "134 passed" in output:
                print("✅ Tests passed!")
            else:
                print("⚠️  Some test issues (check output):")
                print(output[-500:])

        except Exception as e:
            print(f"⚠️  Test run failed: {e}")

        print("\n💾 Committing changes...")
        try:
            subprocess.run(["git", "add", "-A"], cwd=PROJECT_ROOT, check=True)
            subprocess.run(
                ["git", "commit", "-m", "refactor: update all imports to new module structure"],
                cwd=PROJECT_ROOT,
                check=True
            )
            print("✅ Committed")
        except subprocess.CalledProcessError as e:
            print(f"⚠️  Commit failed: {e}")

    elif dry_run:
        print("\n💡 Run without --dry-run to execute updates")


if __name__ == "__main__":
    main()
