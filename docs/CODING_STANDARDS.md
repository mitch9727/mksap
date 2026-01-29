# MKSAP Coding Standards & Best Practices

**Last Updated**: January 23, 2026
**Scope**: All Python code in statement_generator/
**Audience**: Claude Code, AI assistants, and human developers
**Category**: Living Documentation (update as patterns evolve)

---

## Core Principles

1. **Readability First**: Code is read more often than written
2. **DRY (Don't Repeat Yourself)**: Consolidate duplicated logic
3. **YAGNI (You Aren't Gonna Need It)**: Don't build for hypothetical future requirements
4. **Fail Fast**: Validate inputs early, use type hints
5. **Test Coverage**: Unit tests for all non-trivial logic

---

## Naming Conventions

### Files & Modules
- **snake_case** for all Python files: `guidance_formatter.py`, `nlp_utils.py`
- **Descriptive names**: `critique.py` (extractor) vs `critique_checks.py` (validator)
- **Plurals for collections**: `validators/`, `providers/`, `extractors/`

### Classes
- **PascalCase**: `NLPGuidanceFormatter`, `ProviderRegistry`, `CritiqueProcessor`
- **Suffixes for roles**:
  - `*Processor` for extractors (CritiqueProcessor, KeyPointsProcessor)
  - `*Validator` for validators (AtomicityValidator, QualityValidator)
  - `*Provider` for LLM clients (AnthropicProvider, ClaudeCodeProvider)
  - `*Registry` for registries (ProviderRegistry, ValidatorRegistry)

### Functions & Methods
- **snake_case**: `format_nlp_guidance()`, `get_key_entities()`
- **Verb-first**: `extract_statements()`, `validate_structure()`, `normalize_text()`
- **Private methods**: `_internal_helper()` (leading underscore)

### Variables
- **snake_case**: `statement_text`, `cloze_candidates`, `validation_result`
- **Descriptive**: `entity_count` not `cnt`, `is_valid` not `ok`
- **Constants**: `UPPER_SNAKE_CASE` for module-level constants

---

## Architectural Patterns

### Dependency Injection
```python
# Good: Dependencies injected via constructor
class StatementPipeline:
    def __init__(self, client: ClaudeClient, file_io: QuestionFileIO):
        self.client = client
        self.file_io = file_io

# Bad: Direct instantiation inside class
class StatementPipeline:
    def __init__(self):
        self.client = ClaudeClient()  # Hard to test, hard to swap
```

### Factory Pattern (Registries)
```python
# Use registry pattern for extensibility
class ProviderRegistry:
    _providers = {}

    @classmethod
    def register(cls, name: str, provider_class):
        cls._providers[name] = provider_class
```

### Composition Over Inheritance
```python
# Good: Composition with shared utility
class CritiqueProcessor:
    def __init__(self):
        self.formatter = NLPGuidanceFormatter()  # Shared utility

    def _format_nlp_guidance(self, context):
        return self.formatter.format(context, max_entities=15)

# Bad: Duplicating logic in each processor
class CritiqueProcessor:
    def _format_nlp_guidance(self, context):
        # 200 lines of formatting logic duplicated across files
```

### Fail Fast with Type Hints
```python
# Good: Type hints + early validation
def extract_statements(
    self,
    source_text: str,
    objective: str = "",
    nlp_context: Optional[EnrichedPromptContext] = None
) -> List[Statement]:
    if not source_text:
        raise ValueError("source_text cannot be empty")
    # ... processing logic

# Bad: No types, late failure
def extract_statements(self, source_text, objective="", nlp_context=None):
    # Fails deep in processing when source_text is None
```

---

## Error Handling

### Use Specific Exceptions
```python
# Good: Specific exceptions
class ValidationError(Exception):
    pass

class NLPModelNotFoundError(Exception):
    pass

# Bad: Generic exceptions
raise Exception("Something went wrong")  # Unhelpful
```

### Fail Gracefully for Optional Features
```python
# Good: Degrade gracefully if NLP unavailable
nlp = get_nlp()
if nlp is None:
    logger.warning("NLP model unavailable, skipping entity extraction")
    return []  # Continue without NLP

# Bad: Crash if optional feature unavailable
nlp = get_nlp()  # Raises if not available
doc = nlp(text)  # Crashes entire pipeline
```

---

## Performance Best Practices

### Use Caching for Expensive Operations
```python
from functools import lru_cache

# Good: Cache expensive model loading
@lru_cache(maxsize=1)
def get_nlp():
    return spacy.load("en_core_sci_sm")

# Good: Cache document parsing
@lru_cache(maxsize=1000)
def nlp_cached(text: str):
    nlp = get_nlp()
    return nlp(text)
```

### Avoid Re-instantiating Singletons
```python
# Good: Class-level singleton
class NLPPreprocessor:
    _negation_detector = None  # Shared instance

    def __init__(self):
        if NLPPreprocessor._negation_detector is None:
            NLPPreprocessor._negation_detector = NegationDetector()
        self.negation_detector = NLPPreprocessor._negation_detector

# Bad: New instance per call
class NLPPreprocessor:
    def __init__(self):
        self.negation_detector = NegationDetector()  # New every time
```

### Batch Processing for I/O
```python
# Good: Batch file reads
def read_batch(paths: List[Path]) -> List[dict]:
    return [json.load(open(p)) for p in paths]

# Bad: One-at-a-time in loop
for path in paths:
    data = json.load(open(path))  # Repeated I/O overhead
    process(data)
```

---

## Testing Standards

### Test File Organization
- Tests mirror `src/` structure: `tests/processing/statements/extractors/test_critique.py`
- One test file per source file
- Use `test_*.py` naming

### Test Naming
```python
# Good: Descriptive test names
def test_extract_statements_returns_empty_list_for_empty_input():
    pass

def test_validate_structure_fails_for_missing_required_fields():
    pass

# Bad: Generic test names
def test_1():
    pass

def test_extractor():
    pass
```

### Use Fixtures for Shared Setup
```python
import pytest

@pytest.fixture
def sample_statement():
    return Statement(
        statement="Patient has hypertension",
        cloze_candidates=["hypertension"]
    )

def test_validates_correctly(sample_statement):
    result = validate(sample_statement)
    assert result.valid
```

---

## Documentation Standards

### Docstrings for Public Functions
```python
def extract_statements(
    source_text: str,
    objective: str = "",
    nlp_context: Optional[EnrichedPromptContext] = None
) -> List[Statement]:
    """Extract medical statements from source text.

    Args:
        source_text: Raw text from question critique or key points
        objective: Optional educational objective for context
        nlp_context: Optional NLP preprocessing results for guidance

    Returns:
        List of Statement objects with cloze candidates

    Raises:
        ValueError: If source_text is empty
    """
```

### Inline Comments for Complex Logic
```python
# Use comments to explain "why", not "what"

# Good: Explains reasoning
# Use fuzzy matching with 80% threshold to handle minor variations
# like "hypertension" vs "primary hypertension"
ratio = SequenceMatcher(None, a, b).ratio()
if ratio > 0.8:
    return True

# Bad: States the obvious
# Calculate ratio
ratio = SequenceMatcher(None, a, b).ratio()
# Check if ratio greater than 0.8
if ratio > 0.8:
    return True
```

---

## Import Standards

### Order of Imports
```python
# 1. Standard library
import os
from pathlib import Path
from typing import List, Optional

# 2. Third-party libraries
import spacy
from pydantic import BaseModel

# 3. Local imports (relative)
from ..infrastructure.llm.client import ClaudeClient
from .base import BaseExtractor
```

### Avoid Star Imports
```python
# Good: Explicit imports
from .validators import StructureValidator, QualityValidator

# Bad: Star imports
from .validators import *  # Unclear what's imported
```

---

## Always Update TODO.md

**Critical Rule**: Every feature implementation, bug fix, or architectural change MUST include a TODO.md update.

### When to Update TODO.md
1. **Before starting work**: Check if task is in TODO.md, understand dependencies
2. **During work**: Mark task as in-progress, update with blockers or discoveries
3. **After completion**: Remove completed task, add any follow-up tasks discovered

### Example Workflow
```bash
# 1. Before starting
# Open TODO.md, find task: "Consolidate NLP guidance formatting"

# 2. Mark in-progress (optional, for long tasks)
# Update TODO.md: "🔄 Consolidate NLP guidance formatting (in progress)"

# 3. Complete work
# ... implement changes ...

# 4. Update TODO.md
# Remove task from TODO.md
# Add new task if discovered: "Add unit tests for NLPGuidanceFormatter"

# 5. Update "Last Updated" in TODO.md header
```

### Link to TODO.md from
- `CLAUDE.md:12` - "Single source of truth for active/planned work"
- All phase status docs (PHASE_X_STATUS.md)
- `whats-next.md` - Should reference TODO.md for current priorities

---

## Always Update whats-next.md

**Purpose**: `whats-next.md` is a handoff document for fresh sessions. Keep it synchronized with project progress.

### When to Update whats-next.md
1. **Phase completion**: Mark phase complete, update status
2. **Major milestone**: Add to <work_completed> section
3. **New decision required**: Add to <work_remaining> section
4. **Configuration changes**: Update <critical_context> section

### Relationship to TODO.md
- TODO.md: Granular task list (day/week level)
- whats-next.md: High-level context (phase/month level)
- Both should be kept in sync for current phase status

---

## Code Review Checklist

Before committing code, verify:

- [ ] **Follows naming conventions** (snake_case, PascalCase)
- [ ] **Type hints on public functions**
- [ ] **Docstrings for complex logic**
- [ ] **No code duplication** (extract shared logic to utilities)
- [ ] **Error handling** (specific exceptions, graceful degradation)
- [ ] **Performance patterns** (caching, batching, singletons)
- [ ] **Tests updated** (mirror src/ structure, descriptive names)
- [ ] **TODO.md updated** (task removed or marked complete)
- [ ] **whats-next.md updated** (if phase milestone reached)
- [ ] **Documentation updated** (if API changed or new feature added)

---

## Related Documentation

- [ARCHITECTURE.md](architecture/ARCHITECTURE.md) - System architecture overview
- [DOCUMENTATION_POLICY.md](DOCUMENTATION_POLICY.md) - Documentation guidelines
- [TODO.md](../TODO.md) - Current task tracking
- [whats-next.md](../whats-next.md) - Session handoff context

---

**This document is a living standard. Update as patterns evolve.**
