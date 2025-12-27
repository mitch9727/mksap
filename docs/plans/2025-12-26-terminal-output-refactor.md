# Terminal Output Refactoring Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Refactor the MKSAP text extractor's terminal output to be production-grade: consolidate phase-based logging, remove redundant information, and improve readability.

**Architecture:**
- Move phase-level detail logs (Phase 1, 2, 3) to debug level using `tracing::debug!` macro
- Consolidate discovery results into single-line info output: `✓ {system}: Discovered {count} questions ({types} types)`
- Consolidate extraction results into single-line info output: `✓ {system}: Extracted {new} new, {existing} already extracted`
- Remove redundant category name repetition in individual log statements
- Make directory creation silent (no logging output)
- Preserve all error handling at error/warning level

**Tech Stack:**
- Rust `tracing` crate (info!, debug!, error!, warn! macros)
- Existing checkpoint and extraction logic (no behavior changes)

---

## Task 1: Refactor Discovery Phase Logging in extractor.rs

**Files:**
- Modify: `extractor/src/extractor.rs:230-280` (discover_questions method)

**Step 1: Understand current discovery logging**

Read lines 230-280 to see:
- Line 232: `info!("Extracting: {}", category.name);` - redundant category name
- Line 238: `info!("Phase 1: Discovering valid questions for {}...", category.name);` - phase detail
- Line 265-274: Directory creation logging - should be silent
- Line 324: Skip message with redundant category name

Expected current structure has 4 info! calls per system discovery.

**Step 2: Update discover_questions method**

Change these lines in extractor.rs:

**Line 238** - Change from:
```rust
info!("Phase 1: Discovering valid questions for {}...", category.name);
```

To:
```rust
debug!("Phase 1: Discovering valid questions for {}...", category.name);
```

**Lines 266-274** - Change the entire directory creation block from:
```rust
info!("Phase 2: Creating directories for {} questions...", valid_ids.len());
...
info!("✓ Directories created");
```

To:
```rust
debug!("Phase 2: Creating directories for {} questions...", valid_ids.len());
...
debug!("✓ Directories created");
```

**Line 278** - Change from:
```rust
"Phase 3: Extracting data for {} questions (concurrency: {})...",
```

To (add debug! prefix):
```rust
debug!("Phase 3: Extracting data for {} questions (concurrency: {})...", valid_ids.len(), concurrency);
```

**Step 3: Remove redundant skip message**

**Lines 323-325** - Change from:
```rust
if questions_skipped > 0 {
    info!("Skipped {} already-extracted questions for {}", questions_skipped, category.name);
}
```

To:
```rust
// Skip count will be included in per-system summary from main.rs
```

This information will be reported in the consolidated extraction result line.

**Step 4: Verify no syntax errors**

Run: `cargo check`
Expected: Clean compilation

**Step 5: Commit**

```bash
git add extractor/src/extractor.rs
git commit -m "refactor: move discovery phase details to debug logging"
```

---

## Task 2: Add Discovery Result Logging Method to extractor.rs

**Files:**
- Modify: `extractor/src/extractor.rs` (add new method after discover_questions)

**Step 1: Add new method after discover_questions**

Add this method around line 330 (after the discover_questions method ends):

```rust
/// Log a consolidated discovery result line
pub fn log_discovery_result(category_code: &str, discovered_count: usize, question_types: &[&str]) {
    if discovered_count > 0 {
        let types_str = if question_types.is_empty() {
            "0 types".to_string()
        } else {
            format!("{} types", question_types.len())
        };
        info!("✓ {}: Discovered {} questions ({})", category_code, discovered_count, types_str);
    }
}
```

**Step 2: Verify syntax**

Run: `cargo check`
Expected: Clean compilation

**Step 3: Commit**

```bash
git add extractor/src/extractor.rs
git commit -m "refactor: add discovery result logging method"
```

---

## Task 3: Update main.rs to Use Consolidated Discovery Results

**Files:**
- Modify: `extractor/src/main.rs:410-430` (extraction loop)

**Step 1: Understand current extraction loop**

Look at lines 410-430 in main.rs to see:
- Line 413: `info!("\n[{}/{}] Extracting: {}", idx + 1, categories.len(), category.name);`
- Line 418: `info!("✓ Extracted {} questions from {}", count, category.name);`

**Step 2: Find where questions_extracted is captured and reported**

The extract_questions method returns the count. Modify the loop to:
1. Still call extract_questions (no change to logic)
2. Log discovery result BEFORE extraction
3. Log consolidated extraction result instead of current format

**Step 3: Update extraction loop around line 413**

