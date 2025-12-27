use serde::{Deserialize, Serialize};

// ============================================================================
// Core Media Reference Types
// ============================================================================

#[derive(Debug, Clone, Serialize, Deserialize, Eq, PartialEq, Hash)]
pub struct FigureReference {
    pub figure_id: String,
    pub extension: String, // "svg", "jpg", "png"
    pub title: Option<String>,
    pub width: u32,
    pub height: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize, Eq, PartialEq, Hash)]
pub struct TableReference {
    pub table_id: String,
    pub title: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, Eq, PartialEq, Hash)]
pub struct VideoReference {
    pub video_id: String,
    pub title: Option<String>,
    pub canonical_location: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, Eq, PartialEq, Hash)]
pub struct SvgReference {
    pub svg_id: String,
    pub source: SvgSource,
}

#[derive(Debug, Clone, Serialize, Deserialize, Eq, PartialEq, Hash)]
pub enum SvgSource {
    ContentId(String),
    Inline,
}

// ============================================================================
// Question Media Container
// ============================================================================

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct QuestionMedia {
    pub question_id: String,
    pub array_id: Option<u32>,
    pub subspecialty: Option<String>,
    pub product_type: Option<String>,
    pub figures: Vec<FigureReference>,
    pub tables: Vec<TableReference>,
    pub videos: Vec<VideoReference>,
    pub svgs: Vec<SvgReference>,
}

impl QuestionMedia {
    pub fn has_media(&self) -> bool {
        !self.figures.is_empty()
            || !self.tables.is_empty()
            || !self.videos.is_empty()
            || !self.svgs.is_empty()
    }

    pub fn media_type_count(&self) -> u32 {
        let mut count = 0;
        if !self.figures.is_empty() {
            count += 1;
        }
        if !self.tables.is_empty() {
            count += 1;
        }
        if !self.videos.is_empty() {
            count += 1;
        }
        if !self.svgs.is_empty() {
            count += 1;
        }
        count
    }
}

// ============================================================================
// Media Type Categorization
// ============================================================================

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum MediaType {
    Figure,
    Table,
    Video,
    Svg,
}

impl MediaType {
    /// Categorize a content ID based on its prefix pattern
    pub fn from_content_id(content_id: &str) -> Self {
        let lower = content_id.to_ascii_lowercase();

        if lower.starts_with("fig") || lower.get(2..).map_or(false, |tail| tail.starts_with("fig"))
        {
            MediaType::Figure
        } else if lower.starts_with("tab")
            || lower.get(2..).map_or(false, |tail| tail.starts_with("tab"))
        {
            MediaType::Table
        } else if lower.starts_with("vid")
            || lower.get(2..).map_or(false, |tail| tail.starts_with("vid"))
        {
            MediaType::Video
        } else if lower.starts_with("svg")
            || lower.get(2..).map_or(false, |tail| tail.starts_with("svg"))
        {
            MediaType::Svg
        } else {
            MediaType::Figure // Default fallback
        }
    }
}
