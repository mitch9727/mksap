# Refined Syllabus Extraction Plan - Focused & Hierarchical

## Problem Analysis

Current issues with naive extraction:
1. **Hyperlink Overload**: Every page has 20-50+ links (many to other topics)
2. **Noise in Extraction**: Cross-references to other syllabus sections don't belong in this section's content
3. **Lost Hierarchy**: No distinction between main topics, subtopics, and question references
4. **Inefficient Linking**: Hard to relate syllabus content back to specific questions later

## Solution: Hierarchical Outline-First Extraction

Instead of extracting full content immediately, first build a **complete syllabus outline** that maps:
- Specialty → Section → Subsection → Heading → Subheading → Questions

---

## Phase 1: Build Syllabus Outline (No Content Yet)

### Step 1.1: Extract Section Structure from Sidebar

For each specialty, navigate to `/app/syllabus/{specialty}` and extract the table of contents structure:
```rust
struct SyllabusOutline {
    specialty: String,
    sections: Vec<Section>,
}

struct Section {
    id: String,              // cvsec24001
    title: String,           // "Epidemiology and Risk Factors"
    subsections: Vec<Subsection>,
}

struct Subsection {
    id: String,              // cvsec24001_24001
    title: String,           // "Overview"
    parent_section: String,
    url: String,
}
```

**Where to find it**: From the sidebar navigation (ref_912 in previous analysis)
- Extract all `<a>` tags with `href="/app/syllabus/{specialty}/{section_id}/{subsection_id}"`
- Group by section_id to understand hierarchy

**Example from Pericardial Disease:**
```
Pericardial Disease (cvsec24009)
├── Acute Pericarditis (cvsec24009_24001)
│   ├── Clinical Presentation and Evaluation (cvsec24009_24002)
│   └── Management (cvsec24009_24003)
├── Pericardial Effusion and Cardiac Tamponade (cvsec24009_24004)
│   ├── Pericardial Effusion (cvsec24009_24005)
│   └── Cardiac Tamponade (cvsec24009_24006)
│       ├── Clinical Presentation and Evaluation (cvsec24009_24010)
│       └── Management (cvsec24009_24011)
└── Constrictive Pericarditis (cvsec24009_24009)
    ├── Clinical Presentation and Evaluation (cvsec24009_24024)
    └── Management (cvsec24009_24025)
```

### Step 1.2: Extract Heading Hierarchy from Content

For each subsection page, extract the **internal heading structure** (not external links):
```rust
struct ContentHierarchy {
    subsection_id: String,
    headings: Vec<ContentHeading>,
}

struct ContentHeading {
    level: u32,              // 1 = h1, 2 = h2, 3 = h3, etc.
    title: String,
    order: u32,              // Position on page
    section_id: String,      // HTML id/anchor if available
}
```

**Where to find it**: From the main article (ref_421)
- Extract all `<h2>`, `<h3>`, `<h4>` within the article
- Ignore all headings outside the article
- Track order of appearance

**Example from Pericardial Disease page:**
```
Subsection: cvsec24009_24002 (Clinical Presentation and Evaluation of Acute Pericarditis)
├── H3: "Clinical Presentation and Evaluation of Acute Pericarditis"
├── H3: "Key Point"
├── H3: "Causes of Pericardial Disease" (with embedded table)
├── H3: "Evaluation of Pericardial Disease" (with embedded table)
├── H3: "Pericarditis" (with embedded video)
└── H3: "ECG Changes of Acute Pericarditis" (with embedded figure)
```

---

## Phase 2: Link Questions to Syllabus Content

### Step 2.1: Extract Embedded Question References

Within each subsection, find the "Test your knowledge" boxes:
```rust
struct SubsectionQuestion {
    subsection_id: String,
    question_text: String,           // "Diagnose acute pericarditis."
    question_count: String,           // "3 answered of 3 questions"
    heading_context: String,          // Which heading this appears under
    heading_level: u32,               // Which level heading
}
```

**Where to find it**: Look for `"Test your knowledge:"` pattern
- DOM: regions with `<generic>` containing "Test your knowledge:" followed by question counts
- Extract button text which contains the question objective
- Map to the nearest preceding heading

**Example from Pericardial Disease:**
```
Heading: "Clinical Presentation and Evaluation of Acute Pericarditis"
  Questions:
    - "Diagnose acute pericarditis."
    - "Identify manifestations of pericarditis on ECG."
    - "Identify pericardial rub on auscultation."

Heading: "Pericardial Effusion"
  Questions:
    - "Diagnose pericardial effusion secondary to tuberculosis."
    - "Manage an asymptomatic idiopathic pericardial effusion."
    - "Manage uncomplicated idiopathic pericardial effusion."
    - "Diagnose pericardial effusion using point-of-care ultrasonography."
```

