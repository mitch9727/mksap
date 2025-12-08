# 📁 Project Instructions: Medical Flashcard Markdown Generation (Unified README)

> ✅ **Canonical Formatting References** — All outputs must strictly follow the formatting and structuring styles shown in these gold‑standard examples:  
> • `CVQQQ24018.md`  
> • `CVMCQ24044.md`  
> • `CVMCQ24089.md`  
> • `CVMCQ24073.md`
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

### Figures
Use HTML `<figure>` with `<img>` and `<figcaption>`:
```html
<figure>
  <img src="[FILENAME.ext]" alt="[Descriptive alt text]">
  <figcaption>
    [Short, self‑contained legend. If an abbreviations line is provided in the source, include it verbatim. If none, omit.]<br>
    <em>[Only include a “Source:” / “Reprinted from:” line if it appears in the source, verbatim.]</em>
  </figcaption>
</figure>
```
- **Alt text** must be descriptive enough for screen readers.  
- If the main text references **arrow markers/colors** or labeled parts of a figure and the **source caption** describes them, you may include that description **verbatim** in the legend. Do not invent new labels.  
- Prefer **SVG** for line art/algorithms; PNG/JPG are acceptable for photos.

### Tables
Use semantic HTML; **no inline styles**:
```html
<table>
  <caption><strong>[Table Title]</strong></caption>
  <thead>
    <tr><th>[Col 1]</th><th>[Col 2]</th><th>[Col 3]</th></tr>
  </thead>
  <tbody>
    <tr><td>[Cell]</td><td>[Cell]</td><td>[Cell]</td></tr>
  </tbody>
</table>
<p><em>[Verbatim abbreviations and verbatim footnotes from the source only.]</em></p>
```
- Place **footnotes** immediately after the table in an italicized paragraph.  
- If the source uses superscripts/letters/numbers, **preserve them exactly** with `<sup>…</sup>`.  
- Keep units in headers or cells consistently (e.g., `ng/L`).

### Videos
- If a video is provided with a title/caption, add under `#### 🔊 Supplemental Videos`:
```html
<figure>
  <video src="[FILENAME.mp4]" controls></video>
  <figcaption>[Exact video title/caption as provided.]</figcaption>
</figure>
```

### 🔒 Footnote Fidelity Rule (Assets)
1. Use **only the footnote(s) provided** with each asset; **do not** add/remove/normalize content.  
2. Preserve **exact text** (wording, capitalization, punctuation, units, symbols, order).  
3. Footnotes belong **only** to their respective asset; **do not reuse** across assets.  
4. If **no footnotes** are provided, **omit** the block entirely.

### 📋 Table/Algorithm Images → HTML + Statement Derivations (Unlimited)

**Workflow**
1. **Transcribe** the photographed table/algorithm to semantic HTML (caption, thead, tbody) and append it under **🗾 Supplemental Tables**. Include all **units** and **category labels** exactly as shown.  
2. **Derive any number of non‑duplicate ✅ True Statements** strictly from the explicit content (values, thresholds, ranges, classes of recommendation, definitions). Place under **📘 Related Text Derivations → ✅ True Statements**.  
3. **Add 💬 Extras** for units/footnotes/measurement conditions as needed, one line per statement (repeat the index for multiple extras).  
4. **Accessibility:** Provide a meaningful `<caption>` and descriptive **alt text** when an image is also used to represent the same content.  
5. **Consistency:** Maintain original column order and header labels. If normalization improves clarity (e.g., unit harmonization), note this in **💬 Extra** without altering verbatim footnote text.

### 🧱 Table‑Derived **Standalone** Statements — Construction Rules

Include all context needed to stand alone, avoiding any reference to “the table/figure.” Put any attribution in **💬 Extra**.

**Required elements (as applicable):**
1) **Clinical subject** (condition/test/therapy or population),  
2) **Qualifiers** from row/column labels (risk group, pattern, severity class, comorbidity, setting),  
3) **Measurement/criterion** with **unit/threshold/range**,  
4) **Explicit action**,  
5) **Timing/frequency/duration**,  
6) **Prohibitions/alternatives** when listed.

**Templates (fill‑ins; brackets not included in outputs):**
- “For **[population qualifier]** with **[condition/test descriptor] [threshold/range + units]**, **[action]** **[timing/frequency/duration]**.”  
- “If **[criterion/threshold]** is present in **[population/setting]**, **[action]** **[timing/notes]**.”  
- “**[Condition/test]** **[does/does not]** require **[action]** when **[qualifier + threshold]**.”

**Example (correct style avoids citing the table in ✅):**
- ✅ “For a **high‑risk adult** with a **single solid pulmonary nodule >8 mm**, **consider chest computed tomography at 3 months, positron emission tomography/computed tomography, or tissue sampling**.”  
  💬 Extra: Derived from **‘Fleischner Society Recommendations for Single Pulmonary Nodule Follow‑Up’**.


---

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

## 🔎 Final Formatting Checklist (Quick Human Review)
Before accepting any `.md` file, confirm:  

1. **Header**
   - `### 🫀 [System]: [Key Concept]` at very top.  

2. **Section Order (must be exact)**
   - `#### ✅ True Statements`  
   - `#### 💬 Extra(s)`  
   - `#### 📚 Reference`  
   - `#### 🏷️ Tags`  
   - `#### 🆔 Question ID`  
   - `#### 🕒 Last Updated`  
   - `---`  
   - `#### 📖 Related Text` + breadcrumb (e.g., `MKSAP: ...`)  
   - `---`  
   - `### 📘 Related Text Derivations`  
     - `#### ✅ Additional True Statements (from Related Text)`  
     - `#### 💬 Extra(s)`  
   - `---` (if tables exist)  
   - `### 🗾 Supplemental HTML Table(s)` (with each table formatted)  

3. **True Statements**
   - Numbered list (1, 2, 3 …).  
   - Each item standalone; abbreviations expanded on first use; bold clinical terms.  

4. **Extras**
   - Numbered list only.  
   - **No phrases** like “Relates to X” or “Statement X.”  
   - Clean, standalone clarifications.  

5. **Separators**
   - Horizontal rule (`---`) before Related Text.  
   - Horizontal rule (`---`) before Supplemental Tables section.  

6. **Tables**
   - Each table has:
     - HTML block with `<caption>` and `<tfoot>` if footnotes exist.  
     - `#### ✅ True Statements (from Table: *Exact Title*)`  
     - `#### 💬 Optional Extra(s)`  

7. **References/Tags/ID/Last Updated**
   - Must appear **immediately after Extras** (not at bottom).  
