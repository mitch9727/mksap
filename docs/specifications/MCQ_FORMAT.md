# README — Gold‑Standard MCQ Markdown Generator (Anki‑ready)

## Purpose
Create **machine‑readable**, **Anki‑ready** markdown files from MCQ explanations with a **stable, repeatable structure**. Every file uses the **same headings, order, spacing, and numbering**, so a simple parser can extract fields into a CSV.

> **Scope:** Works for any Q&A explanation (“main text”) plus an optional **Related Text** section. Supports supplemental **figures, videos, and HTML tables** at the bottom.


## System Emoji Key (use in titles)
- 🫀 Cardiovascular medicine
- 🦋 Endocrinology and metabolism
- 🩺 Foundations of clinical practice
- 🤒 Common symptoms
- 🍽️ Gastroenterology and Hepatology
- 🩸 Hematology
- 🦠 Infectious disease
- 🩹 Interdisciplinary medicine and dermatology
- 💧 Nephrology
- 🧠 Neurology
- 🎗️ Oncology
- 🫁 Pulmonary and critical care medicine
- 🦴 Rheumatology

---

## Input Parsing & Extraction — Deterministic Rules

### 1) Segment the raw input
- **Main Text block** starts at the first line that equals `Answer and Critique` and ends **just before** the first line that equals `Related Text`.
- **Related Text block** starts at the line `Related Text` and continues to the end of the input.

### 2) Extract fields from the Main Text block
- **System & Care Type**:
  - Find the line containing `Care type:`. Everything **before** `Care type:` on that line is the **System** (e.g., `Cardiovascular Medicine`).
  - If the source has no space (e.g., `Cardiovascular MedicineCare type:`), insert one **before** `Care type:` during parsing.
  - Map **System → Emoji** using the **System Emoji Key**.
  - Add the **Care type** (e.g., `Ambulatory`, `Emergent`, `Inpatient`) as a tag (e.g., `#Ambulatory`).
- **Key Concept (Title tail)**:
  - If present, read `Educational Objective: …` and convert to a concise noun phrase:
    - Leading verbs → noun forms: `Manage`→`Management of`, `Diagnose`→`Diagnosis of`, `Treat`→`Treatment of`.
    - Keep disease and modifiers verbatim (e.g., `severe primary tricuspid regurgitation`).
  - If `Educational Objective` is absent, derive from the first sentence that states the primary recommendation (e.g., “The most appropriate management is …”). Convert to a general rule (“Management of …”).
- **True Statements (Main)**:
  - Extract **only** general, directly stated clinical facts/rules from the Main Text.
  - **Always include the `Key Point` line** as one True Statement (verbatim, normalized to a standalone fact).
  - Recast patient-specific sentences into **Extra(s)** attached to their parent True Statement.
  - Strip option letters `(Option A/B/C/D)`; encode the underlying rule instead (e.g., “Tricuspid valve replacement is indicated when …”).
  - Include modality/threshold statements if explicitly stated (e.g., “Echocardiography centers on RV function and pulmonary pressures”).
- **Extra(s) (Main)**:
  - Use for clarifications, “why other options are incorrect,” and case-specific rationales.
  - **Number by parent True Statement index** (e.g., `1., 4.`), not sequentially.
- **Reference**:
  - Capture everything under `Reference` **up to the blank line** (include PMID/DOI if present).
- **Question ID & Last Updated**:
  - Parse the pattern `Question ID <ID> was last updated in <Month YYYY>`. Fill:
    - **Question ID** = `<ID>` (must match the filename).
    - **Last Updated** = `<Month YYYY>`.

### 3) Extract fields from the Related Text block
- **Related Text (title line)**:
  - Immediately after `Related Text`, read the **next 2–5 non-empty lines** that list the hierarchy (e.g., `Cardiovascular Medicine`, `Valvular Heart Disease`, `Tricuspid Valve Disease`).
  - If the last line repeats the topic (e.g., `Tricuspid Valve Disease` appears twice), **deduplicate the trailing duplicate**.
  - Render as: `MKSAP: Cardiovascular Medicine, Valvular Heart Disease, Tricuspid Valve Disease`.
