# MKSAP Statement Generator - System Architecture

**Last Updated**: January 23, 2026
**Category**: Living Documentation
**Purpose**: High-level architecture overview for quick project orientation

---

## System Overview

The MKSAP Medical Education Pipeline is a multi-phase system for extracting medical education flashcards from the ACP MKSAP question bank (2,198 questions).

**Current Phase**: Phase 4 (Production Deployment) - Ready to execute
**Architecture Date**: Reorganized January 15, 2026 | Optimized January 23, 2026

---

## Project Structure (High-Level)

```
MKSAP/
├── extractor/                  # Phase 1: Rust question extractor
├── mksap_data/                 # Extracted questions (2,198 JSON files)
├── statement_generator/        # Phase 2-4: Python statement processing
├── anking_analysis/            # Anking deck comparison tools
├── docs/                       # Project-level documentation
└── scripts/                    # Utility scripts
```

---

## Phase Overview

### Phase 1: Rust Extractor (Complete ✅)
**Goal**: Extract 2,198 questions from MKSAP API to JSON
**Status**: Complete - January 15, 2026
**Output**: `mksap_data/` directory with 2,198 JSON files

### Phase 2: Statement Generator (Complete ✅)
**Goal**: Extract medical statements from questions using LLM
**Status**: Complete - January 16, 2026
**Output**: Python pipeline with hybrid NLP+LLM processing

### Phase 3: Validation (Complete ✅)
**Goal**: Validate statement quality with automated checks
**Status**: Complete - January 16, 2026
**Output**: 92.9% validation pass rate, NLP metadata persistence

### Phase 4: Production Deployment (In Progress ⚡)
**Goal**: Process all 2,198 questions with optimized pipeline
**Status**: Optimization complete, ready for production run
**ETA**: 20-53 hours (depending on async enablement)

### Phase 5: Cloze Application (Planned 📋)
**Goal**: Apply cloze blanks based on `cloze_candidates`
**Status**: Not started

### Phase 6: Anki Export (Planned 📋)
**Goal**: Export to .apkg file for Anki import
**Status**: Not started

---

## Statement Generator Architecture (Phase 2-4)

### Layered Architecture (4 Layers)

```
┌─────────────────────────────────────────────────────────┐
│                    Interface Layer                       │
│                   (CLI Entry Point)                      │
│                                                          │
│  src/interface/cli.py - Commands: process, stats, reset │
└────────────────┬─────────────────────────────────────────┘
                 │
┌────────────────▼─────────────────────────────────────────┐
│                 Orchestration Layer                      │
│            (Pipeline & State Management)                 │
│                                                          │
│  src/orchestration/                                      │
│  ├── pipeline.py - StatementPipeline (main workflow)    │
│  └── checkpoint.py - State tracking & resumability      │
└────────────────┬─────────────────────────────────────────┘
                 │
┌────────────────▼─────────────────────────────────────────┐
│                  Processing Layer                        │
│             (Feature Modules by Domain)                  │
│                                                          │
│  src/processing/                                         │
│  ├── statements/                                         │
│  │   ├── extractors/ - Critique & keypoints extraction  │
│  │   └── validators/ - [Legacy, being consolidated]     │
│  ├── cloze/ - Cloze candidate identification            │
│  ├── tables/ - Table extraction & processing            │
│  ├── normalization/ - Text cleaning                     │
│  └── nlp/ - NLP preprocessing                           │
│      ├── guidance_formatter.py - Shared NLP formatting  │
│      └── preprocessor.py - spaCy integration            │
└────────────────┬─────────────────────────────────────────┘
                 │
┌────────────────▼─────────────────────────────────────────┐
│               Infrastructure Layer                       │
│          (Cross-Cutting Concerns)                        │
│                                                          │
│  src/infrastructure/                                     │
│  ├── llm/ - LLM provider abstraction                    │
│  │   ├── client.py - Multi-provider wrapper            │
│  │   ├── base_provider.py - Provider interface         │
│  │   └── providers/                                     │
│  │       ├── registry.py - Provider factory (NEW!)     │
│  │       ├── anthropic.py - Anthropic API              │
│  │       ├── claude_code.py - Claude Code CLI          │
│  │       ├── gemini.py - Google Gemini                 │
│  │       └── codex.py - OpenAI Codex                   │
│  ├── cache/ - Performance optimization (NEW!)           │
│  │   └── llm_cache.py - TTL-based response cache       │
│  ├── io/ - File operations                             │
│  │   └── file_handler.py - JSON I/O (uses orjson)      │
│  ├── config/ - Configuration management                 │
│  │   └── settings.py - Environment variable loading    │
│  └── models/ - Data models (Pydantic)                  │
│      └── data_models.py - Statement, Question schemas  │
└────────────────┬─────────────────────────────────────────┘
                 │
┌────────────────▼─────────────────────────────────────────┐
│                  Validation Framework                    │
│            (Quality Checks - Consolidated)               │
│                                                          │
│  src/validation/                                         │
│  ├── registry.py - ValidatorRegistry (NEW!)             │
│  ├── validator.py - Main orchestrator                   │
│  ├── structure_checks.py - JSON schema validation       │
│  ├── quality_checks.py - Atomicity, vague language      │
│  ├── ambiguity_checks.py - Medication, numeric clarity  │
│  ├── cloze_checks.py - Cloze candidate quality         │
│  ├── context_checks.py - Extra field quality (NEW!)    │
│  ├── enumeration_checks.py - List handling             │
│  ├── hallucination_checks.py - Source fidelity         │
│  └── nlp_utils.py - NLP helper functions               │
└──────────────────────────────────────────────────────────┘
```

