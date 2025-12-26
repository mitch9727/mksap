# Potential Problems & Risk Analysis - Syllabus Extraction Project

## 🔴 Critical Problems

### 1. **Page Load Time & Rendering Variability**
**Problem**: Pages have unpredictable load times (2-8+ seconds observed)
- Some pages load quickly, others take much longer
- Images within figures take additional time to render
- The loading spinner appears but timing is inconsistent

**Impact**:
- Static 2-3 second wait time may not be sufficient
- Could miss content if navigation happens too early
- Need exponential backoff or dynamic wait detection
- Each page could take 5-10 seconds instead of projected 3-5 seconds
- **Timeline impact**: Could increase from 4-6 hours to 8-12 hours

**Required Mitigations**:
```rust
// Instead of fixed waits:
wait_for_element("article h1, article h2", timeout: 10_000);
wait_for_images_to_load(timeout: 5_000);
wait_for_selector_stable(".article-content"); // Wait until DOM stabilizes
```

---

### 2. **Dynamic Expansion Content ("Expand" Buttons)**
**Problem**: Many figures have embedded "Expand" buttons that lazy-load detailed content
- Images appear collapsed/with caption only initially
- Full content only loads when "Expand" button is clicked
- Detailed figure descriptions are hidden by default

**Examples observed**:
- "ECG Demonstrating Electrical Alternans" - has caption but full image needs expansion
- "Echocardiogram" images - show thumbnail until expanded
- "Radiographs and CT Scan" - multi-panel image requires expansion

**Impact**:
- Naive extraction gets only captions, not actual detailed images
- Missing significant content from figures
- Database will show "figure referenced" but not actual figure content
- Search/analysis incomplete

**What needs to happen**:
```rust
// For each figure/expandable element:
for element in expandable_elements {
    let expand_button = element.find("button[aria-label*='Expand']");
    expand_button.click();  // Trigger expansion
    wait_for_content_to_load();
    extract_figure_details();
}
```

**Timeline impact**: +2-4 hours (each figure needs click + wait)

---

### 3. **Question Count Mismatch**
**Problem**: "Test your knowledge" boxes show question counts, but actual question text doesn't include the full question
- Shows: "3 answered of 3 questions"
- But displays: Only short objective like "Diagnose acute pericarditis."
- **Missing**: Cannot extract actual question IDs programmatically from sidebar

**Example**:
```
Test your knowledge: 1 answered of 1 question
Button text: "Diagnose acute pericarditis." ← This is the OBJECTIVE, not the question ID
```

**Impact**:
- Cannot programmatically match question IDs without clicking into question bank
- The objective text is stored in syllabus, but need to cross-reference with question database
- Relationship mapping may be imperfect if multiple questions share same objective

**What's missing**:
- No visible question ID in the syllabus
- Would need to click "Show Question" button to access actual question
- But questions open in modal/popup with ID visible only then

**Solution**: Must reference back to question database by objective text matching (fuzzy matching required)

---

### 4. **Inconsistent Content Structure Across Topics**
**Problem**: Not all subsections have the same structure
- Some have Key Points box, others don't
- Some have embedded tables, others don't
- Some have extensive image galleries, others have none
- Bibliography structure varies

**Variations observed**:
```
Epidemiology section:
├── Key Points (present)
├── Main text (heavy)
├── Minimal tables
└── No figures

Pericardial Disease section:
├── Key Points (present)
├── Test your knowledge boxes (scattered throughout)
├── Multiple tables (4-5 embedded)
├── Extensive image gallery (8-10 figures with expansions)
├── Videos (at least 1)
└── Cross-references to other topics
```

**Impact**:
- Cannot use one parsing template for all pages
- Need conditional logic for each element type
- Risk of missing content in edge cases
- Error handling becomes complex

**Required complexity**:
```rust
// Pseudo-code for adaptive parsing
if has_key_points_box() { extract_key_points(); }
if has_inline_tables() { extract_all_tables(); }
if has_expandable_figures() { expand_and_extract_all(); }
if has_videos() { extract_video_refs(); }
if has_cross_refs() { extract_cross_refs_intelligently(); }
```

---

### 5. **Table Extraction Complexity**
**Problem**: Tables have complex nested structures with formatting that's hard to preserve
- Tables in sidebars vs. inline tables behave differently
- Some tables are expandable
- Column headers might be in first row or separate
- Merged cells, row/column spans common

**Example from Pericardial Disease**:
```
Table: "Evaluation of Pericardial Disease"
Has columns: Evaluation | Acute Pericarditis | Cardiac Tamponade | Constrictive Pericarditis
Some cells have sub-bullets or multiple lines
Header row is complex with grouping
```

**Impact**:
- Converting HTML table to JSON/CSV loses formatting
- Cell content might contain HTML markup (bold, italic, links)
- Merged cells break simple row-by-row parsing
- Need to preserve original HTML structure OR lose semantic info

**Complexity**: Converting 500+ tables correctly will be error-prone

---

## ⚠️ Major Problems

### 6. **Video Extraction Not Possible Via Playwright Alone**
**Problem**: Video URLs aren't in the HTML source code initially
- Videos are loaded lazily or via API calls
- Video ID is visible, but download URL requires special handling
- CDN URLs not in static HTML (similar to question video issue discovered earlier)