- **Related Text Derivations → True Statements**:
  - Extract general facts explicitly stated in the paragraphs that follow (e.g., etiologies, classic findings, evaluation tests, treatment indications, outcomes from trials).
  - Expand abbreviations at first use (e.g., **right ventricular (RV)**, **transthoracic echocardiography (TTE)**, **transesophageal echocardiography (TEE)**, **B-type natriuretic peptide (BNP)**), and **bold** key terms once per section.
  - When multiple diseases appear (e.g., **tricuspid regurgitation** and **tricuspid stenosis**), include facts for each.
- **Related Text Extra(s)**:
  - Use to hold clarifications subordinate to specific Related Text True Statements (e.g., device-lead cases may require **TEE**). Number by parent statement index (e.g., `2.`).
- **Related Text Tags**:
  - Include `#CardiovascularMedicine` plus topic tags derived **verbatim** from the hierarchy (e.g., `#ValvularHeartDisease`, `#TricuspidValveDisease`) and core entities explicitly named in the body (e.g., `#TricuspidRegurgitation`, `#TricuspidStenosis`, `#Echocardiography`, `#Surgery`, `#EdgeToEdgeRepair`). Prefer 3–8 concise tags.

### 4) Supplemental Materials
**Where assets come from:** All supplemental **images, videos, and tables** will be pasted **after the Related Text block** inside the chat. Titles (and optional captions/footnotes) are provided in plain text under the assets.

**Classification & placement (deterministic):**
- **Figure (image):** Default type for non‑tabular images (e.g., ECGs, radiographs, photos, diagrams). Place under **`#### 🖼️ Supplemental Figure(s)`**.
- **Video:** Detected by file type (e.g., `.mp4`, `.mov`) or when explicitly labeled as a video. Place under **`#### 🔊 Supplemental Video(s)`**.
- **Table (image):** Any image depicting a grid of rows/columns **or** with a title/caption indicating a table. Convert to **HTML** and place under **`#### 🗾 Supplemental HTML Table(s)`**. **Tables require derived True Statements and Optional Extra(s)** immediately after their HTML.

**Title & caption ingestion:**
- Use the **exact provided title** for the HTML comment and caption text. If both a **filename** and **display title** are present and similar, prefer the **display title**; keep filenames only as `src` values.
- If a caption/footnote paragraph follows the title, render it beneath the element (figures/videos) or inside `<tfoot>` (tables) using `<small>` text.
- If **no caption** is given, omit the caption line but still include the figure/video block.

**Images (Figures):**
- HTML template:
  ```html
  <!--Figure: Exact Title-->
  <figure>
    <img src="<filename-or-path>" alt="Concise, specific alt text derived from caption/title." />
    <figcaption>Figure: Exact Title.</figcaption>
  </figure>
  ```
- **No derived statements** are required for figures.
- **Alt text**: one line describing what a clinician should notice (e.g., *Type 1 Brugada pattern with ≥2 mm J‑point elevation and coved ST segment in V1–V3*).

**Videos:**
- HTML template:
  ```html
  <!--Video: Exact Title-->
  <video controls src="<filename-or-path>"></video>
  <p><em>Video: Exact Title.</em></p>
  <p><small>Optional caption/credit/URL.</small></p>
  ```
- **No derived statements** are required for videos.

**Tables (from images):**
- **Must** be converted to **faithful HTML** (headers, body rows, merged cells via `rowspan`/`colspan`, alignment where relevant). Preserve the original **column order**, **row order**, and **footnotes**.
- HTML template:
  ```html
  <!--Table: Exact Title-->
  <table>
    <thead>…</thead>
    <tbody>…</tbody>
    <tfoot>
      <tr><td colspan="100%"><small>Footnote(s) verbatim.</small></td></tr>
    </tfoot>
  </table>
  
  #### ✅ True Statements (from Table: *Exact Title*)
  1. [Direct fact(s) restated from the table content]
  
  #### 💬 Optional Extra(s)
  1. [Clarification tied to True Statement 1]
  ```
