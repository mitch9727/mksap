# Project TODO

**Last Updated**: December 31, 2025
**Current Phase**: Phase 2 (Statement Generator)

This file tracks project completion status across the 4-phase pipeline.

---

## Phase 1: Question Extraction (Complete)

- [x] Extract 2,198 questions across 16 systems
- [x] Validate extraction counts against discovery metadata
- [x] Capture Phase 1 completion report

---

## Phase 2: Statement Generator (Active)

### Priority Now (unblocks production readiness)

- [ ] Verify CLI provider flags (claude-code, gemini, codex)
- [ ] Test all providers with `--dry-run` on `cvmcq24001`
- [ ] Re-run anti-hallucination test on `givdx24022`
- [ ] Run 10-question quality sample across multiple systems
- [ ] Define manual review checklist for statement accuracy
- [ ] Decide default provider (claude-code vs anthropic) and update docs/config
- [ ] Update docs after default provider decision

### Completed (foundation)

- [x] Implement 4-step pipeline (critique -> key points -> cloze -> normalization)
- [x] Add checkpoint resume system with batch saves
- [x] Add provider fallback manager integration
- [x] Add --force re-processing and failed-clear checkpoint behavior
- [x] Consolidate Phase 2 docs into `docs/reference/`

### Next (quality + reliability)

- [ ] Improve provider error classification (retryable vs permanent)
- [ ] Implement validation framework (`validator.py`)
- [ ] Add Phase 2 validation guidance once implemented
- [ ] Track processing time per question and provider usage
- [ ] Capture rough cost estimates for paid providers

### Later (production run)

- [ ] Run full production pass on all 2,198 questions

---

## Phase 3: Cloze Application (Planned)

- [ ] Draft Phase 3 design/spec for cloze application
- [ ] Implement cloze blanking based on `cloze_candidates`
- [ ] Preserve `extra_field` and link to source data
- [ ] Add tests for cloze generation edge cases

---

## Phase 4: Anki Export (Planned)

- [ ] Select Anki export tooling (likely `genanki`)
- [ ] Define note model and field mapping
- [ ] Include media assets (figures/tables/videos/SVGs)
- [ ] Validate import into Anki and review card quality

---

## Tooling and Maintenance

- [ ] Restore `.claude` config path to enable `/maintain` workflows
- [ ] Add automated docs link check to routine workflow
