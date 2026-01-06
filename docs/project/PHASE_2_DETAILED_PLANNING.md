# Phase 2: Statement Generator - Detailed Planning

> For quick commands, see [QUICKSTART.md](QUICKSTART.md). For implementation details, see [Statement Generator Reference](../reference/STATEMENT_GENERATOR.md).

## Phase 2 Overview

Phase 2 extracts testable medical facts from MKSAP questions using LLM-powered analysis. It processes the JSON output from Phase 1 and augments each question with structured flashcard statements.

**Key Features**:
- 4-phase pipeline: critique extraction -> key points extraction -> cloze identification -> text normalization
- Multi-provider LLM support (Anthropic API, Claude Code CLI, Gemini CLI, Codex CLI)
- Evidence-based flashcard design aligned with spaced repetition best practices
- Non-destructive JSON updates (adds `true_statements` field only)
- Checkpoint-based resumable processing with atomic saves

## Multi-Phase Pipeline Context

The MKSAP project follows a **4-phase sequential pipeline**:

### Phase 1: Question Extraction (Complete ✅)
**Technology**: Rust
**Input**: MKSAP API (https://mksap.acponline.org)
**Output**: 2,198 structured JSON files (one per question)

**Key Outputs**:
- question_id, category, critique, key_points
- question_text, question_stem, options
- educational_objective, references
- media files (figures, tables, videos, SVGs)

### Phase 2: Statement Generation (Active 🔄)
**Technology**: Python 3.9+ with LLM providers
**Input**: Phase 1 JSON files
**Output**: Augmented JSONs with `true_statements` field

**Process**:
- Extract testable facts from critique
- Extract facts from key_points
- Identify cloze deletion candidates (2-5 per statement)
- Normalize mathematical notation

### Phase 3: Cloze Application (Planned 📋)
**Technology**: TBD (likely Python)
**Input**: Phase 2 JSONs with true_statements
**Output**: Formatted flashcards with [...] blanks applied

**Process**:
- Apply cloze deletions based on cloze_candidates
- Generate multiple cards per statement (one per candidate)
- Preserve extra_field for context

### Phase 4: Anki Export (Planned 📋)
**Technology**: TBD (Python + genanki or similar)
**Input**: Phase 3 formatted flashcards
**Output**: Anki deck (.apkg) with media assets

**Process**:
- Generate Anki note types
- Link media files (figures, tables, videos, SVGs)
- Apply spaced repetition metadata
- Package into importable deck

## High-Level Architecture

### 4-Phase Pipeline Design

```
PHASE 1: Critique Extraction
- Input: critique field (300-800 words of medical explanation)
- Output: 3-7 atomic statements
- Constraint: Extract ONLY facts explicitly stated in the critique

PHASE 2: Key Points Extraction
- Input: key_points array (0-3 pre-formatted bullets)
- Output: 1-3 refined statements
- Constraint: Minimal rewriting, same anti-hallucination rules

PHASE 3: Cloze Identification
- Input: All statements from phases 1-2
- Output: 2-5 cloze candidates per statement
- Strategy: Modifier splitting (e.g., "mild" and "hypercalcemia")

PHASE 4: Text Normalization
- Input: Statements with cloze candidates
- Output: Normalized symbols ("less than" -> "<", "greater than" -> ">")

FINAL: JSON Augmentation
- Add true_statements field to existing question JSON
- Preserve all original fields (non-destructive)
- Checkpoint each processed question
```

### Multi-Provider Abstraction

```
BaseLLMProvider
-> AnthropicProvider
-> ClaudeCodeProvider
-> GeminiProvider
-> CodexProvider
```

### Provider Selection and Fallback

- Provider settings (model, temperature, keys) are loaded via `--provider` or `LLM_PROVIDER`.
- Processing uses a provider manager with fallback order: claude-code -> codex -> anthropic -> gemini.
- User confirmation is required before switching providers on rate limits.

### Checkpoint/Resume System

- Checkpoint file: `statement_generator/outputs/checkpoints/processed_questions.json`
- Tracks processed and failed question IDs
- Atomic writes with batch saves (default: every 10 questions)
- Safe to interrupt and resume without data loss

### Non-Destructive JSON Updates

- Adds `true_statements` without modifying any existing fields
- Preserves all media metadata, question text, and performance data
- Allows re-running Phase 2 without re-extracting data

## Evidence-Based Flashcard Design

Prompts follow research-backed principles from [Cloze Flashcard Best Practices](../reference/CLOZE_FLASHCARD_BEST_PRACTICES.md):

1. Atomic facts (one concept per statement)
2. Anti-hallucination constraints (source-only extraction)
3. Modifier splitting for clinically important qualifiers
4. Clinical context in `extra_field` only when source provides it
5. Concise phrasing (remove patient-specific fluff)
6. Avoid enumerations (chunk lists into overlapping clozes)
7. Multiple cloze candidates per statement (2-5)

## Module Organization

### Core Pipeline Modules
- Pipeline orchestration (critique → key points → cloze → normalization)
- Critique statement extraction
- Key points statement extraction
- Cloze candidate identification
- Text normalization

### Infrastructure Modules
- CLI entry point and orchestration
- Configuration and environment loading
- JSON read/write and augmentation helpers
- Resume/checkpoint management
- Multi-provider client wrapper
- Provider fallback orchestration
- Pydantic data models

### Provider Implementations
- Anthropic API (API key required)
- Claude Code CLI (subscription)
- Gemini CLI (subscription)
- OpenAI CLI (subscription)

## Critical Design Constraints

- Sequential processing only (LLM-bound, simpler error handling, avoids rate limits)
- Low temperature default (0.2) to minimize hallucination
- Non-destructive JSON updates (Phase 1 data is treated as immutable)
- Checkpoint batching for I/O efficiency and safe resume

## Known Limitations

1. Some CLI providers ignore temperature settings
2. No automated validation framework yet
3. No extraction from wrong-answer explanations
4. No extraction from media (figures/tables captions)
5. No scenario extraction from question_text
6. Sequential-only processing (no parallelism)

---

**Last Updated**: January 5, 2026
**Status**: 🔄 Active
