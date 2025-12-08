# 📁 Project Instructions: Medical Flashcard Markdown Generation (Unified README)

> ✅ **Canonical Formatting References** — All outputs must strictly follow the formatting and structuring styles shown in these gold‑standard examples:  
> • `CVQQQ24018.md`
> • `CVMCQ24089.md`  
> • `CVMCQ24073.md`
> • `NRMCQ24077.md`
>
> ⚠️ Any future markdown generation **must** match these examples in section ordering, headers, numbered ✅ True Statements, 💬 Extra, 🏷️ Tags, full references, related‑text derivations, and HTML‑formatted supplemental material.

This document defines the **authoring standard** for converting board‑style medical MCQs into **single‑file**, Anki‑ready markdown flashcards. Outputs are **deterministic**, **parse‑friendly**, and **self‑contained** (text + figures/tables/videos).


---

## 🎯 Primary Goal (Single‑File Output Policy)

- **Exactly one markdown file per question**, saved to `questions/` and **named with the question ID** (e.g., `CVMCQ24073.md`).  
- The file must include **all required sections** in the order below, **plus any figures/tables/videos** appended at the end.  
- No additional helper files or sidecar notes are allowed in the question directory (assets may be external image files referenced by `<img src="...">`).


---

## 🧵 Required Section Order (Authoring Contract)

1) `### [Emoji] [System]: [Key Concept]`  
2) `#### ✅ True Statements` *(numbered; context‑complete; abbreviations expanded on first mention)*  
3) `#### 💬 Extra` *(optional; matched indices to True Statements; see rules below)*  
4) `#### 🏷️ Tags` *(camel‑case hash‑tags derived from Educational Objective + topical tags explicitly stated)*  
5) `#### 📚 Reference` *(primary source only; include PMID and/or DOI when available)*  
6) `#### 🆔 Question ID` *(exact ID string, also used as filename)*  
7) `#### 🕒 Last Updated` *(absolute month/year)*  
8) `#### 📖 Related Text` *(if provided; exact source breadcrumb per spec below)*  
9) `### 📘 Related Text Derivations` *(if Related Text exists; includes its own ✅ and optional 💬 and 🏷️)*  
10) `#### 🖼️ Supplemental Figures` / `#### 🗾 Supplemental Tables` / `#### 🔊 Supplemental Videos` *(if any)*

> 🧺 **Context‑complete rule:** Every True Statement (main and related‑text) must be interpretable **in isolation**, avoiding vague case language (“this patient”). Move any case‑specific details to **💬 Extra** with matched indices.


---

## 🧮 Input Handling & Normalization

The input may include any subset of: **Answer & Critique**, **Key Points**, **Related Text**, and asset images of **figures/tables/algorithms**.

- **Main ✅ list:** Extract **only directly stated, true medical statements** from **Answer & Critique** and **Key Points**.  
- **Related Text ✅ list:** If **Related Text** is present, extract **additional non‑duplicate true statements** for **📘 Related Text Derivations**.  
- **Assets:** If a **table/figure/algorithm** is provided (including as an image), (1) **transcribe** it to semantic HTML under the appropriate Supplemental section, and (2) **derive unlimited non‑duplicate ✅ True Statements** strictly from its explicit content (place these under **📘 Related Text Derivations**).

### Minimum Inputs Accepted
- **Answer & Critique** *(required)*  
- **Key Points** *(optional; if present, integrate into main ✅)*  
- **Related Text** *(optional; if present, create the Related sections)*  
- **Figures/Tables/Algorithms/Videos** *(optional; if present, embed per HTML rules below)*

### Abbreviation Expansion
- Expand on **first mention** in **each major section** (main ✅ vs. related‑text ✅).  
  Example: “**Heart failure with reduced ejection fraction (HFrEF)** …” then later “HFrEF”.

### Statement Granularity
- Break compound facts into **discrete, numbered statements**.  
- Include the **disease/condition/test** in each sentence to ensure **standalone clarity**.


---

## 🔖 Related Text — Strict Heading Containment (Required)

> **Rule of record:** *Statements derived from Related Text must be placed **only** under headings that are **directly mentioned within the Related Text** block.* Do **not** invent, infer, or reword headings.

**What counts as a valid heading?**
1. **Explicit section titles** (e.g., `Dermatologic Conditions of Aging`, `Calculating Cardiovascular Risk`).  
2. **Subsection titles** that are typographically distinct in the source (e.g., bold/line‑separated subheads).  
3. **Figure/Table captions** beginning with `Figure:` or `Table:` (treated as headings).  
4. **Labeled media titles** (e.g., a named video) with an explicit caption.

