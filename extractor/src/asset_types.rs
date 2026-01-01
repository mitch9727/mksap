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
    pub subspecialty: Option<String>,
    #[serde(skip_serializing_if = "Vec::is_empty", default)]
    pub figures: Vec<FigureReference>,
    #[serde(skip_serializing_if = "Vec::is_empty", default)]
    pub tables: Vec<TableReference>,
    #[serde(skip_serializing_if = "Vec::is_empty", default)]
    pub videos: Vec<VideoReference>,
    #[serde(skip_serializing_if = "Vec::is_empty", default)]
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
