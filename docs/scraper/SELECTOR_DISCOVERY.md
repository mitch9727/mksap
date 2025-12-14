# CSS Selector Discovery Guide

## Quick Reference: Converting HTML to CSS Selectors

When you inspect an element in DevTools, you'll see HTML like:
```html
<input name="password" autocomplete="current-password" type="password" id="password2" class="form-control" value="">
```

You can use any of these to create a selector:

| What You See | CSS Selector | Format |
|---|---|---|
| `id="password2"` | `#password2` | `#` + id name |
| `name="password"` | `input[name="password"]` | `element[attribute="value"]` |
| `class="form-control"` | `.form-control` | `.` + class name |
| `type="password"` | `input[type="password"]` | `element[attribute="value"]` |
| Multiple attributes | `input[name="password"][type="password"]` | Combine with `[]` |
| Text content | `button:contains("Login")` | `:contains()` pseudo-selector |

## Elements to Find

### 1. Login Indicator
**What to look for:** Element showing you're logged in
**Examples:** User name, profile icon, "Logout" button, user menu
**Your HTML:**
```
(paste the HTML element here)
```
**Selector:**

---

### 2. Question List Container
**What to look for:** The div or section holding all question rows/cards
**Examples:** `<div class="question-list">`, `<tbody>`, `<ul class="questions">`
**Your HTML:**
```
(paste the HTML element here)
```
**Selector:**

---

### 3. Question Item (Individual)
**What to look for:** A single question row/card in the list
**Examples:** `<tr>`, `<li>`, `<div class="question-card">`
**Your HTML:**
```
(paste the HTML element here)
```
**Selector:**

---

### 4. Question Modal/Container
**What to look for:** The popup or section showing full question details
**Examples:** `<div class="modal-content">`, `<dialog>`, `<div role="dialog">`
**Your HTML:**
```
(paste the HTML element here)
```
**Selector:**

---

### 5. Question ID
**What to look for:** The question number (e.g., "CVMCQ24042")
**Examples:** `<h1>`, `<span>`, `<div class="question-id">`
**Your HTML:**
```
(paste the HTML element here)
```
**Selector:**

---

### 6. Educational Objective
**What to look for:** The learning objective text
**Examples:** `<div class="educational-objective">`, `<p>` after "Educational Objective" heading
**Your HTML:**
```
(paste the HTML element here)
```
**Selector:**

---

### 7. Care Type
**What to look for:** Inpatient/Outpatient or similar
**Examples:** `<span class="care-type">`, badge element
**Your HTML:**
```
(paste the HTML element here)
```
**Selector:**

---

### 8. Answer & Critique
**What to look for:** The full explanation/answer section
**Examples:** `<article>`, `<div class="explanation">`, `<section class="critique">`
**Your HTML:**
```
(paste the HTML element here)
```
**Selector:**

---

### 9. Key Points
**What to look for:** Key learning points or takeaways
**Examples:** `<ul class="key-points">`, `<section>` with key points
**Your HTML:**
```
(paste the HTML element here)
```
**Selector:**

---

### 10. References
**What to look for:** Citations or references section
**Examples:** `<div class="references">`, `<footer>`, reference list
**Your HTML:**
```
(paste the HTML element here)
```
**Selector:**

---

### 11. Figures/Images
**What to look for:** Diagnostic images or diagrams
**Examples:** `<img>`, `<figure>`, image elements with alt text
**Your HTML:**
```
(paste the HTML element here)
```
**Selector:**

---

### 12. Tables
**What to look for:** Data tables in the question
**Examples:** `<table>`, `<div role="table">`
**Your HTML:**
```
(paste the HTML element here)
```
**Selector:**

---

### 13. Related Text Link
**What to look for:** Link labeled "Related Text" or "Syllabus"
**Examples:** `<a href="...">Related Text</a>`
**Your HTML:**
```
(paste the HTML element here)
```
**Selector:**

---

### 14. Close Button
**What to look for:** Button to close the question modal
**Examples:** `<button class="close">`, X button, "Back" button
**Your HTML:**
```
(paste the HTML element here)
```
**Selector:**

---

### 15. Next Page Button
**What to look for:** Pagination "Next" button
**Examples:** `<button>Next</button>`, `<a href="...">Next Page</a>`
**Your HTML:**
```
(paste the HTML element here)
```
**Selector:**

---

### 16. Syllabus Content Body (Optional)
**What to look for:** Main content area on syllabus/related text page
**Examples:** `<article>`, `<main>`, `<div class="content">`
**Your HTML:**
```
(paste the HTML element here)
```
**Selector:**

---

## How to Use This Guide

1. Open MKSAP in browser
2. Press F12 to open DevTools
3. Click the Inspector tool (arrow icon)
4. Click on the element you want to identify
5. Copy the entire HTML element from DevTools
6. Paste it in the appropriate section above
7. Create the CSS selector
8. Update `src/selectors.js` with your selectors

## Common Selector Patterns

```javascript
// By ID
#myId

// By class
.myClass

// By attribute
[name="password"]
[type="submit"]
[data-qa="question-id"]

// By element and attribute
input[name="password"]
button[type="submit"]
a[href*="logout"]

// Multiple attributes
input[name="password"][type="password"]

// Text content
button:contains("Login")
a:contains("Related Text")

// Combination
div.container button.close
```

## Example: Converting Your Password Field

You provided:
```html
<input name="password" autocomplete="current-password" type="password" id="password2" class="form-control" value="">
```

**Best selectors:**
1. `#password2` (most specific - by ID)
2. `input[name="password"]` (by element + attribute)
3. `input[type="password"]` (by element + type)
4. `.form-control` (by class)

Use the **first one that works** - try in order of specificity.