---

## Data Flow

### Input → Output Pipeline

```
┌──────────────┐
│ Question JSON│  (from Phase 1 extractor)
│  (mksap_data)│
└──────┬───────┘
       │
       ▼
┌──────────────────────────────────────────────────────────┐
│ 1. NLP Preprocessing (Optional but Recommended)          │
│    - Entity extraction (medications, conditions, tests)  │
│    - Negation detection (NOT, negative, denies)         │
│    - Atomicity analysis (single fact per sentence)       │
│    - Sentence segmentation                               │
└──────┬───────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────┐
│ 2. Statement Extraction (LLM)                            │
│    a. Critique Processor                                 │
│       - Extracts statements from critique field          │
│       - NLP guidance: entities, negations, atomicity     │
│       - Output: List[Statement] with cloze candidates    │
│                                                          │
│    b. Key Points Processor                               │
│       - Extracts statements from key_points field        │
│       - NLP guidance: key entities, structure            │
│       - Output: List[Statement] with cloze candidates    │
│                                                          │
│    c. Table Processor (if tables present)               │
│       - Extracts statements from markdown tables         │
│       - Output: List[TableStatement]                     │
└──────┬───────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────┐
│ 3. Validation Framework                                  │
│    - Structure checks (required fields, types)           │
│    - Quality checks (atomicity, vague language)          │
│    - Ambiguity checks (medication, numeric clarity)      │
│    - Cloze checks (candidate quality, count)             │
│    - Context checks (extra_field quality)                │
│    - Enumeration checks (list handling)                  │
│    - Hallucination checks (source fidelity)              │
│    → Output: validation_pass boolean + issues list       │
└──────┬───────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────┐
│ 4. Output Writing                                        │
│    - Add true_statements field to JSON                   │
│    - Add validation_pass field                           │
│    - Add nlp_analysis metadata (if NLP enabled)          │
│    - Write back to same file (non-destructive append)    │
└──────┬───────────────────────────────────────────────────┘
       │
       ▼
┌──────────────┐
│Enhanced JSON │  (ready for Phase 5: Cloze application)
│  (mksap_data)│
└──────────────┘
```

---

## Key Architectural Patterns

### 1. Provider Registry Pattern (NEW - Jan 23, 2026)

**Location**: `src/infrastructure/llm/providers/registry.py`

**Purpose**: Dynamic LLM provider registration and instantiation

```python
# Providers self-register on import
# anthropic.py
ProviderRegistry.register("anthropic", AnthropicProvider)

# Client creates providers via registry
provider = ProviderRegistry.create(config.provider, config=config)
```

**Benefits**:
- Easy to add new providers (no client.py changes)
- Better error messages (shows available providers)
- Testable and mockable

### 2. Validator Registry Pattern (NEW - Jan 23, 2026)

**Location**: `src/validation/registry.py`

**Purpose**: Centralized validator management with enable/disable control

```python
# Validators auto-register on module load
ValidatorRegistry.register(StructureValidator)
ValidatorRegistry.register(QualityValidator)

# Validate all at once
issues = ValidatorRegistry.validate_all(statement, context)
```

**Benefits**:
- Enable/disable specific validators
- Easier to add new validators
- Consistent validation interface

### 3. Shared Formatter Pattern (NEW - Jan 23, 2026)

**Location**: `src/processing/nlp/guidance_formatter.py`