- **Derived statements**: include only facts explicitly present in the table cells/legend; keep numbers/thresholds verbatim.
- **Optional Extras**: short clarifications tied to specific True Statements; number by parent statement index.

**If no assets are provided:** keep all three supplemental headings and add `<!-- None -->` under each.

### 5) Abbreviation & Styling Rules
- Expand each abbreviation on first use per block; thereafter use the abbreviation.
- **Bold** key clinical terms (diagnoses, procedures, test names, treatments) once per block.
- Keep numbers/thresholds verbatim. Prefer concise, declarative sentences.

---

## Output File Naming
- **Filename = exact Question ID** (e.g., `CCMCQ24001.md`).
- One file per question.

---

## Canonical Section Order (strict)
1) **Main block (from the Answer & Critique / main explanation)**
   - Title
   - True Statements
   - Extra(s)
   - Reference
   - Tags
   - Question ID
   - Last Updated
2) **Horizontal rule** (`---`)
3) **Related Text block**
   - Related Text (title line)
4) **Horizontal rule** (`---`)
5) **Related Text Derivations**
   - True Statements (from Related Text)
   - Extra(s) (from Related Text)
   - **Related Text Tags**
6) **Horizontal rule** (`---`)
7) **Supplemental Materials (grouped and ordered)**
   - Supplemental Figure(s)
   - Supplemental Video(s)
   - Supplemental HTML Table(s)
     - For **each** table: HTML comment with title → table HTML → derived True Statements and Optional Extra(s) for that table

> **Never** reorder sections. **Never** drop required headings. **Always** keep exactly **one blank line** between sections and **use the horizontal rules** at the three boundaries shown above.

---

## Canonical Template (copy‑paste this skeleton)

### [EMOJI] [System]: [Key Concept]

#### ✅ True Statements
1. [Directly stated, stand‑alone fact from the main text; expand abbreviations on first use and **bold** key clinical terms]
2. [...]

#### 💬 Extra(s)
1. [Optional clarification **about True Statement 1** only]
4. [Optional clarification **about True Statement 4** only]

#### 📚 Reference
[Full citation or source as given]

#### 🏷️ Tags
#System #Subtopic #Diagnosis #Management (etc.)

#### 🆔 Question ID
[Exact ID, e.g., CCMCQ24044]

#### 🕒 Last Updated
[Month YYYY]

---

#### 📖 Related Text
MKSAP: [Section hierarchy and title as provided]

---

### 📘 Related Text Derivations

#### ✅ True Statements (from Related Text)
1. [Directly stated, stand‑alone fact extracted from the Related Text; expand abbreviations on first use and **bold** key clinical terms]
2. [...]

#### 💬 Extra(s) (from Related Text)
1. [Optional clarification **about Related Text True Statement 1**]
3. [...]

#### 🏷️ Related Text Tags
#System #Subtopic #DiagnosticTesting (etc.)

---

#### 🖼️ Supplemental Figure(s)
<!-- One entry per figure. Use HTML below. If none, keep heading and add `<!-- None -->` -->

<!--Figure: Exact Title-->
<figure>
  <img src="Figure_Filename.png" alt="Concise, specific alt text." />
  <figcaption>Figure: Exact Title.</figcaption>
</figure>

---

#### 🔊 Supplemental Video(s)
<!-- One entry per video. If none, keep heading and add `<!-- None -->` -->

<!--Video: Exact Title-->
<video controls src="Video_Filename.mp4"></video>
<p><em>Video: Exact Title.</em></p>

---