Replace:
```rust
info!("\n[{}/{}] Extracting: {}", idx + 1, categories.len(), category.name);
```

With:
```rust
info!("\n[{}/{}] Processing: {}", idx + 1, categories.len(), category.name);
```

(Minimal change - just rename "Extracting" to "Processing" to be more accurate)

**Step 4: Capture both new and total counts**

After the `count` is returned from `extract_questions`, we need to report both new and existing counts.

Modify the completion logging around line 418 from:
```rust
info!("✓ Extracted {} questions from {}", count, category.name);
```

To:
```rust
// Load checkpoint to get total discovered count
let checkpoint_path = format!("mksap_data/.checkpoints/{}_ids.txt", category.code);
let total_discovered = match std::fs::read_to_string(&checkpoint_path) {
    Ok(content) => content.lines().count(),
    Err(_) => count as usize,
};
let already_extracted = total_discovered.saturating_sub(count as usize);

info!("✓ {}: Extracted {} new, {} already extracted",
    category.code, count, already_extracted);
```

**Step 5: Verify syntax**

Run: `cargo check`
Expected: Clean compilation

**Step 6: Commit**

```bash
git add extractor/src/main.rs
git commit -m "refactor: consolidate extraction result logging format"
```

---

## Task 4: Build and Test Output

**Files:**
- No file changes
- Test: Full extraction run to verify output

**Step 1: Clean build**

Run: `cargo build --release`
Expected: Clean compilation, zero warnings

**Step 2: Run validation command to test logging**

Run: `cargo run --release -- validate`
Expected: Clean output without redundant phase messages

**Step 3: Verify output format**

Check that validation output shows:
- No "Phase 1", "Phase 2", "Phase 3" messages (they're at debug level)
- Clean checkpoint file listing without per-phase details
- Summary statistics at end

**Step 4: Test debug logging**

Run: `RUST_LOG=debug cargo run --release -- validate 2>&1 | head -50`
Expected: See Phase 1-3 messages in output when debug logging is enabled

**Step 5: Commit**

```bash
git add .
git commit -m "test: verify refactored logging output"
```

---

## Task 5: Update Documentation

**Files:**
- Modify: `docs/project/README.md`
- Modify: `extractor/README.md` (if it exists)

**Step 1: Document logging levels**

Add a new section "Logging and Debugging" to the appropriate documentation:

```markdown
## Logging and Debugging

### Standard Output
The extractor produces clean, concise output by default:
- Discovery results: `✓ {system}: Discovered {count} questions ({types} types)`
- Extraction results: `✓ {system}: Extracted {new} new, {existing} already extracted`
- Errors and warnings are always displayed

### Debug Output
To see detailed phase information (Phase 1, 2, 3 logs):
```bash
RUST_LOG=debug cargo run --release
```

This enables tracing of discovery progress, directory creation, and extraction concurrency details.
```

**Step 2: Verify documentation**

Run: `grep -n "Logging\|Debug" docs/project/README.md`
Expected: New section appears in output

**Step 3: Commit**

```bash
git add docs/project/README.md
git commit -m "docs: document logging levels and debug output"
```

---

## Task 6: Final Cleanup and Validation

**Files:**
- No file changes
- Validation: Full extraction to verify production readiness

**Step 1: Run full build**

Run: `cargo build --release`
Expected: Clean compilation

**Step 2: Run validation**

Run: `cargo run --release -- validate 2>&1 | tail -50`
Expected: Clean output showing per-system extraction results without phase clutter

**Step 3: Check git log**

Run: `git log --oneline -6`
Expected: See 5 new commits related to logging refactor

**Step 4: Create summary commit**

```bash
git commit --allow-empty -m "chore: terminal output refactor complete

- Moved phase-level logging to debug level (RUST_LOG=debug to enable)
- Consolidated discovery results to single-line info output
- Consolidated extraction results to single-line format with new/existing counts
- Removed redundant category name repetition
- Made directory creation silent
- Updated documentation with logging guide

Terminal output is now production-grade: clean, scannable, and informative."
```

---

## Testing Checklist

After implementing:

- [ ] `cargo check` passes with zero warnings
- [ ] `cargo build --release` completes successfully
- [ ] `cargo run --release -- validate` shows clean output without phase messages
- [ ] `RUST_LOG=debug cargo run --release -- validate 2>&1 | grep "Phase"` shows phase messages
- [ ] Error messages still display at all log levels
- [ ] Per-system summary shows format: `✓ {code}: Extracted {new} new, {existing} already extracted`
- [ ] No redundant category names in individual log lines
- [ ] Documentation mentions debug logging option