**Purpose**: Consolidate duplicate NLP guidance formatting

```python
# Both extractors use shared formatter
formatter = NLPGuidanceFormatter()
guidance = formatter.format_nlp_guidance(context, max_entities=15)
```

**Benefits**:
- Eliminated ~200 lines of duplication
- Single place to modify NLP guidance
- Consistent formatting across extractors

### 4. Singleton Pattern for NLP Analyzers (NEW - Jan 23, 2026)

**Location**: `src/processing/nlp/preprocessor.py`

**Purpose**: Reuse expensive analyzer instances across questions

```python
class NLPPreprocessor:
    _negation_detector = None  # Class-level singleton

    def __init__(self):
        if NLPPreprocessor._negation_detector is None:
            NLPPreprocessor._negation_detector = NegationDetector()
        self.negation_detector = NLPPreprocessor._negation_detector
```

**Benefits**:
- Reduced per-question instantiation overhead
- Memory efficiency

### 5. Cache Layer Pattern (NEW - Jan 23, 2026)

**Location**: `src/infrastructure/cache/llm_cache.py`

**Purpose**: TTL-based caching of LLM responses

```python
# Automatic caching in client
cache_key = hashlib.md5(f"{prompt}{model}{temperature}".encode()).hexdigest()
if cache_key in cache:
    return cache[cache_key]
response = provider.generate(prompt)
cache[cache_key] = response
```

**Benefits**:
- 5-15% speedup on re-runs
- Reduces API costs
- Transparent to callers

---

## Technology Stack

### Languages
- **Python 3.10+** - Statement generator (Phase 2-6)
- **Rust** - Question extractor (Phase 1)

### Python Dependencies (Key)
- **anthropic** - Anthropic API client
- **pydantic** - Data validation and models
- **spacy + scispacy** - NLP processing (entity extraction, negation)
- **aiohttp** - Async HTTP (for future async LLM calls)
- **cachetools** - TTL-based caching
- **orjson** - Fast JSON serialization (3-4x faster than json)
- **click** - CLI framework
- **pytest + pytest-xdist** - Testing (parallel execution)

### External Services
- **Anthropic Claude API** - LLM provider (or Gemini, Codex, Claude Code CLI)
- **MKSAP API** - Question source (Phase 1 only)

---

## Configuration

### Environment Variables (.env)

**Critical Settings**:
```bash
# LLM Provider
LLM_PROVIDER=codex                    # anthropic | claude-code | gemini | codex
ANTHROPIC_API_KEY=sk-...              # If using Anthropic

# NLP Model
USE_HYBRID_PIPELINE=true              # Enable NLP preprocessing
MKSAP_NLP_MODEL=/absolute/path/to/en_core_sci_sm

# Performance
MKSAP_LLM_CACHE_ENABLED=1             # Enable response cache
MKSAP_LLM_CACHE_TTL=3600              # Cache TTL (1 hour)

# Data Paths
MKSAP_DATA_ROOT=/Users/Mitchell/coding/projects/MKSAP/mksap_data

# Python
MKSAP_PYTHON_VERSION=3.13.5
```

**See**: `.env.template` for full list

---

## Performance Characteristics

### Current Performance (January 2026)

**With all optimizations enabled**:
- **~87 seconds per question** (sequential processing)
- **~53 hours for full 2,198 questions**
- **Memory usage**: ~200-300MB

**Optimizations active**:
- ✅ orjson (2-3% speedup)
- ✅ @lru_cache decorators (5% speedup)
- ✅ LLM response cache (5-15% on re-runs)
- ✅ NLP document cache (5-10% speedup)
- ✅ NLP analyzer singletons (<1% speedup)

**Total speedup**: ~12-18% + cache benefits

### Bottleneck Analysis (Expected)

- **LLM API calls**: 60-70% of total time
- **NLP processing**: 15-20%
- **Validation**: <10%
- **JSON I/O**: 2-3%
- **Everything else**: <5%

**See**: [PERFORMANCE_OPTIMIZATION.md](PERFORMANCE_OPTIMIZATION.md) for profiling guide

---

## Deployment Models

### Sequential Processing (Current)
- Process questions one at a time
- Simple, reliable, easy to debug
- ~53 hours for full dataset

### Async Processing (Infrastructure Ready)
- Infrastructure exists but not operational
- Would require 4-8 hours to enable
- Expected: 3-5x speedup (15-20 hours for full dataset)
- See: [ASYNC_IMPLEMENTATION.md](../statement_generator/docs/ASYNC_IMPLEMENTATION.md)

