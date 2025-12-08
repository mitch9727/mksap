# 📁 Project Instructions: Medical Flashcard Markdown Generation (Unified README)

> ✅ **Canonical Formatting References** — All outputs must strictly follow the formatting and structuring styles shown in these gold-standard examples:  
> • `CVQQQ24018.md`  
> • `CVMCQ24089.md`  
> • `CVMCQ24073.md`  
>
> ⚠️ Any future markdown generation **must** match these examples in section ordering, headers, numbered ✅ True Statements, 💬 Extra, 🏷️ Tags, full references, related-text derivations, and HTML-formatted supplemental material.

This document defines the **authoring standard** for converting board-style medical MCQs into **single-file**, Anki-ready markdown flashcards. Outputs are **deterministic**, **parse-friendly**, and **self-contained** (text + figures/tables/videos).

---

## 🎯 Primary Goal (Single-File Output Policy)

- **Exactly one markdown file per question**, saved to `questions/` and **named with the question ID** (e.g., `CVMCQ24073.md`).  
- The file must include **all required sections** in the order below, **plus any figures/tables/videos** appended at the end.  
- No additional helper files or sidecar notes are allowed in the question directory (assets may be external image files referenced by `<img src="...">`).

---

## 🧵 Required Section Order (Authoring Contract)

1) `### [Emoji] [System]: [Key Concept]`  
2) `#### ✅ True Statements` *(numbered; context-complete; abbreviations expanded on first mention)*  
3) `#### 💬 Extra` *(optional; matched indices to True Statements)*  
4) `#### 🏷️ Tags`  
5) `#### 📚 Reference`  
6) `#### 🆔 Question ID`  
7) `#### 🕒 Last Updated`  
8) `#### 📖 Related Text`  
9) `### 📘 Related Text Derivations`  
   - `#### ✅ True Statements — [Heading]`  
   - `#### 💬 Extra` *(if applicable)*  
   - `#### 🏷️ Tags` *(if applicable)*  
10) `#### 🖼️ Supplemental Figures`  
11) `#### 🗾 Supplemental Tables`  
12) `#### 🔊 Supplemental Videos`

---

## 🧮 Input Handling & Normalization

- Extract only **directly stated, true medical statements** from **Answer & Critique** and **Key Points**.  
- If **Related Text** is present, extract **additional non-duplicate true statements**.  
- Convert provided **tables/figures/videos** into semantic HTML under the supplemental sections, and derive non-duplicate ✅ True Statements from them.

---

## 🧠 Flashcard Construction Principles (Evidence-Based)

When extracting and writing flashcards, follow these cognitive-science–supported principles to maximize learning efficiency:

1. **Atomicity & Simplicity**  
   - Each ✅ True Statement should test *only one concept, fact, or relationship*.  
   - Avoid compound statements; if needed, split into multiple cards.

2. **Active Recall Format**  
   - Prefer question-like or cloze deletion phrasing over passive notes.  
   - Statements must be structured so that the learner has to retrieve an answer, not simply recognize it.

3. **Cloze Deletions (Preferred for Facts)**  
   - When the source provides definitional or list-based content, use cloze deletion style (`____`) to encourage active generation.  
   - Example: *“In cystic fibrosis, the most common mutation is ____.”*

4. **Contextualization**  
   - Include enough clinical context so that each statement stands alone.  
   - Expand abbreviations on first use (e.g., *“Fractional flow reserve computed tomography (FFR-CT)”*).

5. **Bidirectionality (When Applicable)**  
   - For paired associations (e.g., disease ↔ finding, drug ↔ mechanism), generate flashcards in both directions if recall from both is educationally useful.  
   - Avoid unnecessary bidirectionality for complex concepts.

6. **Optional Extras as Feedback**  
   - Use 💬 Extra to provide *concise explanations, clarifications, or common pitfalls*.  
   - No filler or generic rationale; must tie directly to the True Statement.  
   - Serves as immediate feedback during retrieval practice.

7. **Imagery and Dual Coding**  
   - If the source provides a figure or table, embed it in HTML and derive at least one statement referencing it.  
   - Visual + text (“dual coding”) enhances retention.

8. **Spaced Repetition Ready**  
   - Keep each statement concise so it can be reviewed in a few seconds when resurfaced by the algorithm.  
   - Long, paragraph-style cards are discouraged.

---

## 🔖 Related Text — Strict Heading Containment

- Use only **exact headings/captions** from the Related Text.  
- No invented or paraphrased headings.  
- Derived statements must appear under their own `#### ✅ True Statements — [Heading]`.

---

## 💬 Extras — Generation Rules

- Provide **short clarifications** only if they are directly supported by the text.  
- Match each Extra to its numbered statement.  
- No generic filler, no vignette language, no new clinical claims.

---

## 🖼️ Figures • 🗾 Tables • 🔊 Videos
- **Supplemental Tables Rule (2025 update):**  
  For every supplemental table included, a `#### ✅ True Statements (from Table: …)` block **must immediately follow the table**.  
  These statements must be atomic, context-complete, and derived directly from the table content.  
  Optional `💬 Extra` notes and `🏷️ Tags` may be added under the same block if applicable.  


- Embed all assets in strict HTML (`<figure>`, `<table>`, `<video>`).  
- Captions and footnotes must be included **verbatim**.  
- No inference or added descriptions in captions.

---

## 🏷️ Tags

- Derived from **Educational Objective** and topical tags explicitly present.  
- Use camel-case hashtags, e.g., `#Cardiology #AmbulatoryCare`.

---

## 🧾 CSV Conversion (Downstream)

Suggested export fields: `question_id`, `system`, `key_concept`, `statement_index`, `statement_text`, `extra_text`, `section`, `related_statement_index`, `related_statement_text`, `related_extra_text`, `tags`, `reference`, `last_updated`, `assets`.

---

## 🌟 Emoji Mapping by Section

| MKSAP 19 Section                   | Emoji |
| ---------------------------------- | ----- |
| General Internal Medicine          | 🩺    |
| Cardiovascular Medicine            | 🫀    |
| Pulmonary & Critical Care Medicine | 🫁    |
| Gastroenterology & Hepatology      | 🍽️   |
| Endocrinology & Metabolism         | 🧪    |
| Hematology & Oncology              | 🩸    |
| Infectious Disease                 | 🦠    |
| Nephrology                         | 🗄️    |
| Neurology                          | 🧠    |
| Rheumatology                       | 🦴    |
| Dermatology                        | 🩹    |

---

## 🚨 Strict Enforcement Policy

- **All 12 sections listed in the Required Section Order MUST be present in every file.**
- **Sections must always appear in the exact order defined above.**
- **No paraphrasing of headings, captions, or footnotes is allowed.**
- **All supplemental figures, tables, and videos MUST be embedded in HTML format with verbatim captions/footnotes.**
- **Derived True Statements MUST be generated from every section, table, or figure provided, avoiding duplicates.**
- **Extras MUST be tied to numbered statements and cannot introduce unsupported information.**
- **Tags MUST be consistent and follow camel-case convention.**
- Files not following this strict order are considered invalid.

---

*Last updated: September 2025*
