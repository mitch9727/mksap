# Hybrid spaCy/scispaCy + LLM Plan (Preliminary)

Goal: Increase statement accuracy by pairing deterministic NLP (spaCy/scispaCy) with LLM
generation/verification. Keep LLMs for reasoning/rewrites; use scispaCy for grounding,
entity anchoring, and stable preprocessing.

## Why hybrid (vs LLM-only)
- Deterministic entity/lemma spans anchor statements/clozes to source text (reduces hallucinations).
- Stable dedupe/overlap checks; reproducible across runs.
- LLMs stay focused on synthesis and repair, not basic extraction.

## Proposed pipeline (accuracy-first)
**Phase 0: NLP preprocessing (scispaCy)**
- Model: prefer `en_core_sci_lg` (fallback: `en_core_sci_sm`).
- Outputs per sentence: tokens/lemmas, entities (drug/condition/procedure/lab/organism),
  numerics (values + units), negation cues, spans → “fact context”.
- New: `statement_generator/src/nlp_preprocess.py`; invoke early in `src/pipeline.py`.

**Phase 1: LLM statement generation**
- Inputs: critique text + per-sentence fact context (entities, numbers, negation).
- Output: 1–2 statements per sentence, with indication/timing/context; no source references.
- Update prompts: `prompts/critique_extraction.md`, `prompts/key_points_extraction.md` to
  consume fact context and enforce anchors/format.

**Phase 2: Hybrid cloze candidate selection**
- scispaCy proposes: entities (drug/condition/procedure/lab/organism), numeric thresholds/units.
- LLM ranks/filters for testability and ambiguity.
- New: `src/cloze_candidate_selector.py`; integrate before `src/cloze_identifier.py`
  final selection. Keep strict substring/unit checks in `validation/cloze_checks.py`.

**Phase 3: Validation + entailment**
- Keep existing lemma/entity overlap fidelity checks.
- Add entailment gate: LLM entailment (critique ⇒ statement) or local NLI (MedNLI/SciNLI) if needed.
- New: `src/validation/entailment_checks.py`; wire into `validation/validator.py`.

**Phase 4: Dedupe (accuracy-first)**
- scispaCy entity signatures + lemmatized token overlap for safe dedupe; optional
  semantic embeddings (SciBERT/MedCPT) for near-dupes.
- New: `src/dedupe.py`; run after generation, before cloze selection.

**Phase 5: Repair loop (LLM)**
- For validator flags (multi-concept, missing indication/timing, vague language).
- LLM rewrites with strict constraints; re-validate.
- Add repair step in `src/pipeline.py`.

## Model choices
- scispaCy: `en_core_sci_lg` (better NER); keep `MKSAP_NLP_MODEL` configurable.
- LLM: strongest available for generation/repair; smaller/faster for entailment if desired.
- Optional embeddings for dedupe: SciBERT/MedCPT.

## Config knobs
- Existing: `MKSAP_NLP_MODEL`, `MKSAP_NLP_BATCH_SIZE`, `MKSAP_NLP_N_PROCESS`.
- Proposed: `MKSAP_ENTAILMENT_PROVIDER`, `MKSAP_ENTAILMENT_MODEL`, `MKSAP_DEDUPE_MODEL`.

## Integration map (files to touch)
- New: `src/nlp_preprocess.py`, `src/cloze_candidate_selector.py`,
  `src/validation/entailment_checks.py`, `src/dedupe.py`.
- Update: `src/pipeline.py` (invoke phases, repair loop),
  `src/validation/validator.py` (entailment), `prompts/critique_extraction.md`,
  `prompts/key_points_extraction.md`, `docs/reference/STATEMENT_GENERATOR.md`
  (workflow + env vars).

## Metrics and regression
- Track per-question: statement yield, entity coverage, cloze yield, warning/error counts, dedupe rate.
- Maintain a small gold set for regression across model/prompt changes.

## Open questions for you
1) Entailment gate: prefer LLM-based check (simpler to wire) or local NLI model (deterministic, slower)?  
2) Dedupe aggressiveness: safe (entity + lemma overlap only) vs semantic (adds embeddings)?  
3) How many statements per sentence max (1–2) to control duplication/verbosity?  
4) Are we okay pinning to `en_core_sci_lg` (larger) or keep `en_core_sci_sm` default for speed?  
5) Do we want a pure “rephrase from critique only” mode (no new facts) for high-stakes accuracy?

## Notes on “LLM vs reorganization only”
- scispaCy alone cannot reliably synthesize concise, human-like statements; LLM adds
  clarity and testable phrasing. Best practice: use scispaCy to ground facts and let
  the LLM rephrase/repackage them, with entailment + fidelity checks to prevent drift.