#### 🗾 Supplemental HTML Table(s)
<!-- Keep each table in the following block pattern. If none, keep heading and add `<!-- None -->` -->

<!--Table: Exact Title-->
<table>
  <thead>
    <tr>
      <th>Column A</th>
      <th>Column B</th>
      <th>Column C</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Cell A1</td>
      <td>Cell B1</td>
      <td>Cell C1</td>
    </tr>
    <!-- Continue exactly as in the source table, including row spans/col spans if present -->
  </tbody>
  <tfoot>
    <tr><td colspan="100%"><small>Optional table footnote(s).</small></td></tr>
  </tfoot>
</table>

#### ✅ True Statements (from Table: *Exact Title*)
1. [Direct fact(s) restated from the table content]

#### 💬 Optional Extra(s)
1. [Optional clarification **about True Statement 1**]

<!-- Repeat the block above for each additional table -->

---

## Content Extraction Rules (what to include)

### True Statements (Main and Related)
- Extract **only** facts **directly stated** in the source text (main explanation or related text). No inference.
- Each statement must **stand alone** (understandable without other context).
- **Expand abbreviations on first use**; thereafter you may use the abbreviation.
- **Bold** key clinical terms (diagnoses, drugs, procedures, test names) the first time they appear in a section.
- Keep clinical numbers/thresholds verbatim.

### Extra(s)
- **Optional.** Include only if a short clarification helps the corresponding True Statement.
- **Number by the True Statement it belongs to** (e.g., `1.` then `4.`). **Do not** renumber sequentially.
- Keep each extra short; avoid adding new facts not present in the source.
- Move **patient‑specific** details or edge‑case notes into Extra(s) rather than True Statements.

### Reference
- Use the **full citation** if provided; otherwise the exact source line given (e.g., “MKSAP 19, Pulmonary Medicine, …”).

### Tags
- Space‑separated hashtags (e.g., `#PulmonaryMedicine #PleuralDisease #Diagnosis`).
- Provide both **Main Tags** and **Related Text Tags**.

### Question ID
- Must match the **filename** exactly.

### Last Updated
- Use the current **Month YYYY** at generation time.

### Related Text handling
- Include only the **title line** under “📖 Related Text” (do **not** paste the full related text body).
- Derive statements under **📘 Related Text Derivations**.

### Supplemental Materials
- **Always include the three headings** (Figures, Videos, HTML Tables). If none, keep the heading and place `<!-- None -->` inside that section.
- **Images (Figures):** use `<figure>` → `<img>` with descriptive `alt` + `<figcaption>Figure: Title.</figcaption>`.
- **Videos:** `<video controls src="...">` and a caption paragraph below.
- **Tables:** convert to **pure HTML** faithfully (preserve row/column order, headers, merged cells via `rowspan`/`colspan`, footnotes as small text or `<tfoot>` if present). After each table, add **derived True Statements** and **Optional Extra(s)** blocks using the pattern above.
- For each asset, include an HTML **comment** with the exact title (e.g., `<!--Figure: ...-->`, `<!--Table: ...-->`, `<!--Video: ...-->`).

---

## Formatting & Spacing Rules (strict)
- Headings and emojis must match the template **exactly**.
- **One blank line** between sections.
- Use the three **horizontal rules** exactly as shown.
- Do **not** reorder **Reference / Tags / Question ID / Last Updated**; they stay **immediately** after **Extra(s)** in the main block.
- Do **not** invent data (e.g., references, tags) not present or obvious from the source; prefer concise, accurate tags.

---

## Flashcard‑Optimized True Statements (Evidence‑based)

Use these rules to turn source text into high‑yield, machine‑parsable facts suitable for Anki.

