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
