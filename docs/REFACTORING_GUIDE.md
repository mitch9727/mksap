# Refactoring Guide - Implementation Patterns

**Last Updated**: January 23, 2026
**Category**: Living Documentation
**Purpose**: Step-by-step guide for implementing improvements from January 23, 2026 audit

---

## Overview

This guide provides detailed implementation patterns for refactorings identified in the comprehensive codebase audit. Use this as a reference when implementing future improvements or training new developers.

**Related Documentation**:
- [Audit Plan](.claude/plans/splendid-herding-sutherland.md) - Original audit findings
- [Audit Implementation Summary](../statement_generator/artifacts/AUDIT_IMPLEMENTATION_SUMMARY.md) - What's been completed
- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture overview
- [CODING_STANDARDS.md](CODING_STANDARDS.md) - Python best practices

---

## Completed Refactorings (January 23, 2026)

### ✅ 1. NLP Guidance Consolidation (Finding 1.1)

**Problem**: Duplicate `_format_nlp_guidance()` logic in critique.py and keypoints.py (~200 lines)

**Solution**: Created shared formatter module

**Implementation**:
```python
# 1. Created: src/processing/nlp/guidance_formatter.py
def format_nlp_guidance(
    context: EnrichedPromptContext,
    include_atomicity: bool = True,
    max_entities: int = 15,
) -> str:
    """Shared NLP guidance formatting."""
    sections = []
    if context.entity_summary:
        sections.append(f"**Detected Entities**: {context.entity_summary}")
    if context.negation_summary:
        sections.append(f"**CRITICAL - Negations Detected**: {context.negation_summary}")
    # ... more sections
    return "\n\n".join(sections)

# 2. Updated: src/processing/statements/extractors/critique.py
from ...nlp.guidance_formatter import format_nlp_guidance

class CritiqueProcessor:
    def _format_nlp_guidance(self, context):
        return format_nlp_guidance(context, max_entities=15)

# 3. Updated: src/processing/statements/extractors/keypoints.py
from ...nlp.guidance_formatter import format_nlp_guidance

class KeyPointsProcessor:
    def _format_nlp_guidance(self, context):
        return format_nlp_guidance(context, max_entities=10)
```

**Benefits**:
- Eliminated 200 lines of duplication
- Single place to modify NLP guidance
- Configurable per extractor (max_entities parameter)

**Testing**:
```bash
# Verify output identical before/after
./scripts/python -m src.interface.cli process --question-id cvmcq24001
# Compare true_statements field in JSON
```

---

### ✅ 2. Provider Registry Pattern (Finding 1.3)

**Problem**: 40-line if-elif chain in client.py for provider instantiation

**Solution**: Registry pattern with self-registration

**Implementation**:
```python
# 1. Created: src/infrastructure/llm/providers/registry.py
from typing import Dict, Type
from .base_provider import BaseLLMProvider

class ProviderRegistry:
    _providers: Dict[str, Type[BaseLLMProvider]] = {}

    @classmethod
    def register(cls, name: str, provider_class: Type[BaseLLMProvider]):
        """Register a provider by name."""
        cls._providers[name] = provider_class

    @classmethod
    def create(cls, name: str, **kwargs) -> BaseLLMProvider:
        """Create provider instance by name."""
        if name not in cls._providers:
            available = ", ".join(cls._providers.keys())
            raise ValueError(f"Unknown provider '{name}'. Available: {available}")
        return cls._providers[name](**kwargs)

    @classmethod
    def list_providers(cls) -> list[str]:
        """List registered provider names."""
        return list(cls._providers.keys())

# 2. Updated: Each provider file (anthropic.py, claude_code.py, etc.)
class AnthropicProvider(BaseLLMProvider):
    # ... implementation

# Self-register at module load
from .registry import ProviderRegistry
ProviderRegistry.register("anthropic", AnthropicProvider)

# 3. Updated: src/infrastructure/llm/client.py
from .providers.registry import ProviderRegistry

def _create_provider(config: LLMConfig) -> BaseLLMProvider:
    """Create provider from config."""
    return ProviderRegistry.create(config.provider, config=config)
```

**Benefits**:
- Simplified client.py from 40 lines to 1 line
- Easy to add new providers (no client.py changes)
- Better error messages (shows available providers)
- Testable (can list providers, mock registry)