### Multiprocessing (Future)
- Process questions in parallel (different processes)
- Use `multiprocessing.Pool` with 4-8 workers
- Expected: 3-4x speedup (13-18 hours for full dataset)

---

## Quality Metrics

### Validation Framework

**Pass Rate Targets**:
- **Phase 3 baseline**: 92.9% (13/14 questions)
- **Phase 4 target**: ≥90% across all 2,198 questions
- **Red flag**: <85% pass rate

**Validation Categories** (11 validators):
1. **Structure** - JSON schema, required fields
2. **Quality** - Atomicity, vague language, board relevance
3. **Ambiguity** - Medication, numeric, organism clarity
4. **Cloze** - Candidate count, uniqueness, triviality
5. **Context** - Extra field quality, embedded reasoning (NEW!)
6. **Enumeration** - List handling, multi-item clozes
7. **Hallucination** - Source fidelity checks

### NLP Metrics (Hybrid Pipeline)

- **Negation preservation**: 100% (critical for accuracy)
- **Entity completeness**: 100%
- **Unit accuracy**: 100%

---

## Testing Strategy

### Unit Tests
- Location: `statement_generator/tests/`
- Mirror `src/` structure
- Use fixtures for shared setup
- Run with: `pytest -n auto` (parallel execution)

### Integration Tests
- Test full pipeline on sample questions
- Verify validation pass rate
- Check statement quality against best practices

### Regression Tests
- Compare outputs before/after refactoring
- Ensure optimizations don't change behavior
- Verify cache correctness

---

## Documentation Structure

### Project-Level (`docs/`)
- **INDEX.md** - Documentation index
- **ARCHITECTURE.md** - This file (system overview)
- **CODING_STANDARDS.md** - Python best practices
- **PERFORMANCE_OPTIMIZATION.md** - Profiling and benchmarking
- **REFACTORING_GUIDE.md** - Implementation guide for improvements
- **DOCUMENTATION_POLICY.md** - Documentation guidelines

### Component-Level (`statement_generator/docs/`)
- **STATEMENT_GENERATOR.md** - CLI reference
- **PHASE_3_STATUS.md** - Validation framework status
- **ASYNC_IMPLEMENTATION.md** - Async infrastructure details
- **PHASE4_DEPLOYMENT_PLAN.md** - Production deployment strategy

### Artifacts (`statement_generator/artifacts/`)
- **AUDIT_IMPLEMENTATION_SUMMARY.md** - January 23 audit results
- **phase3_evaluation/** - Phase 3 test results
- **logs/** - Runtime logs
- **checkpoints/** - State tracking

---

## Extension Points

### Adding a New LLM Provider

1. Create `src/infrastructure/llm/providers/my_provider.py`:
   ```python
   class MyProvider(BaseLLMProvider):
       def generate(self, prompt: str, **kwargs) -> str:
           # Implementation
           pass

   # Self-register
   ProviderRegistry.register("my-provider", MyProvider)
   ```

2. Update `.env`:
   ```bash
   LLM_PROVIDER=my-provider
   MY_PROVIDER_API_KEY=...
   ```

3. Test with single question:
   ```bash
   ./scripts/python -m src.interface.cli process --question-id cvmcq24001
   ```

### Adding a New Validator

1. Create `src/validation/my_checks.py`:
   ```python
   class MyValidator:
       enabled = True

       def validate(self, statement: Statement, context: dict) -> List[ValidationIssue]:
           issues = []
           # Validation logic
           return issues

   # Auto-register
   ValidatorRegistry.register(MyValidator)
   ```

2. Validator runs automatically on all statements

### Adding a New Extractor

1. Create `src/processing/statements/extractors/my_extractor.py`
2. Inherit from base extractor pattern
3. Use shared `NLPGuidanceFormatter` for NLP guidance
4. Integrate into `pipeline.py` orchestration

---

## Related Documentation

- [CODING_STANDARDS.md](CODING_STANDARDS.md) - Python best practices
- [PERFORMANCE_OPTIMIZATION.md](PERFORMANCE_OPTIMIZATION.md) - Profiling guide
- [REFACTORING_GUIDE.md](REFACTORING_GUIDE.md) - Implementation patterns
- [STATEMENT_GENERATOR.md](../statement_generator/docs/STATEMENT_GENERATOR.md) - CLI reference
- [CLAUDE.md](../CLAUDE.md) - Project overview and quick start

---

**Last Updated**: January 23, 2026
**Next Review**: After Phase 4 completion