1. **Atomicity (one idea per line).** Each True Statement must express a single, testable fact; avoid chains with multiple clauses or list‑like sentences. Split long rules into multiple statements.
2. **Discriminative cues.** Prefer features that *differentiate* similar entities (e.g., Brugada vs early repolarization; tricuspid vs mitral murmurs). Include the distinctive lead/location, maneuver response, or hallmark imaging/lab detail.
3. **Precision with numbers.** Keep thresholds **verbatim** with units and comparators (\> / \< / ≥ / ≤). Do not round unless the source rounds.
4. **Positive assertions first.** State the rule directly ("X is indicated when…"). Reserve exclusions/"except" wording for **Extra(s)** unless the source is explicitly exception‑based.
5. **Cloze‑ready phrasing.** Each statement should be convertible to a single cloze deletion with a clear cue → target. Avoid pronouns (this/that/it), vague time words, or multi‑target lists.
6. **Context minimalism.** Remove patient‑specific details from True Statements; place them in **Extra(s)** if they clarify why the rule applies in the vignette.
7. **Standard terminology.** Use guideline names and standard test/procedure terms; expand abbreviations on first use; **bold** key clinical terms once per block.
8. **Clear condition–action structure.** For management statements, include **indication** → **intervention** ± **modifiers** (severity grade, refractory status, risk class, comorbidity).
9. **Scope labeling.** If a rule applies to a *specific population* (e.g., adults, pregnancy, reduced ejection fraction), name it in the statement.
10. **Avoid hedging not in the source.** Reflect certainty as written ("recommended" vs "may be considered").
11. **Tables to statements.** When deriving from tables, mirror the row‑level facts (entity → key finding → treatment) as separate atomic statements.
12. **No inference beyond text.** Do not incorporate outside knowledge; do not synthesize new thresholds or indications.

**Mini examples**
- ✅ "**Type 1 Brugada pattern** shows **coved ST‑segment elevation** ≥2 mm in **leads V1–V3**."  
- ✅ "**Tricuspid valve replacement** is indicated in **severe symptomatic primary tricuspid regurgitation** **refractory to diuretics**."  
- ➖ Split instead of chaining: "TTE evaluates RV function **and** estimates pulmonary pressures" →
  1) "**Transthoracic echocardiography (TTE)** evaluates **right ventricular function**."  
  2) "TTE allows **estimation of pulmonary artery pressure**."

---

## Minimal‑Extrapolation Policy (Verbatim‑Leaning Generation)

**Goal:** Generate True Statements that are maximally faithful to the source wording while remaining atomic and cloze‑ready.

### Sourcing
- Each True Statement must be traceable to **one explicit sentence or one table row/cell** in the provided text.
- Prefer **source phrasing**. Only change wording to: (a) make the statement stand‑alone, (b) expand abbreviations on first use, (c) standardize tense to present, (d) convert pronouns to their explicit nouns, (e) split multi‑idea sentences into atomic lines, (f) remove patient‑specific details (move to Extra[s]).

### Allowed micro‑edits (and nothing more)
1. **Subject restoration:** Replace “this/that/it/they” with the explicit term from the nearest antecedent in the same paragraph.
2. **Abbreviation expansion on first use** (retain abbreviation in parentheses).
3. **Tense normalization** to present (e.g., “is recommended”, “may be considered”).
4. **Comparator/units normalization:** Keep symbols (\>, \<, ≥, ≤) and units exactly as written; do not round.
5. **Atomic split:** Break conjunctions into separate lines (no added synonyms).
6. **Option letter removal:** Drop “(Option X)” without changing the medical content.
7. **Minimal scaffolding:** If needed, prepend population/context phrases **using the exact nouns** from the source (e.g., “In severe symptomatic primary tricuspid regurgitation…”).

### Prohibited edits
- No synonyms that change nuance (e.g., “reasonable” ≠ “recommended”). Keep **modal verbs and qualifiers** exactly.
- No synthesis across separate sentences/rows unless the relationship is explicit in the text (e.g., “therefore”, “recommended when…”).
- No inferred thresholds, disease stages, or guideline classes not verbatim in the source.
- Do not convert negatives to positives (or vice versa) unless the source is explicitly framed that way.