**Impact**:
- Need to intercept network requests to get video URLs
- Or wait for video player to load and extract from player
- Cannot simply scrape HTML for video downloads

---

### 7. **Cross-Reference Linking Ambiguity**
**Problem**: Many syllabus sections link to other syllabus sections
- Example: "Addressing Bias, Stigma, and Discrimination in Foundations of Clinical Practice"
- Need to determine: Is this a semantic reference or navigation noise?

**Challenge**: 
- How to distinguish between:
  a) "This is a related important topic" (should extract)
  b) "This is just a navigation link" (skip)
- Context matters but hard to determine programmatically

---

### 8. **Media File Size & Storage**
**Problem**: Unknown total media footprint
- 573 topics × average 5-10 media items = 2,865-5,730+ media files
- Images could be 500KB-5MB each
- Total could be 2-30 GB+ depending on image resolution

**Impact**:
- Storage planning needed
- Download time could be 2-6 hours with reasonable bandwidth
- Bandwidth limits if rate-limited
- Database bloat if storing actual image data (vs. just references)

---

### 9. **Authentication/Session Timeout Risk**
**Problem**: Playwright must maintain session for 4-12 hours
- Browser session could timeout
- Cookies might expire
- "Re-authenticate" modals could appear mid-extraction

**Impact**:
- Extraction could fail mid-way through
- No built-in recovery mechanism
- Would need to restart entire process
- Cannot batch/pause and resume easily

---

### 10. **Heading Hierarchy Extraction Fragility**
**Problem**: Heading hierarchy is not always programmatically obvious
- `<h2>`, `<h3>` tags present, but not always used consistently
- Some headings are actually styled `<div>` or `<strong>` tags
- Heading levels don't always nest logically

**Example**:
```html
<h3>Acute Pericarditis</h3>
<h3>Clinical Presentation and Evaluation of Acute Pericarditis</h3>
<!-- Both are h3, but logically one is parent of the other -->
```

**Impact**:
- Need heuristics to determine true hierarchy
- Relationship between headings hard to infer
- Questions mapped to wrong heading level
- Database schema assumes logical nesting that may not exist

---

## 🟡 Moderate Problems

### 11. **"Show Question" / "Show Questions" Buttons**
**Problem**: Question text is hidden behind collapsible buttons
- Icon indicates "3 answered of 3 questions"
- Actual question objectives shown only after clicking "Show Questions"
- Multiple questions under same heading but order unclear

**Impact**:
- Cannot extract without clicking button (adds delay)
- Extraction is interactive, not passive
- Each subsection with questions needs 1+ additional clicks

---

### 12. **Learning Links & Related Content**
**Problem**: Sidebar shows "Learning Plan Topic" sections
- Reference to related learning topics
- Not clear if should be included in extraction
- Could be considered "noise" or "important context"

---

### 13. **Specialty Prefix Variations**
**Problem**: Question prefixes don't cleanly map to syllabus prefixes
- Question: `cvmcq24001` (Cardiovascular Multiple Choice)
- Syllabus: `cvsec24001` (Cardiovascular Section)
- Different numbering schemes

**Impact**:
- Mapping questions to syllabus requires fuzzy matching, not ID-based
- Need to rely on question objective text, not IDs

---

## 📊 Timeline Impact Summary

| Problem | Original Estimate | Revised Estimate | Add'l Time |
|---------|---|---|---|
| Dynamic load times | 3-5 sec/page × 3000 = 2.5-4 hrs | 5-10 sec/page = 4-8 hrs | +1.5-4 hrs |
| Expandable content | 0 (not planned) | 2 sec/figure × 2000 = ~1 hr | +1 hr |
| Error handling/retries | Not factored | ~10% failure rate = 24 min | +24 min |
| Session management | 0 (assumed continuous) | Potential 2-3 restarts × 1 hr | +2-3 hrs |
| **Total Revised** | **4-6 hours** | **10-18 hours** | **+6-12 hours** |

---

## 🛡️ Recommended Mitigation Strategies

### Must-Implement:
1. **Dynamic wait detection** - Wait for actual content, not fixed time
2. **Expandable content handling** - Click and wait for all expand buttons
3. **Retry logic** - Handle timeouts and failures gracefully
4. **Session management** - Detect and handle session timeouts
5. **Content validation** - Check if extraction actually succeeded before moving on

### Nice-to-Have:
6. **Parallel page downloads** - But carefully to avoid overwhelming server
7. **Checkpoint/Resume** - Save progress every N pages to allow recovery
8. **Headless browser metrics** - Monitor memory, CPU to detect issues
9. **Question cross-validation** - Verify question mapping quality

---

## ⚡ Quick Wins (To Reduce Risk)

1. **Start with 1 specialty** (CV) to prototype and find unknown unknowns
2. **Manual spot-check** first 10 pages to validate extraction quality
3. **Create test dataset** for validation before full extraction
4. **Implement extensive logging** to diagnose failures
5. **Build failure detection** - Can recognize incomplete pages and retry

---

## 🎯 Recommendation

**Proceed with careful implementation:**
- Start with Phase 1 (outline building) first
- Build Phase 2 (question mapping) with 1 section to validate
- Only after validating on ~50 pages, scale to full extraction
- Expect 10-18 hours total runtime, not 4-6 hours
- Budget for 2-3 full restarts/retries during process
- Have monitoring in place to catch failures early