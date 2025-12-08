# Flashcard Markdown Formatting Guidelines (Gold Standard, Reverse‑Engineered)

This README is the **single source of truth** for generating board‑style medical flashcard markdown files from MKSAP‑like inputs (Answer & Critique, Key Points, Related Text, Tables, Figures, Videos).  
**Input**: Source text only. **Output**: A strictly formatted `.md` file ready for downstream use (e.g., Anki).  
If output ever drifts, **discard and regenerate** using the gold‑standard examples and the rules below.

**Gold‑standard examples for structure fallback**
- `PMMCQ24001.md`
- `PMMCQ24006.md`
- (Also referenced in prior instructions: `CVQQQ24018.md`, `CVMCQ24044.md`)


## 🔄 Section Order (Sequential Generation REQUIRED)

Generate sections **in this exact order**, with **no extra horizontal rules** (`---`) inside the **main cluster**:
1. `### 🫀 [System]: [Key Concept]`
2. `#### ✅ True Statements`
3. `#### 💬 Extra(s)`
4. `#### 📚 Reference`
5. `#### 🏷️ Tags`
6. `#### 🆔 Question ID`
7. `#### 🕒 Last Updated`

(Only after the main cluster, add:)
8. (Optional) `#### 📖 Related Text` followed by either  
   - `### 📘 Related Text Derivations`, **or**  
   - `### ✅ Additional True Statements (from Related Text)`
9. (Optional) Supplements in order:  
   - `#### 🖼️ Supplemental Figure(s)`  
   - `#### 🔊 Supplemental Video(s)`  
   - `#### 🗾 Supplemental HTML Table(s)`

**Enforcement**  
- Do not skip any section. If a section has no content, write `None`.  
- Do not place References/Tags/ID/Last Updated at the bottom; they always complete the **main cluster**.  
- Related Text and all Supplements must appear **after** the main cluster.


## 🧭 How to Generate Each Section

### 1) 🫀 Main Header
```
### 🫀 [System]: [Key Concept]
```
- **System** = discipline from the source (e.g., Critical Care Medicine, Pulmonary Medicine).  
- **Key Concept** = concise statement of the Educational Objective (e.g., “Opioid Toxicity Treatment”, “Diagnose pleural malignancy with thoracoscopy”).  
- Keep short, specific, and clinical.

### 2) ✅ True Statements
- Include **only** directly stated, stand‑alone medical facts from **Answer & Critique** and **Key Points**.  
- **No inference or paraphrasing**, except to expand abbreviations and ensure standalone clarity.  
- Avoid case‑specific phrasing (“this patient”, “in this case”); move such context to **Extras**.  
- **Abbreviations**: expand on first use, then use the short form thereafter (e.g., “bilevel positive airway pressure (**BPAP**)”).  
- **Bolding**: emphasize key clinical terms and entities (**BNP**, **NSTEMI**, **HFrEF**, **naloxone**, **thoracoscopy**).  
- **Numbered list** only (1., 2., 3., …).  
- **Deduplicate**: If Answer & Critique and Key Points repeat a fact, keep a single clear statement.