### Tables → Statements
- Derive statements directly from **row‑level** content; one row = one (or more) atomic statements mirroring the cell wording.
- Include footnote constraints **only if** they appear in the legend/footnote; place clarifications in **Optional Extra(s)** and number by parent.

### Micro‑workflow (per statement)
1) Copy the source sentence/row text.  
2) Expand first‑use abbreviations; restore explicit subject; normalize tense.  
3) Remove case‑specific context → move to **Extra(s)**.  
4) Ensure **one idea only**; split if needed.  
5) Preserve numbers, units, comparators, and qualifiers verbatim.  
6) **Bold** key clinical terms once per block.  
7) Verify cloze‑readiness (clear cue → target).

---

## Quality‑Control Checklist (run this before saving)
1. Filename equals **Question ID** (e.g., `PMMCQ24061.md`).
2. Title format is `### [EMOJI] [System]: [Key Concept]` with the correct **system emoji**.
3. **Main block** order: True Statements → Extra(s) → Reference → Tags → Question ID → Last Updated.
4. Exactly **one blank line** between sections; horizontal rules placed exactly as specified.
5. **Educational Objective** (if present) is transformed into a concise **Key Concept**.
6. **Key Point** is included as a True Statement (normalized), not lost.
7. Extra(s) numbers mirror their **parent True Statement numbers** (e.g., `1., 4.`) — not sequential.
8. **Related Text** shows the hierarchy line as `MKSAP: …` (deduplicated), and its facts live only under **Related Text Derivations**.
9. **No verbatim Related Text body** is pasted into the main file.
10. All three **Supplemental** headings exist; `<!-- None -->` added where empty.
11. **Every provided asset appears once** in the correct section: images under Figures, videos under Videos, tables converted to **valid HTML** under HTML Tables.
12. **Each table** is followed by per‑table **True Statements** and **Optional Extra(s)** blocks; figures/videos have **no** derived statements.
13. Captions/footnotes preserved (figures/videos as paragraphs; tables inside `<tfoot>`). Alt text present for all `<img>`.
14. Reference present and accurate; Tags present for both Main and Related blocks (3–8 each, derived from explicit terms).
15. **Last Updated** matches the parsed month/year (e.g., `June 2025`).
16. Abbreviations expanded on first use; key terms **bolded** once per block; no patient‑specific phrasing in True Statements.
17. **Flashcard quality:** True Statements are **atomic** and **cloze‑ready**; include **discriminative cues** where relevant; numbers carry **units and comparators**; negative/"except" forms moved to **Extra(s)** unless the source is exception‑based.

---

## Parser Anchors (for downstream CSV)
Use these **exact** headings as stable anchors:
- Title lines beginning `### ` followed by a **system emoji** (see key) and a space.
- `#### ✅ True Statements`
- `#### 💬 Extra(s)`
- `#### 📚 Reference`
- `#### 🏷️ Tags`
- `#### 🆔 Question ID`
- `#### 🕒 Last Updated`
- `#### 📖 Related Text`
- `### 📘 Related Text Derivations`
- `#### ✅ True Statements (from Related Text)`
- `#### 💬 Extra(s) (from Related Text)`
- `#### 🏷️ Related Text Tags`
- `#### 🖼️ Supplemental Figure(s)`
- `#### 🔊 Supplemental Video(s)`
- `#### 🗾 Supplemental HTML Table(s)`
- `#### ✅ True Statements (from Table: *Title*)`
- `#### 💬 Optional Extra(s)`

---

## Common Pitfalls & Fixes
- **Pitfall:** Extras numbered 1, 2, 3 sequentially → **Fix:** number by their parent True Statement numbers (`1., 4., 7.` …).
- **Pitfall:** Pasting the full Related Text body → **Fix:** include only the **title**; derive facts under **Related Text Derivations**.
- **Pitfall:** Tables summarized in prose only → **Fix:** provide **HTML table** + derived statements.
- **Pitfall:** Reference/Tags moved to the bottom → **Fix:** keep them **immediately after Extra(s)** in the main block.
- **Pitfall:** Missing horizontal rules or extra blank lines → **Fix:** enforce exact placement and spacing.

