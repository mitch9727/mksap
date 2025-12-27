use anyhow::{bail, Context, Result};
use serde::{Deserialize, Serialize};
use std::collections::{HashMap, HashSet};
use std::fs;
use std::path::{Path, PathBuf};

use super::asset_discovery::DiscoveryResults;

#[derive(Clone, Debug)]
pub struct QuestionEntry {
    pub question_id: String,
    pub question_dir: PathBuf,
    pub json_path: PathBuf,
}

#[derive(Debug, Default)]
pub struct MediaUpdate {
    pub tables: Vec<String>,
    pub images: Vec<String>,
    pub videos: Vec<String>,
    pub svgs: Vec<String>,
    pub metadata: MediaMetadata,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct MediaMetadata {
    pub figures: Vec<FigureMetadata>,
    pub tables: Vec<TableMetadata>,
    pub videos: Vec<VideoMetadata>,
    pub svgs: Vec<SvgMetadata>,
}

impl MediaMetadata {
    pub fn is_empty(&self) -> bool {
        self.figures.is_empty()
            && self.tables.is_empty()
            && self.videos.is_empty()
            && self.svgs.is_empty()
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FigureMetadata {
    pub figure_id: String,
    pub file: Option<String>,
    pub title: Option<String>,
    pub short_title: Option<String>,
    pub number: Option<String>,
    pub footnotes: Vec<String>,
    pub extension: Option<String>,
    pub width: Option<u32>,
    pub height: Option<u32>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TableMetadata {
    pub table_id: String,
    pub file: Option<String>,
    pub title: Option<String>,
    pub short_title: Option<String>,
    pub footnotes: Vec<String>,
    pub headers: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct VideoMetadata {
    pub video_id: String,
    pub file: Option<String>,
    pub title: Option<String>,
    pub short_title: Option<String>,
    pub width: Option<u32>,
    pub height: Option<u32>,
    pub caption: Option<String>,
    pub mp4_hash: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SvgMetadata {
    pub svg_id: String,
    pub file: Option<String>,
    pub title: Option<String>,
    pub caption: Option<String>,
}

pub fn collect_question_entries(data_dir: &str) -> Result<Vec<QuestionEntry>> {
    let root = ensure_data_dir(data_dir)?;
    let mut entries = Vec::new();

    for category_path in list_dirs(&root)? {
        for q_path in list_dirs(&category_path)? {
            if let Some(entry) = build_question_entry(q_path) {
                entries.push(entry);
            }
        }
    }

    Ok(entries)
}

pub fn collect_question_entry_map(data_dir: &str) -> Result<HashMap<String, QuestionEntry>> {
    let entries = collect_question_entries(data_dir)?;
    let mut entry_map = HashMap::new();
    for entry in entries {
        entry_map.insert(entry.question_id.clone(), entry);
    }
    Ok(entry_map)
}

pub fn select_targets(
    question_id: Option<&str>,
    available_ids: &HashSet<String>,
    source_label: &str,
) -> Result<Vec<String>> {
    let mut targets: Vec<String> = if let Some(qid) = question_id {
        if !available_ids.contains(qid) {
            bail!("Question ID not present in {}: {}", source_label, qid);
        }
        vec![qid.to_string()]
    } else {
        available_ids.iter().cloned().collect()
    };

    targets.sort();
    Ok(targets)
}

pub fn load_discovery_results(path: &Path) -> Result<HashSet<String>> {
    let results = DiscoveryResults::load_from_file(path)
        .with_context(|| format!("Failed to read discovery results from {}", path.display()))?;

    Ok(results.questions.keys().cloned().collect())
}

pub fn update_question_json(json_path: &Path, update: &MediaUpdate) -> Result<()> {
    let text = fs::read_to_string(json_path)
        .with_context(|| format!("Failed to read {}", json_path.display()))?;
    let mut value: serde_json::Value = serde_json::from_str(&text)
        .with_context(|| format!("Failed to parse {}", json_path.display()))?;

    let media = ensure_media_object(&mut value)?;
    insert_unique_strings(media, "tables", &update.tables);
    insert_unique_strings(media, "images", &update.images);
    insert_unique_strings(media, "videos", &update.videos);
    insert_unique_strings(media, "svgs", &update.svgs);

    if !update.metadata.is_empty() {
        merge_media_metadata(&mut value, &update.metadata)?;
    }

    let updated = serde_json::to_string_pretty(&value)?;
    fs::write(json_path, updated)
        .with_context(|| format!("Failed to write {}", json_path.display()))?;
    Ok(())
}

fn merge_media_metadata(value: &mut serde_json::Value, update: &MediaMetadata) -> Result<()> {
    let existing = value.get("media_metadata").cloned();
    let mut merged: MediaMetadata = existing
        .and_then(|val| serde_json::from_value(val).ok())
        .unwrap_or_default();

    for figure in &update.figures {
        upsert_figure_metadata(&mut merged.figures, figure.clone());
    }
    for table in &update.tables {
        upsert_table_metadata(&mut merged.tables, table.clone());
    }
    for video in &update.videos {
        upsert_video_metadata(&mut merged.videos, video.clone());
    }
    for svg in &update.svgs {
        upsert_svg_metadata(&mut merged.svgs, svg.clone());
    }

    value["media_metadata"] = serde_json::to_value(&merged)?;
    Ok(())
}

fn upsert_figure_metadata(target: &mut Vec<FigureMetadata>, item: FigureMetadata) {
    if let Some(existing) = target.iter_mut().find(|m| m.figure_id == item.figure_id) {
        merge_option(&mut existing.file, item.file);
        merge_option(&mut existing.title, item.title);
        merge_option(&mut existing.short_title, item.short_title);
        merge_option(&mut existing.number, item.number);
        merge_option(&mut existing.extension, item.extension);
        merge_option(&mut existing.width, item.width);
        merge_option(&mut existing.height, item.height);
        merge_vec_unique(&mut existing.footnotes, item.footnotes);
    } else {
        target.push(item);
    }
}

fn upsert_table_metadata(target: &mut Vec<TableMetadata>, item: TableMetadata) {
    if let Some(existing) = target.iter_mut().find(|m| m.table_id == item.table_id) {
        merge_option(&mut existing.file, item.file);
        merge_option(&mut existing.title, item.title);
        merge_option(&mut existing.short_title, item.short_title);
        merge_vec_unique(&mut existing.footnotes, item.footnotes);
        merge_vec_unique(&mut existing.headers, item.headers);
    } else {
        target.push(item);
    }
}

fn upsert_video_metadata(target: &mut Vec<VideoMetadata>, item: VideoMetadata) {
    if let Some(existing) = target.iter_mut().find(|m| m.video_id == item.video_id) {
        merge_option(&mut existing.file, item.file);
        merge_option(&mut existing.title, item.title);
        merge_option(&mut existing.short_title, item.short_title);
        merge_option(&mut existing.width, item.width);
        merge_option(&mut existing.height, item.height);
        merge_option(&mut existing.caption, item.caption);
        merge_option(&mut existing.mp4_hash, item.mp4_hash);
    } else {
        target.push(item);
    }
}

fn upsert_svg_metadata(target: &mut Vec<SvgMetadata>, item: SvgMetadata) {
    if let Some(existing) = target.iter_mut().find(|m| m.svg_id == item.svg_id) {
        merge_option(&mut existing.file, item.file);
        merge_option(&mut existing.title, item.title);
        merge_option(&mut existing.caption, item.caption);
    } else {
        target.push(item);
    }
}

fn merge_option<T>(target: &mut Option<T>, update: Option<T>) {
    if target.is_none() {
        *target = update;
    }
}

fn merge_vec_unique(target: &mut Vec<String>, update: Vec<String>) {
    if update.is_empty() {
        return;
    }
    let mut seen: HashSet<String> = target.iter().cloned().collect();
    for item in update {
        if seen.insert(item.clone()) {
            target.push(item);
        }
    }
}

fn ensure_data_dir(data_dir: &str) -> Result<PathBuf> {
    let root = PathBuf::from(data_dir);
    if root.exists() {
        return Ok(root);
    }
    bail!("Data directory not found: {}", data_dir)
}

fn list_dirs(path: &Path) -> Result<Vec<PathBuf>> {
    let mut dirs = Vec::new();
    for entry in fs::read_dir(path).context("Failed to read directory")? {
        let entry = entry.context("Failed to read directory entry")?;
        let entry_path = entry.path();
        if entry_path.is_dir() {
            dirs.push(entry_path);
        }
    }
    Ok(dirs)
}

fn build_question_entry(question_dir: PathBuf) -> Option<QuestionEntry> {
    let qid = question_dir.file_name()?.to_str()?.to_string();
    let json_path = question_dir.join(format!("{}.json", qid));
    if !json_path.exists() {
        return None;
    }
    Some(QuestionEntry {
        question_id: qid,
        question_dir,
        json_path,
    })
}

fn ensure_media_object(
    value: &mut serde_json::Value,
) -> Result<&mut serde_json::Map<String, serde_json::Value>> {
    if value.get("media").is_none() {
        value["media"] = serde_json::json!({
            "tables": [],
            "images": [],
            "svgs": [],
            "videos": []
        });
    }

    value
        .get_mut("media")
        .and_then(|v| v.as_object_mut())
        .context("Failed to access media object")
}

fn insert_unique_strings(
    media: &mut serde_json::Map<String, serde_json::Value>,
    key: &str,
    items: &[String],
) {
    let entry = media
        .entry(key.to_string())
        .or_insert_with(|| serde_json::Value::Array(Vec::new()));
    let serde_json::Value::Array(arr) = entry else {
        return;
    };
    let mut seen: std::collections::HashSet<String> = arr
        .iter()
        .filter_map(|v| v.as_str().map(|s| s.to_string()))
        .collect();
    for item in items {
        if seen.insert(item.clone()) {
            arr.push(serde_json::Value::String(item.clone()));
        }
    }
}