### 3) 💬 Extra(s)
- **Always include** this section. If none: write `None`.  
- Purpose: patient‑specific context, clarifications, guardrails, and operational details that **relate back** to one or more True Statements.  
- **Numbering & Mapping Rule**: The **list number corresponds to the True Statement number** it augments.  
  - Example (single mapping):  
    ```
    3. Explain why repeat dosing is needed when the opioid half‑life exceeds naloxone’s.
    ```
    (This Extra is tied to **True Statement #3**.)  
  - If an Extra relates to multiple statements, list all numbers at the start separated by commas:  
    ```
    3,5. Continuous intravenous infusion of naloxone may be used to prevent recurrent respiratory depression.
    ```
- Keep Extras **concise, factual, and actionable**.

### 4) 📚 Reference
- Include **exactly as provided** in the source (authors, title, journal, year, PMID, DOI if given).  
- If no reference is provided, write `None`.

### 5) 🏷️ Tags
- Always include. Begin with the system tag (e.g., `#CriticalCare`). Add subtopic, diagnosis, management, or modality tags (e.g., `#Toxicology #OpioidOverdose #Naloxone #AirwayManagement`).  
- Use **CamelCase** or **TitleCase** for multi‑word tags where helpful.  
- 3–8 tags recommended.

### 6) 🆔 Question ID
- Copy the exact ID from the source (e.g., `CCMCQ24001`).  
- This **must** also be used as the **file name**: `CCMCQ24001.md`.

### 7) 🕒 Last Updated
- Copy the **Month YYYY** from the source (e.g., `February 2025`).  
- If absent, write `Unknown` (do not invent).


## 📖 Related Text (Optional)

If a “Related Text” section is provided:
```
#### 📖 Related Text
MKSAP: **[Exact Title from Source]**
```
Then choose **one** of the following blocks:

### 📘 Related Text Derivations
- Use when the related text **explains reasoning, algorithms, or diagnostic/therapeutic pathways**.  
- Extract derivations as bulletproof, standalone facts (same rules as True Statements).  
- Do not duplicate facts that already appear in the main **True Statements** block.

**OR**

### ✅ Additional True Statements (from Related Text)
- Use when the related text contains **additional discrete facts** that extend the topic.  
- Same rules as True Statements (abbreviation expansion, bold key terms, numbered list, no case‑specific phrasing).


## 🧩 Supplements (Optional, order is strict)

#### 🖼️ Supplemental Figure(s)
- Embed figures only if provided. Include informative alt text and a concise caption.  
- Example:
```
![Alt text: succinct clinical description](/path/to/figure.ext "Figure: Exact Caption from Source")
```

#### 🔊 Supplemental Video(s)
- Reference video file or link with a short caption.  
- Example:
```
**Video:** Title — brief one‑line description.
```

#### 🗾 Supplemental HTML Table(s)
- For each table, include **(1) HTML**, **(2) derived statements**, **(3) optional extras** in this exact pattern:

```
<!--Table 1: Exact Title From Source-->
<table>
  <thead>
    <tr><th>Column A</th><th>Column B</th></tr>
  </thead>
  <tbody>
    <tr><td>Parent Row</td><td>Primary content</td></tr>
    <!-- Sub‑rows under a parent: use a CSS class and an en dash prefix for readability -->
    <tr class="sub-row"><td>— Sub‑item 1</td><td>Detail</td></tr>
    <tr class="sub-row"><td>— Sub‑item 2</td><td>Detail</td></tr>
  </tbody>
</table>

#### ✅ True Statements (from Table: *Exact Title From Source*)
1. [Directly stated fact captured by the table]

#### 💬 Optional Extra(s)
1. [If needed; else write `None`]
```
**Sub‑row / indentation guidance**  
- When the source uses visual indentation to indicate hierarchy, represent it by:  
  - A preceding en dash (`— `) in the first cell of sub‑rows **and**  
  - An optional `class="sub-row"` on the `<tr>` for clarity.  
- If the source uses grouped headings, consider `rowspan` and/or header rows with `<th scope="rowgroup">` as appropriate.


## 🧪 Content Rules & Edge Cases

- **No case‑based language** in True Statements (e.g., “this patient”); move such context to **Extras**.  
- **Numbers & thresholds**: reproduce as given, including units. Do not invent ranges or qualifiers.  
- **Conflicting statements**: If the source text conflicts internally, prefer **Key Points**, then **Answer & Critique**; note a brief clarification in **Extras** (mapped to the relevant True Statement number).  
- **Multiple references**: list them as separate lines in the Reference section.  
- **Abbreviation economy**: expand on first use per section. If a term only appears once, still expand it.  
- **Bolding discipline**: bold clinically salient entities (diseases, tests, therapies, imaging modalities, named scales) but avoid over‑bolding whole sentences.  
- **De‑duplication**: if the same fact appears in multiple sections (e.g., Key Points + A&C), include it once in the main True Statements.  
- **Safety language**: avoid implications beyond the text (e.g., do not generalize contraindications unless explicitly stated).


## 🧹 Validation Checklist (Pre‑Flight)

1. Header present with accurate **System** and **Key Concept**.  
2. ✅ True Statements numbered; no case‑specific language; abbreviations expanded on first use; key terms bolded.  
3. 💬 Extra(s) present; **number(s) at the start map to True Statement indices** (e.g., `3.` or `3,5.`).  
4. 📚 Reference present (or `None`).  
5. 🏷️ Tags present and reasonable coverage (system + topic).  
6. 🆔 Question ID present and used as the **file name** (`[ID].md`).  
7. 🕒 Last Updated present (Month YYYY or `Unknown`).  
8. Related Text (if any) appears **after** the main cluster and uses either *Derivations* or *Additional True Statements* block (not both unless the source logically requires both).  
9. Supplements (if any) follow in the required order; tables include HTML + derived statements + extras.  
10. No `---` horizontal rules inside the main cluster; only between major clusters (Main → Related Text → Supplements).


## ♻️ Regeneration & Fallback

If any validation item fails:  
- **Discard and regenerate** using this README; compare against `PMMCQ24001.md` and `PMMCQ24006.md`.  
- Maintain **exact headings**, section order, and numbering conventions.


## ✅ Minimal Template (Copy/Paste Skeleton)

```
### 🫀 [System]: [Key Concept]

#### ✅ True Statements
1. 
2. 

#### 💬 Extra(s)
1. 
2. 

#### 📚 Reference
[Full citation or None]

#### 🏷️ Tags
#System #Subtopic #Diagnosis #Management

#### 🆔 Question ID
[ID]

#### 🕒 Last Updated
[Month YYYY]

---

#### 📖 Related Text
MKSAP: **[Title]**

### 📘 Related Text Derivations
#### ✅ True Statements
1. 

#### 💬 Extra(s)
1. 

---

#### 🖼️ Supplemental Figure(s)

#### 🔊 Supplemental Video(s)

#### 🗾 Supplemental HTML Table(s)

<!--Table 1: [Title]-->
<table>...</table>

#### ✅ True Statements (from Table: *[Title]*)
1. 

#### 💬 Optional Extra(s)
1. 
```
