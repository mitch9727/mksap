# MKSAP Selectors Reference

## Complete List of CSS Selectors Used by the Scraper

All selectors have been manually discovered by inspecting the actual MKSAP website HTML and are configured in `src/selectors.js`.

### Login Section

| Field | Selector | HTML Element | Purpose |
|-------|----------|--------------|---------|
| Logged In Indicator | `span[data-testid="greeting"]` | `<span data-testid="greeting">Welcome, [User]</span>` | Verify user is authenticated |

### Navigation Section

| Field | Selector | HTML Element | Purpose |
|-------|----------|--------------|---------|
| Question Bank Link | `a[href="/app/question-bank"]` | `<a href="/app/question-bank">Question Bank</a>` | Navigate to question bank |
| Cardiovascular Link | `a[href="/app/question-bank/content-areas/cv"]` | `<a href="/app/question-bank/content-areas/cv">Cardiovascular</a>` | Navigate to CV section |
| Answered Questions Link | `a[href="/app/question-bank/content-areas/cv/answered-questions"]` | Link with answered questions href | Navigate to answered questions |

### Question List Section

| Field | Selector | HTML Element | Purpose |
|-------|----------|--------------|---------|
| Question Container | `.list-group` | `<div class="list-group">` | Container for all questions |
| Question Item | `button.list-group-item.list-group-item-action` | `<button class="list-group-item list-group-item-action">` | Individual question button to click |
| Next Page Button | `button:has-text("Next"), a:has-text("Next")` | Button or link with "Next" text | Pagination control |

### Question Detail Section

#### Metadata
| Field | Selector | HTML Element | Purpose |
|-------|----------|--------------|---------|
| Question ID | `.text-uppercase.text-nowrap` | `<span class="text-uppercase text-nowrap">CVMCQ24042</span>` | Unique question identifier |
| Educational Objective | `p.h5 span` | `<p class="h5"><span>Objective text</span></p>` | Learning objective for the question |
| Care Type | `span.tag.tag-primary` | `<span class="tag tag-primary">Inpatient</span>` | Patient care setting (multiple tags) |
| Last Updated | `.last-updated span.date` | `<div class="last-updated"><span class="date">June 2025</span></div>` | Publication/update date |

#### Content Sections
| Field | Selector | HTML Element | Purpose |
|-------|----------|--------------|---------|
| Answer & Critique | `div.critique` | `<div class="critique">Full explanation text...</div>` | Main answer explanation |
| Key Points | `ul.keypoints-list li` | `<ul class="keypoints-list"><li>Point text</li></ul>` | Learning key points (list items) |
| References | `h5:has-text("Reference") + p.small` | Paragraph after "Reference" heading | Citation/reference information |

#### Assets
| Field | Selector | HTML Element | Purpose |
|-------|----------|--------------|---------|
| Figure Images | `img[src*="d2chybfyz5ban.cloudfront.net"]` | `<img src="https://d2chybfyz5ban.cloudfront.net/...jpg">` | Diagnostic/anatomical images |
| Figure Links | `a.callout[href*="/figures/"]` | `<a class="callout" href="/app/syllabus/.../figures/...">` | Links to expand figures |
| Table Links | `a.callout[href*="/tables/"]` | `<a class="callout" href="/app/syllabus/.../tables/...">Table: Title</a>` | Links to open table modals |
| Tables | `table` | `<table>...</table>` | HTML table data (inline or in modal) |
| Syllabus Link | `a[href*="/syllabus/"]` | `<a href="/app/syllabus/...">Read Now</a>` | Link to related syllabus content |

### Syllabus/Related Text Section

| Field | Selector | HTML Element | Purpose |
|-------|----------|--------------|---------|
| Content Body | `main, article, section` | Main content container | Syllabus page content |
| Breadcrumbs | `ol.page-location li span` | `<ol class="page-location"><li><span>Topic</span></li></ol>` | Navigation breadcrumbs |

---

## Extraction Logic

### How Tables Are Extracted

MKSAP has two types of tables:

1. **Inline Tables** - Directly visible in the critique section
   - Found with selector: `table`
   - Extracted directly from the DOM

2. **Modal Tables** - Opened via callout links
   - Found with selector: `a.callout[href*="/tables/"]`
   - Clicked to open modal
   - Table extracted from modal
   - Modal closed with Escape key

### How Figures Are Extracted

- Direct images: `img[src*="d2chybfyz5ban.cloudfront.net"]`
- Downloaded to disk with original URL stored
- Alternative: Expandable figure links with `a.callout[href*="/figures/"]`

### How Breadcrumbs Are Extracted

Syllabus breadcrumbs show the content hierarchy:
- Selector: `ol.page-location li span`
- Each span text is extracted and joined with " > "
- Example: "Acute Coronary Syndromes > General Considerations for Acute Coronary Syndromes"

---

## Notes

- All selectors use Playwright locator syntax
- Multiple element selectors (care type, key points) extract all matches
- Asset extraction handles both inline elements and modal-based content
- Breadcrumbs are optional (some questions may not have syllabus links)
- Optional fields default to empty strings or empty arrays in JSON