### Step 2.2: Create Question-to-Syllabus Mapping
```rust
struct QuestionSyllabusMapping {
    question_objective: String,      // "Diagnose acute pericarditis."
    specialty: String,                // "cv"
    section_id: String,               // "cvsec24009"
    subsection_id: String,            // "cvsec24009_24002"
    heading_context: String,          // The heading under which this Q appears
    heading_level: u32,
}
```

**Database Schema:**
```sql
CREATE TABLE question_syllabus_map (
    id TEXT PRIMARY KEY,
    question_objective TEXT NOT NULL,
    specialty TEXT NOT NULL,
    section_id TEXT NOT NULL,
    subsection_id TEXT NOT NULL,
    heading_context TEXT,
    heading_level INTEGER,
    FOREIGN KEY(subsection_id) REFERENCES subsections(id)
);
```

---

## Phase 3: Focused Content Extraction

### Step 3.1: Extract Only Main Content (Skip External Links)

For each subsection, extract **only the content within the `<article>` tag**, organized by heading:
```rust
struct SubsectionFullContent {
    subsection_id: String,
    title: String,
    sections: Vec<HeadingSection>,
}

struct HeadingSection {
    heading: String,
    heading_level: u32,
    order: u32,
    content: String,                  // Text only
    media: Vec<MediaReference>,
    tables: Vec<TableContent>,
    key_points: Option<String>,       // If present in Key Point box
    questions: Vec<String>,           // Questions under this heading
    links: Vec<ContentLink>,          // ONLY internal cross-ref links to other syllabus
}

struct ContentLink {
    text: String,
    href: String,
    link_type: LinkType,  // Internal, ExternalReference, Table, Figure
}

enum LinkType {
    TableReference,        // Links to "Table: ..."
    FigureReference,       // Links to "Figure: ..."
    VideoReference,        // Links to videos
    SyllabusReference,     // Links to other syllabus sections
    ExternalReference,     // External URLs (ignore)
}

struct MediaReference {
    media_type: String,    // "table", "figure", "video"
    id: String,            // cvtab24041
    title: String,         // Title from link text
    position_in_text: u32, // Where it appears
}
```

### Step 3.2: Smart Link Filtering

**EXCLUDE these link types:**
- External links (URLs starting with `http://`, `https://`)
- Cross-specialty references that don't add value
- Bibliography links
- "View Learning Plan" links

**INCLUDE these link types:**
- `Table: ...` references (internal tables)
- `Figure: ...` references (internal figures)
- `Video: ...` references (internal videos)
- Cross-references to related syllabus sections (marked with italic/special styling)

**Detection logic:**
```rust
fn should_extract_link(href: &str, link_text: &str) -> bool {
    // Exclude external links
    if href.starts_with("http") && !href.contains("mksap.acponline.org") {
        return false;
    }
    
    // Exclude learning plan, annotations, etc.
    if href.contains("/app/learning-plan/") || href.contains("/app/annotations") {
        return false;
    }
    
    // Include table/figure/video references
    if link_text.starts_with("Table:") || 
       link_text.starts_with("Figure:") || 
       link_text.starts_with("Video:") {
        return true;
    }
    
    // Include syllabus cross-references (href contains /syllabus/)
    if href.contains("/app/syllabus/") {
        return true;  // But only if it's a semantic reference, not just navigation
    }
    
    // Default: exclude
    false
}
```

---

## Phase 4: Media Extraction (Targeted)

Instead of extracting every image, extract ONLY referenced media:
```rust
struct MediaToDownload {
    media_type: String,    // "figure", "table", "video"
    id: String,
    url: Option<String>,   // For figures
    referenced_in: Vec<String>,  // List of subsection_ids that reference it
    download_priority: u32, // Higher if referenced multiple times
}
```

**Rules:**
1. Extract figure IDs only from `<a href="/app/syllabus/*/figures/*">`
2. Extract table IDs only from `<a href="/app/syllabus/*/tables/*">`
3. Extract video IDs only from `<a href="/app/syllabus/*/videos/*">`
4. Count how many subsections reference each media item
5. Download media in order of reference frequency

---

## Complete Data Model
```rust
struct CompleteSyllabusDatabase {
    // Structure
    specialties: Vec<Specialty>,
    sections: Vec<Section>,
    subsections: Vec<Subsection>,
    
    // Content
    headings: Vec<ContentHeading>,
    subsection_content: Vec<SubsectionContent>,
    
    // Relationships
    question_mappings: Vec<QuestionSyllabusMapping>,
    media_references: Vec<MediaReference>,
    
    // Media
    figures: Vec<MediaFile>,
    tables: Vec<MediaFile>,
    videos: Vec<MediaFile>,
}

struct Specialty {
    id: String,              // "cv"
    name: String,           // "Cardiovascular Medicine"
    section_count: u32,
}

struct Subsection {
    id: String,
    title: String,
    section_id: String,
    heading_hierarchy: Vec<ContentHeading>,
    question_count: u32,
    embedded_media_count: u32,
}

struct SubsectionContent {
    subsection_id: String,
    heading_sections: Vec<HeadingSection>,
    text_length: u32,
    media_count: u32,
    related_questions: Vec<String>,
    cross_references: Vec<String>,  // Other syllabus sections referenced
}
```