**Testing**:
```python
# tests/test_provider_registry.py
def test_all_providers_registered():
    providers = ProviderRegistry.list_providers()
    assert "anthropic" in providers
    assert "claude-code" in providers
    assert "gemini" in providers
    assert "codex" in providers

def test_create_unknown_provider_raises():
    with pytest.raises(ValueError) as exc:
        ProviderRegistry.create("unknown")
    assert "Available: anthropic, claude-code" in str(exc.value)
```

---

### ✅ 3. Validator Registry Pattern (Finding 1.2)

**Problem**: Validation logic split across two hierarchies, hardcoded validator calls

**Solution**: Centralized validator registry with enable/disable control

**Implementation**:
```python
# 1. Created: src/validation/registry.py
from typing import List, Protocol
from .validator import ValidationIssue
from ..infrastructure.models.data_models import Statement

class BaseValidator(Protocol):
    enabled: bool = True

    def validate(self, statement: Statement, context: dict) -> List[ValidationIssue]:
        """Validate statement and return issues."""
        ...

class ValidatorRegistry:
    _validators: List[BaseValidator] = []

    @classmethod
    def register(cls, validator_class):
        """Register a validator."""
        cls._validators.append(validator_class())

    @classmethod
    def validate_all(cls, statement: Statement, context: dict) -> List[ValidationIssue]:
        """Run all enabled validators."""
        issues = []
        for validator in cls._validators:
            if validator.enabled:
                issues.extend(validator.validate(statement, context))
        return issues

# 2. Auto-register validators at module load
# At bottom of src/validation/quality_checks.py:
ValidatorRegistry.register(QualityValidator)

# 3. Updated: src/validation/validator.py
from .registry import ValidatorRegistry

def validate_statement(statement: Statement, context: dict) -> List[ValidationIssue]:
    """Validate using registry."""
    return ValidatorRegistry.validate_all(statement, context)
```

**Benefits**:
- Centralized validator management
- Easy to enable/disable specific validators
- Consistent interface for all validators
- Auto-registration (no manual list maintenance)

**Testing**:
```python
def test_all_validators_registered():
    # Should have 11 validators
    assert len(ValidatorRegistry._validators) == 11

def test_disable_validator():
    validator = ValidatorRegistry._validators[0]
    validator.enabled = False
    # Validator should not run
```

---

### ✅ 4. NLP Analyzer Singletons (Finding 1.5)

**Problem**: Creating new analyzer instances for every question (memory churn)

**Solution**: Class-level singletons shared across instances

**Implementation**:
```python
# Updated: src/processing/nlp/preprocessor.py
class NLPPreprocessor:
    # Class-level shared instances (initialized once)
    _negation_detector: Optional[NegationDetector] = None
    _atomicity_analyzer: Optional[AtomicityAnalyzer] = None

    def __init__(self, config: Optional[NLPConfig] = None):
        self.config = config or NLPConfig.from_env()
        self._nlp = None  # Lazy-loaded spaCy model

        # Initialize singletons on first instantiation
        if NLPPreprocessor._negation_detector is None:
            NLPPreprocessor._negation_detector = NegationDetector()
            NLPPreprocessor._atomicity_analyzer = AtomicityAnalyzer()

        # Reference shared instances
        self.negation_detector = NLPPreprocessor._negation_detector
        self.atomicity_analyzer = NLPPreprocessor._atomicity_analyzer
```

**Benefits**:
- Reduced per-question instantiation overhead
- Memory efficiency (2,198 questions → 3 analyzer instances instead of 6,594)
- Estimated savings: 10-20 seconds for full batch

**Testing**:
```python
def test_nlp_analyzers_are_singletons():
    preprocessor1 = NLPPreprocessor()
    preprocessor2 = NLPPreprocessor()

    # Should reference same instances
    assert preprocessor1.negation_detector is preprocessor2.negation_detector
    assert preprocessor1.atomicity_analyzer is preprocessor2.atomicity_analyzer
```

---

### ✅ 5. Shared Retry Logic (Finding 1.4)

**Problem**: Duplicate retry logic in all 4 providers (~50-100 lines each)

**Solution**: Extract to base class with jitter support