---

## Minimal Working Example (with placeholders)

### 🫁 Pulmonary and Critical Care Medicine: Evaluation of Pleural Effusion

#### ✅ True Statements
1. **Pleural effusions** are classified as **transudative** or **exudative** based on **Light’s criteria**.
2. Exudates typically reflect **increased capillary permeability** from **inflammation**.

#### 💬 Extra(s)
1. Light’s criteria include thresholds for **protein** and **lactate dehydrogenase (LDH)** ratios.

#### 📚 Reference
MKSAP 19, Pulmonary Medicine — Pleural Disease — Pleural Effusion.

#### 🏷️ Tags
#PulmonaryMedicine #PleuralDisease #Diagnosis

#### 🆔 Question ID
PMMCQ24061

#### 🕒 Last Updated
September 2025

---

#### 📖 Related Text
MKSAP: Pulmonary Medicine, Pleural Disease, Pleural Fluid Analysis

---

### 📘 Related Text Derivations

#### ✅ True Statements (from Related Text)
1. **Pleural fluid analysis** begins with assessing **appearance** and determining whether the effusion is **exudative** or **transudative**.

#### 💬 Extra(s) (from Related Text)
1. Typical **exudative** etiologies include **infection**, **malignancy**, and **pulmonary embolism**.

#### 🏷️ Related Text Tags
#PleuralEffusion #PleuralFluid #LightCriteria

---

#### 🖼️ Supplemental Figure(s)
<!-- None -->

---

#### 🔊 Supplemental Video(s)
<!-- None -->

---

#### 🗾 Supplemental HTML Table(s)

<!--Table: Light’s Criteria for Exudates-->
<table>
  <thead>
    <tr>
      <th>Criterion</th>
      <th>Threshold</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Protein ratio (pleural/serum)</td>
      <td>> 0.5</td>
    </tr>
    <tr>
      <td>LDH ratio (pleural/serum)</td>
      <td>> 0.6</td>
    </tr>
    <tr>
      <td>Pleural LDH</td>
      <td>> 2/3 upper limit of normal for serum LDH</td>
    </tr>
  </tbody>
</table>

#### ✅ True Statements (from Table: *Light’s Criteria for Exudates*)
1. An **exudate** is present if **any one** of the three criteria is met.

#### 💬 Optional Extra(s)
1. The criteria use **ratios** comparing pleural to **serum** values for **protein** and **LDH**.

---

*End of README.*


## Worked Asset Examples (from your sample)

#### 🖼️ Supplemental Figure(s)
<!--Figure: ECG Demonstrating a Type 1 Brugada Pattern-->
<figure>
  <img src="ECG_Demonstrating_a_Type_1_Brugada_Pattern.jpg" alt="Type 1 Brugada pattern with ≥2 mm J-point elevation, coved ST-segment, and T-wave inversions in V1–V3." />
  <figcaption>Figure: ECG Demonstrating a Type 1 Brugada Pattern.</figcaption>
</figure>

---

#### 🔊 Supplemental Video(s)
<!--Video: Rheumatic Mitral Regurgitation-->
<video controls src="Rheumatic Mitral Regurgitation.mp4"></video>
<p><em>Video: Rheumatic Mitral Regurgitation.</em></p>
<p><small>The carotid pulse is normal. In the mitral area, S1 is obscured by a high-frequency grade 2 holosystolic murmur that begins with mitral closure and continues through aortic closure. Credit: Michael S. Gordon Center for Simulation and Innovation in Medical Education, University of Miami Miller School of Medicine, Miami, Florida. https://gordoncenter.miami.edu</small></p>

---