---

## Database Schema (Refined)
```sql
-- Structure
CREATE TABLE specialties (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL
);

CREATE TABLE sections (
    id TEXT PRIMARY KEY,
    specialty_id TEXT NOT NULL,
    title TEXT NOT NULL,
    FOREIGN KEY(specialty_id) REFERENCES specialties(id)
);

CREATE TABLE subsections (
    id TEXT PRIMARY KEY,
    section_id TEXT NOT NULL,
    title TEXT NOT NULL,
    url TEXT,
    FOREIGN KEY(section_id) REFERENCES sections(id)
);

-- Content Hierarchy
CREATE TABLE content_headings (
    id TEXT PRIMARY KEY,
    subsection_id TEXT NOT NULL,
    heading_text TEXT NOT NULL,
    heading_level INTEGER,
    heading_order INTEGER,
    FOREIGN KEY(subsection_id) REFERENCES subsections(id)
);

CREATE TABLE heading_sections (
    id TEXT PRIMARY KEY,
    subsection_id TEXT NOT NULL,
    heading_id TEXT,
    content_text TEXT,
    heading_level INTEGER,
    section_order INTEGER,
    FOREIGN KEY(subsection_id) REFERENCES subsections(id),
    FOREIGN KEY(heading_id) REFERENCES content_headings(id)
);

-- Question Mapping
CREATE TABLE question_syllabus_mapping (
    id TEXT PRIMARY KEY,
    question_objective TEXT NOT NULL,
    specialty TEXT NOT NULL,
    section_id TEXT NOT NULL,
    subsection_id TEXT NOT NULL,
    heading_context TEXT,
    heading_level INTEGER,
    UNIQUE(subsection_id, question_objective),
    FOREIGN KEY(subsection_id) REFERENCES subsections(id)
);

-- Media References
CREATE TABLE media_references (
    id TEXT PRIMARY KEY,
    subsection_id TEXT NOT NULL,
    media_type TEXT NOT NULL,  -- 'figure', 'table', 'video'
    media_id TEXT NOT NULL,
    media_title TEXT,
    position_in_heading INTEGER,
    FOREIGN KEY(subsection_id) REFERENCES subsections(id)
);

-- Syllabus Cross-References
CREATE TABLE syllabus_crossreferences (
    id TEXT PRIMARY KEY,
    from_subsection TEXT NOT NULL,
    to_subsection TEXT,
    reference_text TEXT,
    reference_type TEXT,  -- 'semantic', 'related_topic'
    FOREIGN KEY(from_subsection) REFERENCES subsections(id),
    FOREIGN KEY(to_subsection) REFERENCES subsections(id)
);

-- Media Files
CREATE TABLE media_files (
    id TEXT PRIMARY KEY,
    media_id TEXT NOT NULL,
    media_type TEXT NOT NULL,
    title TEXT,
    url TEXT,
    local_path TEXT,
    reference_count INTEGER,
    downloaded BOOLEAN DEFAULT FALSE,
    UNIQUE(media_id, media_type)
);
```

---