**Implementation**:
```python
# Updated: src/infrastructure/llm/base_provider.py
import time
import random
from typing import Callable, TypeVar

T = TypeVar('T')

class BaseLLMProvider(ABC):
    def _retry_with_backoff(
        self,
        func: Callable[[], T],
        max_retries: int = 3,
        jitter: bool = True
    ) -> T:
        """Retry with exponential backoff and optional jitter."""
        for attempt in range(max_retries):
            try:
                return func()
            except Exception as e:
                if attempt < max_retries - 1:
                    delay = 2**attempt
                    if jitter:
                        delay += random.uniform(0, 1)  # Add jitter
                    logger.debug(f"Retry {attempt+1}/{max_retries} after {delay:.2f}s")
                    time.sleep(delay)
                else:
                    raise

# Updated: Each provider (anthropic.py, etc.)
class AnthropicProvider(BaseLLMProvider):
    def generate(self, prompt: str, **kwargs) -> str:
        return self._retry_with_backoff(
            lambda: self._call_api(prompt, **kwargs)
        )
```

**Benefits**:
- Eliminated ~50-100 lines of duplicate code per provider
- Consistent retry behavior across all providers
- Easy to add jitter or change backoff strategy
- Single place to fix retry bugs

---

## Future Refactoring Opportunities

### ⚠️ 6. Enable Async LLM Calls (Not Completed)

**Status**: Infrastructure exists but not operational (needs 4-8 hours)

**Problem**: Sequential LLM calls are the primary bottleneck (60-70% of time)

**Solution**: Convert pipeline to async and use `asyncio.gather()`

**Implementation Plan**:

**Step 1: Make pipeline async**
```python
# Update: src/orchestration/pipeline.py
import asyncio

class StatementPipeline:
    async def process_question_async(self, question_file: Path) -> ProcessingResult:
        """Process question with concurrent LLM calls."""
        data = self.file_io.read_question(question_file)

        # Run critique and keypoints extraction concurrently
        critique_task = self.critique_processor.extract_statements_async(
            data["critique"], data.get("educational_objective", "")
        )
        keypoints_task = self.keypoints_processor.extract_statements_async(
            data.get("key_points", [])
        )

        # Wait for both to complete
        critique_stmts, keypoint_stmts = await asyncio.gather(
            critique_task, keypoints_task
        )

        # Continue with sequential steps (NLP, validation)
        # ...
```

**Step 2: Make extractors async**
```python
# Update: src/processing/statements/extractors/critique.py
class CritiqueProcessor:
    async def extract_statements_async(self, source_text: str, objective: str = "") -> List[Statement]:
        """Async version of extract_statements."""
        # Use async LLM client
        response = await self.client.generate_async(prompt, **kwargs)
        # ... rest of logic
```

**Step 3: Update CLI to use asyncio**
```python
# Update: src/interface/cli.py
import asyncio

@click.command()
def process(...):
    pipeline = StatementPipeline(...)
    for question_file in question_files:
        result = asyncio.run(pipeline.process_question_async(question_file))
        # ...
```

**Expected Impact**: 3-5x speedup (if using Anthropic API)

**Gotchas**:
- Need to handle API rate limits (may need throttling)
- Codex CLI provider won't benefit much (uses executor fallback)
- More complex error handling
- Testing becomes more complex (async mocks)

**See**: [ASYNC_IMPLEMENTATION.md](../statement_generator/docs/ASYNC_IMPLEMENTATION.md) for full details

---

### 7. Replace NegationDetector with negspacy (Audit Recommendation)

**Status**: Not started

**Problem**: Custom regex-based negation detection (~200 lines), may miss complex cases

**Solution**: Replace with battle-tested `negspacy` library

**Implementation**:
```bash
# 1. Install negspacy
poetry add negspacy
```

```python
# 2. Update: src/processing/nlp/preprocessor.py
import spacy
from negspacy.negation import Negex

def get_nlp():
    nlp = spacy.load("en_core_sci_sm")
    nlp.add_pipe("negex", config={"ent_types": ["ENTITY"]})
    return nlp

# 3. Replace NegationDetector usage
doc = nlp(text)
for ent in doc.ents:
    if ent._.negex:  # Built-in negation detection
        negations.append({
            "entity": ent.text,
            "negated": True,
            "trigger": ent._.negex  # Negation trigger word
        })

# 4. Remove: src/processing/nlp/negation_detector.py (obsolete)
```

**Benefits**:
- More accurate negation detection
- Handles complex scopes ("neither...nor", nested clauses)
- Reduced maintenance burden (~200 lines removed)
- Battle-tested library

**Testing**:
- Compare negation detection on 14 test questions
- Verify negation preservation rate remains 100%
- Check for any regressions

**Effort**: ~4 hours

---

### 8. Persistent Cache with Redis (Future)

**Status**: Not started

**Problem**: In-memory cache doesn't survive process restarts

**Solution**: Use Redis for persistent LLM response cache