**What does *not* count?**
- Topic nouns appearing only in running text (e.g., “solar lentigines are…”) do **not** become headings.  
- Paraphrased/shortened headings must **not** be created—use the **exact string** from the Related Text.

**Placement Algorithm**
1. Render the source breadcrumb as:
   ```markdown
   #### 📖 Related Text
   MKSAP 19: [Main Section] — [Heading], [Sub‑heading], …, [Final Sub‑heading]
   ```
2. Add:
   ```markdown
   ### 📘 Related Text Derivations
   ```
3. Create derivation blocks **only** for headings that exist verbatim in the Related Text:
   - `#### ✅ True Statements — <Exact Subheading>`  
   - If text sits directly under the main heading, use:  
     `#### ✅ True Statements — <Exact Main Heading>` (repeat the main heading; do not invent a subheading).
4. **No cross‑heading mixing:** statements derived from one heading (or figure/table) **must not** be placed under another heading.  
5. When embedding media, the **same caption string** must be used in `<figcaption>` and (if needed) as the subsection name for derived statements.


---

## 💬 Extras — Generation Rules (Main & Related)

**Goal:** Provide concise context that improves comprehension **without adding new claims**.

**What an Extra *is***  
A short, 1‑2 sentence clarification **anchored to the same source** as its statement (e.g., scope, definitions, indications/contraindications, exceptions, class/grade/strength, list context, immediate rationale).

**Allowed content (priority order)**
1. **Non‑inferential pull‑through** from the same paragraph/bullets.  
2. **Near‑neighbor anchors** within the same section (e.g., alternative tests in the same algorithm step).  
3. **Controlled inference** (tight paraphrase, **no new claims**) **only if** #1–2 are unavailable (e.g., restating scope limits, role such as “screen/confirm/risk‑stratify,” or named guideline class/grade already present).

**Disallowed content**
- New clinical claims, prevalences, outcomes, or management steps **not present** in source.  
- Generic fillers (e.g., “From Related Text…”, “As above…”), or repeating the statement verbatim.  
- Vignette language (“this patient”). If necessary, state case details **only if explicitly present** in the source and keep them generic.

**Matching & numbering**
- Place Extras in a dedicated `#### 💬 Extra` section **after** the ✅ list.  
- **Index match** each extra to its statement number (`1.`, `2.`, …). If a statement has no extra, **skip that number**—don’t add placeholders.  
- If multiple extras apply to the **same statement**, **repeat the index** on separate lines (do **not** compress ranges such as “4–7”).  
- Apply these rules **both** to the main ✅ list and the **Related Text Derivations** ✅ list (each with its own 💬 Extra block).

**Style rule (important):** Do **not** include phrases like “(Controlled inference based on provided text.)”. Extras should read as clean, standalone clarifications. If no legitimate extra exists, **omit** it. Aim for Extras on **≥80%** of statements; brevity is preferred over filler.


---

## 🖼️ Figures • 🗾 Tables • 🔊 Videos (HTML Embed Rules)

All non‑text assets go at the **end of the markdown** under the appropriate supplemental heading(s).  
**Embed rules are designed for Anki media import compatibility and zero‑inference captions.**

### Global Media Rules (Strict)
1. **Use bare filenames only** in `src` (no paths or schemes).  
   - ✅ `src="Anterior Drawer Test.mp4"`  
   - ❌ `src="sandbox:/mnt/data/Anterior Drawer Test.mp4"`
2. **Captions must be verbatim labels/titles only.** Do **not** add descriptions, interpretations, or clinical claims to captions.  
   - ✅ `<figcaption><strong>Video: Anterior Drawer Test</strong>.</figcaption>`  
   - ❌ `<figcaption>… Demonstrates increased ligamentous laxity …</figcaption>`
3. **No inference in captions.** Place any explanatory context in **💬 Extra**, matched to the relevant True Statement index.
4. **Filenames may include spaces**; they must **exactly match** the attached asset names.
5. **Alt text for images:** If no explicit alt text is provided by the source, set `alt="[FILENAME.ext]"` (no auto‑generated alt).