## Extraction Implementation (Pseudocode)
```rust
#[tokio::main]
async fn main() {
    // Phase 1: Build Outline
    println!("Phase 1: Building syllabus outline...");
    let outline = build_complete_outline().await;
    save_outline_to_db(&outline).await;
    println!("Built outline: {} sections, {} subsections", 
             outline.section_count(), outline.subsection_count());
    
    // Phase 2: Link Questions
    println!("Phase 2: Mapping questions to syllabus...");
    for subsection in &outline.all_subsections() {
        let questions = extract_embedded_questions(&subsection).await;
        save_question_mappings(&subsection.id, &questions).await;
    }
    println!("Mapped {} question-syllabus relationships", mapped_count);
    
    // Phase 3: Extract Content
    println!("Phase 3: Extracting focused content...");
    for subsection in &outline.all_subsections() {
        let content = extract_focused_content(&subsection).await;
        save_content_to_db(&content).await;
    }
    
    // Phase 4: Download Media
    println!("Phase 4: Downloading referenced media...");
    let media_to_download = get_referenced_media().await;  // Only media that's referenced
    for media in media_to_download {
        download_media(&media).await;
    }
    
    println!("Extraction complete!");
}

async fn extract_focused_content(subsection: &Subsection) -> SubsectionContent {
    navigate_to(&subsection.url).await;
    
    let article = get_element("article").await;
    let mut content = SubsectionContent::new(&subsection.id);
    
    // Extract only from within <article>
    for element in article.children() {
        match element.tag_name().await {
            "h2" | "h3" | "h4" => {
                let heading = extract_heading(&element).await;
                content.add_heading(heading);
            }
            "p" | "ul" | "ol" => {
                let text = element.inner_text().await;
                content.add_text_to_current_section(text);
            }
            "table" => {
                let table = parse_table(&element).await;
                content.add_table(table);
            }
            "a" => {
                let href = element.get_attribute("href").await;
                let text = element.inner_text().await;
                if should_extract_link(&href, &text) {
                    content.add_link(href, text);
                }
            }
            _ => {}  // Ignore other elements
        }
    }
    
    content
}

fn should_extract_link(href: &str, text: &str) -> bool {
    // Skip external URLs
    if href.starts_with("http") && !href.contains("mksap.acponline.org") {
        return false;
    }
    
    // Skip navigation links
    if href.contains("/app/learning-plan/") || 
       href.contains("/app/annotations") ||
       href.contains("/app/question-bank/") {
        return false;
    }
    
    // Keep table, figure, video references
    if text.starts_with("Table:") || 
       text.starts_with("Figure:") || 
       text.starts_with("Video:") {
        return true;
    }
    
    // Keep syllabus cross-references if they're meaningful
    if href.contains("/app/syllabus/") && text.contains("in ") {
        // "Understanding Patient Context and Social Drivers of Health in Foundations..."
        return true;
    }
    
    false
}
```

---

## Output Structure
```
output/
├── syllabus_outline.json          # Complete hierarchy: specialty → section → subsection → headings
├── question_syllabus_map.json     # All question-to-syllabus relationships
├── syllabus_content_by_spec/
│   ├── cv/
│   │   ├── cvsec24001_outline.json
│   │   ├── cvsec24001_content.json
│   │   ├── cvsec24001_24001.json  # Subsection: Overview
│   │   ├── cvsec24001_24002.json
│   │   └── ...
│   ├── en/
│   └── ...
├── media/
│   ├── figures/
│   │   ├── cvfig24054.jpg
│   │   └── ...
│   ├── tables/
│   │   ├── cvtab24041.json
│   │   └── ...
│   └── videos/
│       └── ...
└── syllabus.db                    # SQLite with all relationships
```

---

## Example Output: Pericardial Disease
```json
{
  "subsection_id": "cvsec24009_24002",
  "title": "Clinical Presentation and Evaluation of Acute Pericarditis",
  "specialty": "cv",
  "section_id": "cvsec24009",
  "heading_sections": [
    {
      "heading": "Clinical Presentation and Evaluation of Acute Pericarditis",
      "heading_level": 3,
      "order": 1,
      "content": "Pericarditis is inflammation of the pericardium...",
      "embedded_questions": [
        "Diagnose acute pericarditis.",
        "Identify manifestations of pericarditis on ECG.",
        "Identify pericardial rub on auscultation."
      ],
      "media_references": [
        {
          "type": "table",
          "id": "cvtab24041",
          "title": "Causes of Pericardial Disease"
        },
        {
          "type": "video",
          "id": "cvvid24011",
          "title": "Pericarditis"
        },
        {
          "type": "figure",
          "id": "cvfig24054",
          "title": "ECG Changes of Acute Pericarditis"
        }
      ],
      "syllabus_crossreferences": [
        {
          "target_specialty": "fc",
          "target_section": "fcsec24004",
          "text": "Addressing Bias, Stigma, and Discrimination in Foundations..."
        }
      ]
    }
  ]
}
```

---

## Key Advantages

✅ **Hierarchical clarity**: Know exact position of any heading/content
✅ **Question mapping**: Instantly see which questions relate to which syllabus content
✅ **No link noise**: Only meaningful references extracted
✅ **Efficient media download**: Only download what's actually referenced
✅ **Semantic understanding**: Understand content structure before extraction
✅ **Searchable**: Query by heading, question, media type, specialty
✅ **Maintainable**: Each subsection is independent; updates don't cascade

---

## Execution Timeline (Refined)

| Phase | Operations | Time | Notes |
|-------|-----------|------|-------|
| 1: Outline | Navigate 573 subsections | 1-2 hrs | Light: just sidebar parsing |
| 2: Questions | Extract Q from 573 pages | 30 min | Already on pages from Phase 1 |
| 3: Content | Extract text from 573 pages | 2-3 hrs | ~50KB per page average |
| 4: Media | Download ~1000 items | 30 min | Parallel downloads, small files |
| **Total** | | **4-6 hours** | Single-threaded safe |

This approach transforms syllabus extraction from a "dump everything" problem into a **focused, relational data structure** that's actually useful for mapping back to questions and understanding the curriculum hierarchy.