**Implementation**:
```bash
# 1. Install redis client
poetry add redis
```

```python
# 2. Create: src/infrastructure/cache/redis_cache.py
import redis
import hashlib

class RedisLLMCache:
    def __init__(self, host='localhost', port=6379, ttl=3600):
        self.client = redis.Redis(host=host, port=port, decode_responses=True)
        self.ttl = ttl

    def get(self, prompt: str, model: str, temperature: float) -> Optional[str]:
        key = self._make_key(prompt, model, temperature)
        return self.client.get(key)

    def set(self, prompt: str, model: str, temperature: float, response: str):
        key = self._make_key(prompt, model, temperature)
        self.client.setex(key, self.ttl, response)

    def _make_key(self, prompt: str, model: str, temperature: float) -> str:
        return f"llm:{hashlib.md5(f'{prompt}{model}{temperature}'.encode()).hexdigest()}"

# 3. Update: src/infrastructure/llm/client.py
from .cache.redis_cache import RedisLLMCache

class ClaudeClient:
    def __init__(self, config):
        if config.use_redis_cache:
            self.cache = RedisLLMCache()
        else:
            self.cache = LLMCache()  # In-memory fallback
```

**Benefits**:
- Cache survives process restarts
- Share cache across multiple runs/sessions
- 10-20% speedup on re-runs (vs 5-15% in-memory)

**Gotchas**:
- Requires Redis server running
- Additional infrastructure dependency
- May need Redis auth in production

**Effort**: ~1 day

---

## Testing Patterns

### Testing Registries

**Pattern**: Verify all expected items are registered

```python
def test_provider_registry_has_all_providers():
    providers = ProviderRegistry.list_providers()
    assert len(providers) == 4
    assert "anthropic" in providers
    assert "claude-code" in providers
    assert "gemini" in providers
    assert "codex" in providers

def test_validator_registry_has_all_validators():
    validators = ValidatorRegistry._validators
    assert len(validators) == 11  # Update when adding validators
```

### Testing Singletons

**Pattern**: Verify instances are reused

```python
def test_nlp_preprocessor_uses_singletons():
    p1 = NLPPreprocessor()
    p2 = NLPPreprocessor()
    assert p1.negation_detector is p2.negation_detector
    assert p1.atomicity_analyzer is p2.atomicity_analyzer
```

### Testing Refactored Code

**Pattern**: Compare outputs before/after refactoring

```python
def test_nlp_guidance_formatter_produces_identical_output():
    # Read question
    question = load_question("cvmcq24001")

    # Process with old code (if available)
    old_output = process_old(question)

    # Process with refactored code
    new_output = process_new(question)

    # Compare
    assert old_output["true_statements"] == new_output["true_statements"]
    assert old_output["validation_pass"] == new_output["validation_pass"]
```

---

## Rollback Plan

### If Refactoring Breaks Something

1. **Identify the issue**:
   ```bash
   # Check validation pass rate
   grep -r "validation_pass.*false" mksap_data/ | wc -l
   ```

2. **Git revert to last good commit**:
   ```bash
   git log --oneline  # Find last good commit
   git revert <commit-hash>
   ```

3. **Or temporarily disable feature**:
   ```bash
   # Disable cache
   export MKSAP_LLM_CACHE_ENABLED=0

   # Disable validator
   # In code: validator.enabled = False
   ```

4. **Run tests to verify rollback**:
   ```bash
   pytest -n auto
   ./scripts/python -m src.interface.cli process --limit 10
   ```

---

## Refactoring Checklist

Before merging any refactoring:

- [ ] Tests pass (pytest -n auto)
- [ ] Integration test passes (process 1 question)
- [ ] Output identical to before refactoring (diff JSON)
- [ ] Validation pass rate unchanged
- [ ] No new errors in logs
- [ ] Documentation updated
- [ ] TODO.md updated
- [ ] Performance measured (if optimization)
- [ ] Rollback plan documented

---

## Related Documentation

- [Audit Plan](.claude/plans/splendid-herding-sutherland.md) - Original findings
- [Audit Implementation Summary](../statement_generator/artifacts/AUDIT_IMPLEMENTATION_SUMMARY.md) - What's done
- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture
- [CODING_STANDARDS.md](CODING_STANDARDS.md) - Python best practices
- [PERFORMANCE_OPTIMIZATION.md](PERFORMANCE_OPTIMIZATION.md) - Profiling guide

---

**Last Updated**: January 23, 2026
**Next Review**: After implementing next refactoring