### Figures (Images)
Use HTML `<figure>` with `<img>` and `<figcaption>`:
```html
<figure>
  <img src="[FILENAME.ext]" alt="[FILENAME.ext]">
  <figcaption><strong>Figure: [Exact Label as Provided]</strong>.</figcaption>
</figure>
```
- If the source provides a **full caption/legend**, include it **verbatim** in place of the label. Do **not** add new prose.
- If abbreviations or “Source/Reprinted from” lines are provided in the **original caption**, include them **verbatim** under the same `<figcaption>` (on new lines as needed). If none are provided, omit.

### Tables
Use semantic HTML; **no inline styles**:
```html
<table>
  <caption><strong>[Exact Table Title as Provided]</strong></caption>
  <thead>
    <tr><th>[Col 1]</th><th>[Col 2]</th><th>[Col 3]</th></tr>
  </thead>
  <tbody>
    <tr><td>[Cell]</td><td>[Cell]</td><td>[Cell]</td></tr>
  </tbody>
</table>
<p><em>[Verbatim abbreviations and footnotes only if provided in the source.]</em></p>
```
- Place **footnotes** immediately after the table in an italicized paragraph. Preserve exact superscripts (`<sup>…</sup>`), units, punctuation, and order.
- Do **not** add clarifications or normalize wording in table captions/footnotes; any clarifying notes belong in **💬 Extra**.

### Videos
- If a video is provided with a title/caption, add under `#### 🔊 Supplemental Videos`:
```html
<figure>
  <video src="[FILENAME.mp4]" controls></video>
  <figcaption><strong>Video: [Exact Title as Provided]</strong>.</figcaption>
</figure>
```

### 🔒 Footnote Fidelity (Assets)
1. Use **only** the footnote(s) provided with each asset; **do not** add/remove/normalize content.  
2. Preserve **exact text** (wording, capitalization, punctuation, units, symbols, order).  
3. Footnotes belong **only** to their respective asset; **do not reuse** across assets.  
4. If **no footnotes** are provided, **omit** the footnote block entirely.

### 🧹 Migration & Validation Aids
- Strip sandbox paths: **Find:** `sandbox:/mnt/data/` → **Replace:** *(empty)*  
- Flag captions with extra prose (manual fix):  
  **Regex:** `<figcaption>.*?(Video|Figure):\s*([^<]+)</strong>(.*?)</figcaption>` → if group 3 is non‑empty, remove the extra prose.
- Verify that **every asset filename** referenced in the markdown exists in the media folder (exact match, including spaces).


## 🏷️ Tags (from Educational Objective)

Convert the specialty and care‑type strings into camel‑case tags. Include population/priorities when listed.

**Examples**
- “Cardiovascular Medicine Care type: Ambulatory High Value Care” → `#Cardiology #AmbulatoryCare #HighValueCare`  
- “Pulmonary Medicine Care type: Hospital Patient: Age ≥65 y” → `#Pulmonology #HospitalCare #PatientOver65`  
- Add topical tags **only if directly stated** in the source (e.g., `#NSTEMI`, `#AtrialFibrillation`).


---

## 🧪 Flashcard Formatting Checklist (Quick Pass)

- Top‑level header with emoji + system + key concept  
- Numbered ✅ True Statements (context‑complete; first‑mention expansions)  
- Optional 💬 Extra with **[n]** indices (repeat index for multi‑extras; never compress ranges)  
- 🏷️ Tags (from Educational Objective + topical)  
- 📚 Reference (one primary citation; include PMID/DOI when available)  
- 🆔 Question ID (must match filename)  
- 🕒 Last Updated (absolute month/year)  
- 📖 Related Text + 📘 Related Text Derivations (when provided; non‑duplicate)  
- Supplemental HTML sections appended (Figures/Tables/Videos)  
- **Footnote Fidelity:** For each asset, use verbatim footnotes only (if provided).  
- **Table/algorithm‑derived statements are standalone** and contain subject, qualifiers, thresholds with units, explicit actions, and timing.

---

## 🧩 Master Output Template (Copy/Paste)

