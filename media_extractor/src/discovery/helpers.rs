use serde_json::Value;
use std::collections::{HashMap, HashSet};

use super::types::{FigureReference, MediaType, SvgReference, SvgSource, TableReference, VideoReference};

// ============================================================================
// Content ID Extraction
// ============================================================================

/// Extract all content IDs from a question's JSON structure
pub fn extract_content_ids(question: &Value) -> Vec<String> {
    let mut ids = Vec::new();
    let mut seen = HashSet::new();
    walk_for_content_ids(question, &mut ids, &mut seen);
    ids
}

fn walk_for_content_ids(value: &Value, ids: &mut Vec<String>, seen: &mut HashSet<String>) {
    match value {
        Value::Object(map) => {
            if let Some(Value::Array(content_ids)) = map.get("contentIds") {
                for id in content_ids {
                    if let Some(id_str) = id.as_str() {
                        if seen.insert(id_str.to_string()) {
                            ids.push(id_str.to_string());
                        }
                    }
                }
            }

            for v in map.values() {
                walk_for_content_ids(v, ids, seen);
            }
        }
        Value::Array(items) => {
            for item in items {
                walk_for_content_ids(item, ids, seen);
            }
        }
        _ => {}
    }
}

// ============================================================================
// Metadata Index Builders
// ============================================================================

/// Build figure lookup index from metadata
pub fn build_figures_index(metadata: &Value) -> HashMap<String, Vec<FigureReference>> {
    let mut figures_by_location: HashMap<String, Vec<FigureReference>> = HashMap::new();

    if let Some(figures) = metadata.get("figures").and_then(|f| f.as_object()) {
        for figure in figures.values() {
            if let Some(canonical_location) = figure.get("canonicalLocation").and_then(|v| v.as_str()) {
                if let Some(figure_id) = figure.get("id").and_then(|v| v.as_str()) {
                    let fig_ref = extract_figure_reference(figure_id, figure);

                    figures_by_location
                        .entry(canonical_location.to_string())
                        .or_insert_with(Vec::new)
                        .push(fig_ref);
                }
            }
        }
    }

    figures_by_location
}

fn extract_figure_reference(figure_id: &str, figure: &Value) -> FigureReference {
    let extension = figure
        .get("imageInfo")
        .and_then(|i| i.get("extension"))
        .and_then(|e| e.as_str())
        .unwrap_or("unknown")
        .to_string();

    let title = figure
        .get("title")
        .and_then(|t| t.as_str())
        .map(String::from);

    let width = figure
        .get("imageInfo")
        .and_then(|i| i.get("width"))
        .and_then(|w| w.as_u64())
        .unwrap_or(0) as u32;

    let height = figure
        .get("imageInfo")
        .and_then(|i| i.get("height"))
        .and_then(|h| h.as_u64())
        .unwrap_or(0) as u32;

    FigureReference {
        figure_id: figure_id.to_string(),
        extension,
        title,
        width,
        height,
    }
}

/// Build video lookup index from metadata
pub fn build_videos_index(metadata: &Value) -> HashMap<String, Vec<VideoReference>> {
    let mut videos_by_location: HashMap<String, Vec<VideoReference>> = HashMap::new();

    if let Some(videos) = metadata.get("videos").and_then(|v| v.as_object()) {
        for video in videos.values() {
            if let Some(canonical_location) = video.get("canonicalLocation").and_then(|v| v.as_str()) {
                if let Some(video_id) = video.get("id").and_then(|v| v.as_str()) {
                    let title = video
                        .get("title")
                        .and_then(|t| t.as_str())
                        .map(String::from);

                    videos_by_location
                        .entry(canonical_location.to_string())
                        .or_insert_with(Vec::new)
                        .push(VideoReference {
                            video_id: video_id.to_string(),
                            title,
                            canonical_location: canonical_location.to_string(),
                        });
                }
            }
        }
    }

    videos_by_location
}

// ============================================================================
// Media Categorization
// ============================================================================

pub struct CategorizedMedia {
    pub figures: Vec<FigureReference>,
    pub tables: Vec<TableReference>,
    pub svgs: Vec<SvgReference>,
}

/// Categorize content IDs and lookup associated media
pub fn categorize_content_ids(
    content_ids: Vec<String>,
    figures_by_location: &HashMap<String, Vec<FigureReference>>,
    related_section: &str,
) -> CategorizedMedia {
    let mut figures = Vec::new();
    let mut tables = Vec::new();
    let mut svgs = Vec::new();
    let mut seen_figures = HashSet::new();
    let mut seen_tables = HashSet::new();
    let mut seen_svgs = HashSet::new();

    for content_id in content_ids {
        match MediaType::from_content_id(&content_id) {
            MediaType::Figure => {
                if seen_figures.insert(content_id.clone()) {
                    if let Some(fig_refs) = figures_by_location.get(related_section) {
                        for fig in fig_refs {
                            if fig.figure_id == content_id {
                                figures.push(fig.clone());
                                break;
                            }
                        }
                    }
                }
            }
            MediaType::Table => {
                if seen_tables.insert(content_id.clone()) {
                    tables.push(TableReference {
                        table_id: content_id,
                        title: None,
                    });
                }
            }
            MediaType::Svg => {
                if seen_svgs.insert(content_id.clone()) {
                    svgs.push(SvgReference {
                        svg_id: content_id.clone(),
                        source: SvgSource::ContentId(content_id),
                    });
                }
            }
            MediaType::Video => {
                // Videos handled separately via canonical location
            }
        }
    }

    CategorizedMedia {
        figures,
        tables,
        svgs,
    }
}

// ============================================================================
// Metadata Extraction Helpers
// ============================================================================

pub fn extract_subspecialty(question_meta: &Value) -> Option<String> {
    question_meta
        .get("subspecialtyId")
        .and_then(|v| v.as_str())
        .map(String::from)
}

pub fn extract_product_type(question_meta: &Value) -> Option<String> {
    question_meta
        .get("tags")
        .and_then(|v| v.as_array())?
        .iter()
        .find_map(|tag| {
            if tag.get("type").and_then(|t| t.as_str())? == "product" {
                tag.get("value").and_then(|v| v.as_str()).map(String::from)
            } else {
                None
            }
        })
}

pub fn extract_related_section(question_meta: &Value) -> &str {
    question_meta
        .get("relatedSection")
        .and_then(|v| v.as_str())
        .unwrap_or("")
}

pub fn is_invalidated(question_meta: &Value) -> bool {
    question_meta
        .get("invalidated")
        .and_then(|v| v.as_bool())
        .unwrap_or(false)
}
