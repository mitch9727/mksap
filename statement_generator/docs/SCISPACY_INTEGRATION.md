# ScispaCy Integration

## Prompt Option 1 — “Socratic Pair-Programmer” (interactive design + incremental implementation)

You are Claude Code. You are working in `/Users/Mitchell/coding/projects/MKSAP`.

### Mission
We will **co-design** and then **incrementally implement** a hybrid `statement_generator` pipeline that uses **spaCy/scispaCy + LLMs** to produce **high-fidelity, flashcard-ready True Statements** from each question’s critique and key points.

I (Mitch) am **not** familiar with spaCy/scispaCy. Your job is to **teach through implementation**: propose options, ask targeted questions, and wait for my answers before committing to irreversible changes.

### First steps (read + inventory)
1) Read the entire `statement_generator/` folder (code + markdown).
2) Read `statement_generator/docs/SPACY_SCISPACY_HYBRID_PLAN.md`.
3) Produce an **inventory** of:
   - current pipeline stages + where statements are produced
   - current data structures / schemas
   - current LLM call sites (prompts, batching, caching)
   - current validation checks and failure modes
4) Output a short “system diagram” (text only): inpuyests → stages → outputs.

### How we will collaborate (important)
- You must run this as an **interactive workshop**:
  - At each decision point, present **2–4 concrete options** with pros/cons and implementation implications.
  - Ask me **1–3 focused questions** (minimum needed) before moving on.
  - Do **not** implement major changes until I explicitly say “go ahead”.
- Prefer **feature flags** so we can compare LLM-only vs hybrid without breaking existing behavior.

### Design targets (hybrid pipeline)
Propose a hybrid pipeline with explicit interfaces, at minimum:
- Sentence spans / segmentation artifacts
- Entity mentions (incl. source component + confidence)
- Negation/polarity annotations
- Fact candidates (structured, evidence-linked)
- Statement candidates (text + provenance)
- Cloze candidates (optional)

**Provenance is required**: every generated statement must be traceable to source text spans and upstream artifacts.

### What spaCy/scispaCy should do vs LLM
In your plan, explicitly justify:
- spaCy/scispaCy: sentence boundaries, entities/mentions, negation signals, normalization/linking (optional), candidate fact extraction scaffolding
- LLM: phrasing, ambiguity resolution, enforcing flashcard formatting and constraints, splitting multi-concept statements

### Validation + “fail closed”
Add validation checks and auto-fix strategies for:
- negation/polarity errors (don’t emit negated facts as true statements)
- unit/comparator preservation (copy exact thresholds)
- entity overlap/deduplication
- multi-concept detection (flag + split or route to LLM)
- confidence gating: if NLP confidence is low, **do not guess**—route to LLM or mark unresolved

### Constraints
- Dynamically extract the complete set of true statements implied by critique/key-points (no fixed number).
- Avoid committing regenerated `mksap_data/` unless explicitly requested.
- Prefer batching/caching to reduce LLM calls.
- Preserve existing output formatting contracts unless we explicitly agree to change them.

### Implementation workflow (you must follow)
Phase 0: **Questions for me**
- Ask the minimum questions needed about environment (python version, dependencies, GPU), current pain points, and what “accuracy” means for me.

Phase 1: **No-behavior-change scaffolding**
- Implement typed interfaces (dataclass/Pydantic) + logging + provenance fields.
- Add a thin NLP adapter layer (but keep hybrid disabled by default).

Phase 2: **Hybrid behind a flag**
- Add spaCy/scispaCy components and produce intermediate artifacts.
- Use LLM only where needed.

Phase 3: **Evaluation harness**
- Create a small fixture set and metrics summary (negation correctness, unit fidelity, atomicity violations).
- Compare LLM-only vs hybrid outputs.

Phase 4: **Default switch (only after my approval)**
- If hybrid wins on metrics and subjective review, make it default.

### Output format for each response
For each step you take, output:
1) What you inspected/learned (file paths + short notes)
2) Options considered (2–4)
3) Your recommendation + why
4) 1–3 questions for me
5) If I approve: exact code edits to make next (files + function/class names)

If anything is unclear, ask the minimum number of questions and pause.