```markdown
### 🫀 [System]: [Key Concept]

#### ✅ True Statements
1. [Fully expanded, context‑complete fact about {condition/test/therapy}.]
2. [Next fact.]

#### 💬 Extra
1. [Optional short context for #1.]
1. [Optional second context line for #1, if needed.]
2. [Optional short context for #2.]

#### 🏷️ Tags
#Cardiology #AmbulatoryCare [#MoreTags]

#### 📚 Reference
[Lead Author] et al. [Title]. [Journal/Publisher]. [Year];[Volume]:[Pages]. PMID: [PMID] doi:[DOI]

#### 🆔 Question ID
[CVxQ/MCQnnnnn]

#### 🕒 Last Updated
[Month Year]

---

#### 📖 Related Text
MKSAP 19: [Main Section] — [Heading], [Sub‑heading], …, [Final Sub‑heading]

---

### 📘 Related Text Derivations

#### ✅ True Statements
1. [Non‑duplicate fact derived from Related Text.]
2. [Additional non‑duplicate fact.]

#### 💬 Extra
1. [Optional context for Related Text #1.]
2. [Optional context for Related Text #2.]

#### 🏷️ Tags
[#OnlyIfNewTopicalTagsAreIntroduced]

---

#### 🖼️ Supplemental Figures
<figure>
  <img src="[FILENAME.ext]" alt="[Descriptive alt text]">
  <figcaption>
    [Legend as provided or minimally normalized for clarity. If an abbreviations line exists in the source, include it verbatim.]<br>
    <em>[Verbatim “Source/Reprinted from” line only if present.]</em>
  </figcaption>
</figure>

#### 🗾 Supplemental Tables
<table>
  <caption><strong>[Table Title]</strong></caption>
  <thead><tr><th>[Col 1]</th><th>[Col 2]</th></tr></thead>
  <tbody>
    <tr><td>[Cell]</td><td>[Cell]</td></tr>
  </tbody>
</table>
<p><em>[Verbatim abbreviations; verbatim footnotes (only if provided).]</em></p>

#### 🔊 Supplemental Videos
<figure>
  <video src="[FILENAME.mp4]" controls></video>
  <figcaption>[Exact video title/caption as provided.]</figcaption>
</figure>
```

---

## 🧾 CSV Conversion (Downstream)

When converting many markdown files to a CSV for Anki import, use section headers as **stable selectors**. Suggested columns:

- `question_id` (from 🆔)  
- `system` (from top header)  
- `key_concept` (from top header)  
- `statement_index` (1‑n)  
- `statement_text` (from main ✅)  
- `extra_text` (from main 💬; keyed by index, one row per extra if repeated)  
- `section` (enum: `main`, `related`)  
- `related_statement_index` (1‑n; when section=`related`)  
- `related_statement_text`  
- `related_extra_text`  
- `tags` (space‑separated string from 🏷️)  
- `reference` (single string)  
- `last_updated` (`YYYY‑MM`)  
- `assets` (pipe‑separated list of filenames from `<img src="...">`/`<video src="...">`)

> Parsing should be robust to minor whitespace; rely on exact **section headers** and **ordered structure** above.


---

## 🌟 Standardized Emoji Mapping by MKSAP Section

| MKSAP 19 Section                   | Required Emoji |
| ---------------------------------- | -------------- |
| General Internal Medicine          | 🩺             |
| Cardiovascular Medicine            | 🫀             |
| Pulmonary & Critical Care Medicine | 🫁             |
| Gastroenterology & Hepatology      | 🍽️            |
| Endocrinology & Metabolism         | 🧪             |
| Hematology & Oncology              | 🩸             |
| Infectious Disease                 | 🦠             |
| Nephrology                         | 🗄️             |
| Neurology                          | 🧠             |
| Rheumatology                       | 🦴             |
| Dermatology                        | 🩹             |

**Implementation Rules**
1. The **emoji** must precede the system name in the top‑level header.  
2. If a question spans multiple sections, choose the **primary** system emphasized in the Educational Objective.  
3. When new MKSAP sections are introduced, add them here to maintain consistency.


---

## ✅ Validation Checklist (Pre‑Save)

- Filename equals the **Question ID**.  
- All **required sections** present and in order.  
- ✅ lists contain **only directly stated facts**, with **first‑mention expansions**.  
- ❌ No case language in ✅; case details (if truly needed) live in **💬 Extra**.  
- **Related Text** used to create **non‑duplicate** statements only, under **verbatim headings/captions**.  
- Figures/Tables/Videos use **standard HTML** blocks, proper captions, and **alt text**.  
- **Extras** follow numbering rules; **no disclaimer phrases**; repeat indices for multiple extras, never compress ranges.  
- **Footnote Fidelity** verified for each figure/table (verbatim, only if provided).  
- **Table/algorithm‑derived statements** are standalone with subject, qualifiers, thresholds with units, explicit actions, and timing.

---

*Last updated: August 2025*


---

## Deriving True Statements from Tables, Figures, and Videos (Minimal Inference • Standalone)