#### 🗾 Supplemental HTML Table(s)
<!--Table: Inherited Syndromes Characterized by Sudden Cardiac Death-->
<table>
  <thead>
    <tr>
      <th>Disorder</th>
      <th>Presenting Symptoms and Characteristic Findings</th>
      <th>Potential Treatments<sup>a</sup></th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Long QT syndrome</td>
      <td>Syncope during sleep, auditory triggers, and/or during exercise (depending on subtype); QTc usually &gt;460 ms; torsades de pointes</td>
      <td>β-Blockers, avoidance of QT-prolonging drugs; selected patients: ICD, sympathectomy, exercise restriction</td>
    </tr>
    <tr>
      <td>Brugada syndrome</td>
      <td>Syncope during sleep, VF; coved ST-segment elevation in early precordial leads (V1 through V3)</td>
      <td>ICD, avoidance or management of triggers (drugs, fever), catheter ablation</td>
    </tr>
    <tr>
      <td>Catecholaminergic polymorphic VT</td>
      <td>Syncope, polymorphic or bidirectional VT during exercise or emotional distress</td>
      <td>β-Blockers, verapamil, flecainide, ICD, exercise abstinence (uniform)</td>
    </tr>
    <tr>
      <td>Arrhythmogenic right ventricular cardiomyopathy/dysplasia</td>
      <td>Syncope, palpitations, T-wave inversions in leads V1 through at least V3, monomorphic VT, frequent PVCs, and abnormal right ventricular size and function on echocardiography or CMR imaging</td>
      <td>ICD, β-blockers, antiarrhythmic medications, catheter ablation, exercise abstinence (uniform)</td>
    </tr>
    <tr>
      <td>Hypertrophic cardiomyopathy</td>
      <td>Syncope, VF during exercise, increased QRS voltage with or without repolarization abnormalities on ECG</td>
      <td>ICD, β-blockers, disopyramide, catheter ablation, surgical myectomy</td>
    </tr>
  </tbody>
  <tfoot>
    <tr>
      <td colspan="100%"><small>CMR = cardiac magnetic resonance; ICD = implantable cardioverter-defibrillator; PVC = premature ventricular contraction; QTc = corrected QT interval; VF = ventricular fibrillation; VT = ventricular tachycardia. <sup>a</sup>Treatment recommendations for ICD placement in inherited arrhythmia syndromes are guided by risk stratification with criteria that are often disease specific. In addition, antiarrhythmic drugs are often required for recurrent ventricular arrhythmias.</small></td>
    </tr>
  </tfoot>
</table>

#### ✅ True Statements (from Table: *Inherited Syndromes Characterized by Sudden Cardiac Death*)
1. **Brugada syndrome** presents with **coved ST-segment elevation** in leads **V1–V3** and is typically managed with **implantable cardioverter-defibrillator (ICD)** therapy and **trigger avoidance**.
2. **Long QT syndrome** is associated with **QTc usually &gt;460 ms** and **torsades de pointes**, and first-line therapy is **β-blockade** with avoidance of **QT-prolonging drugs**.
3. **Catecholaminergic polymorphic ventricular tachycardia (VT)** triggers **polymorphic/bidirectional VT** during **exercise or emotional stress**; treatment includes **β-blockers**, sometimes **flecainide or verapamil**, and **ICD**.
4. **Arrhythmogenic right ventricular cardiomyopathy** shows **T‑wave inversions in V1–V3** and structural right ventricular abnormalities; therapies include **ICD**, **β‑blockers**, and **catheter ablation** with **exercise abstinence**.
5. **Hypertrophic cardiomyopathy** may cause **syncope** and **ventricular fibrillation during exercise** with **increased QRS voltage**; therapies include **β‑blockers**, **disopyramide**, **ICD**, and **septal reduction** (e.g., surgical myectomy).

#### 💬 Optional Extra(s)
2. Selected **Long QT** patients may require **ICD** or **sympathectomy** and **exercise restriction** after risk stratification.

---