**Goal:** Ensure every statement derived from supplemental assets is directly supported by the source and can be understood **in isolation**.

### Canonical Rules
1. **Direct evidence only.** Derive facts **only** from the asset’s **title**, **headers/axis labels**, **cells/data**, and **verbatim figure legends/footnotes**. Do **not** extrapolate, summarize trends, or generalize beyond what is explicitly stated.
2. **Standalone construction.** Each statement must:
   - Name the **condition/test/procedure/therapy** (e.g., “Thessaly test,” “Anterior cruciate ligament (ACL) tear”).
   - Include the **context** (population/setting/condition) when present in the source.
   - State the **fact/threshold/outcome** using **exact units** and **comparators** (>, ≥, etc.) and **timeframes** when present.
   - **Expand abbreviations on first mention** within the derived section (even if expanded earlier in the file).
   - Avoid pronouns and vague phrasing (**no** “this/these/it,” **no** “the patient”). Use explicit nouns.
3. **Zero paraphrase for critical values.** Preserve **numbers, ranges, units, qualifiers, and footnote conditions** exactly. Do not round or average. If a footnote modifies a value, include that qualifier **in the statement** or in **💬 Extra** matched to the same index.
4. **Non-duplicate only.** Include **new** facts not already captured in the main True Statements. If a statement partially overlaps, either (a) merge and keep the most complete version, or (b) omit the duplicate.
5. **Sectioning.** Place these under `#### 📖 Related Text` → `### 📘 Related Text Derivations` → `#### ✅ True Statements` (CVQQQ24018 style). Use a **separate numbered list** from the main list.
6. **Clarifications in 💬 Extra.** If the asset needs context (e.g., how a maneuver is performed, footnote constraints), add a **number-matched** entry under **💬 Extra** in the same derivations block.

### Examples
**✅ Standalone (good)**  
- “**Lachman test** (evaluation of **anterior cruciate ligament (ACL)** integrity) frequently demonstrates **increased ligamentous laxity** in **acute ACL tears**.”  
- “In **medial collateral ligament (MCL) injury** assessment, the **valgus stress test** detects **increased laxity** when a **medially directed force** is applied at **30° of knee flexion**.”

**❌ Not standalone (bad)**  
- “This test shows laxity.” (No named test/condition.)  
- “Positive when painful.” (No context; undefined ‘positive’.)  
- “These findings are common.” (Vague plural; no entities.)

### Quick Validation Heuristics
- Each derived statement should contain **at least one explicit entity** (condition/test/therapy) and **no ambiguous pronouns**.  
  - Flag candidates for review if they match: `^(\s*\d+\.\s*)(This|These|It|They)\b`  
- Footnote fidelity: ensure any symbol/qualifier present in the asset appears in the statement or its matched **💬 Extra** entry.
- Isolation check: read the statement without the rest of the file; if a non-expert cannot tell **what** the fact is about and **when/where** it applies, revise.


---

## Top-Level Header Construction (Source-Aligned)

**Rule:** The left-hand side of the top-level header must use the **main heading that appears immediately after the “Educational Objective”** line in the source text (e.g., **Common Symptoms**, **Pulmonary Medicine**, **Critical Care Medicine**).  
**Format:**  
```
### [System/Section Heading]: [Key Concept or Diagnosis]
```
- Keep the existing project emoji style as a prefix to the header if desired (e.g., `### 🦴 Common Symptoms: Lateral Meniscus Tear Diagnosis`).  
- The **[Key Concept or Diagnosis]** should be the concise clinical concept (e.g., “Lateral Meniscus Tear Diagnosis”).  
- This rule applies to **all new and updated files** to maintain alignment with the source.


### Tables from Images → Convert to Semantic HTML

When a table is provided **as one or more images**, do **not** embed the image(s). Instead:
1. **Rebuild the table** as semantic HTML (`<table>`, `<caption>`, `<thead>`, `<tbody>`), preserving the **exact title, column headers, section headers, row labels, and cell text**.
2. Place the rebuilt table under **`#### 🗾 Supplemental Tables`**.
3. Preserve **footnotes verbatim** after the table (use `<p><em>…</em></p>`), with **`<sup>`** for symbols/letters.
4. **No inference**: do not add values or wording not present in the source; if a cell is blank in the source, use a non‑breaking space (`&nbsp;`) or `—`.
5. If the original table spans **multiple images**, **merge** into a **single HTML table** in reading order.
