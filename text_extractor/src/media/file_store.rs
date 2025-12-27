use anyhow::{bail, Context, Result};
use regex::Regex;
use serde::{Deserialize, Serialize};
use std::collections::HashSet;
use std::fs;
use std::path::{Path, PathBuf};

use super::discovery::DiscoveryResults;

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

pub fn load_discovery_results(path: &Path) -> Result<HashSet<String>> {
    let results = DiscoveryResults::load_from_file(path)
        .with_context(|| format!("Failed to read discovery results from {}", path.display()))?;

    Ok(results
        .questions_with_media
        .iter()
        .map(|q| q.question_id.clone())
        .collect())
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

pub fn backfill_inline_table_metadata(data_dir: &str) -> Result<usize> {
    let entries = collect_question_entries(data_dir)?;
    let mut added = 0usize;

    for entry in entries {
        let text = fs::read_to_string(&entry.json_path)
            .with_context(|| format!("Failed to read {}", entry.json_path.display()))?;
        let mut value: serde_json::Value = serde_json::from_str(&text)
            .with_context(|| format!("Failed to parse {}", entry.json_path.display()))?;

        let media_tables = value
            .get("media")
            .and_then(|media| media.get("tables"))
            .and_then(|tables| tables.as_array())
            .cloned()
            .unwrap_or_default();

        if media_tables.is_empty() {
            continue;
        }

        let mut merged: MediaMetadata = value
            .get("media_metadata")
            .cloned()
            .and_then(|val| serde_json::from_value(val).ok())
            .unwrap_or_default();
        let mut changed = false;

        for table in media_tables {
            let Some(table_str) = table.as_str() else {
                continue;
            };
            if !is_inline_table_path(table_str) {
                continue;
            }

            let filename = Path::new(table_str)
                .file_name()
                .and_then(|name| name.to_str())
                .unwrap_or("");
            if filename.is_empty() {
                continue;
            }

            let table_id = filename.trim_end_matches(".html").to_string();
            let path = entry.question_dir.join(table_str);
            if !path.exists() {
                continue;
            }

            let metadata = build_inline_table_metadata(&path, &table_id, table_str)?;
            let (was_added, was_updated) =
                upsert_inline_table_metadata(&mut merged.tables, metadata);
            if was_added {
                added += 1;
            }
            if was_added || was_updated {
                changed = true;
            }
        }

        if changed {
            value["media_metadata"] = serde_json::to_value(&merged)?;
            let updated = serde_json::to_string_pretty(&value)?;
            fs::write(&entry.json_path, updated)
                .with_context(|| format!("Failed to write {}", entry.json_path.display()))?;
        }
    }

    Ok(added)
}

fn upsert_inline_table_metadata(
    target: &mut Vec<TableMetadata>,
    item: TableMetadata,
) -> (bool, bool) {
    if let Some(existing) = target.iter_mut().find(|t| t.table_id == item.table_id) {
        let mut updated = false;
        if existing.file.is_none() {
            existing.file = item.file;
            updated = true;
        }
        if should_replace_text(existing.title.as_ref()) && item.title.is_some() {
            existing.title = item.title;
            updated = true;
        }
        if should_replace_vec(&existing.headers) && !item.headers.is_empty() {
            existing.headers = item.headers;
            updated = true;
        }
        if should_replace_vec(&existing.footnotes) && !item.footnotes.is_empty() {
            existing.footnotes = item.footnotes;
            updated = true;
        }
        return (false, updated);
    }

    target.push(item);
    (true, true)
}

fn should_replace_text(value: Option<&String>) -> bool {
    match value {
        None => true,
        Some(text) => text.trim().is_empty() || is_probably_html(text),
    }
}

fn should_replace_vec(values: &[String]) -> bool {
    if values.is_empty() {
        return true;
    }
    values.iter().any(|value| is_probably_html(value))
}

fn is_probably_html(text: &str) -> bool {
    text.contains('<') && text.contains('>')
}

fn build_inline_table_metadata(path: &Path, table_id: &str, file: &str) -> Result<TableMetadata> {
    let html =
        fs::read_to_string(path).with_context(|| format!("Failed to read {}", path.display()))?;
    let title = extract_caption_text(&html);
    let headers = extract_tag_texts(&html, "th");
    let footnotes = extract_inline_table_footnotes(&html);

    Ok(TableMetadata {
        table_id: table_id.to_string(),
        file: Some(file.to_string()),
        title,
        short_title: None,
        footnotes,
        headers,
    })
}

fn is_inline_table_path(path: &str) -> bool {
    let filename = Path::new(path)
        .file_name()
        .and_then(|name| name.to_str())
        .unwrap_or("");
    filename.starts_with("inline_table_") && filename.ends_with(".html")
}

fn extract_caption_text(html: &str) -> Option<String> {
    let raw = extract_raw_tag_html(html, "caption")?;
    let text = normalize_text_with_sup(&raw);
    if text.is_empty() {
        None
    } else {
        Some(text)
    }
}

fn extract_tag_texts(html: &str, tag: &str) -> Vec<String> {
    let re = Regex::new(&format!(r"(?s)<{tag}[^>]*>(.*?)</{tag}>")).unwrap();
    let mut seen = HashSet::new();
    let mut values = Vec::new();

    for cap in re.captures_iter(html) {
        let text = normalize_text_with_sup(cap.get(1).map(|m| m.as_str()).unwrap_or(""));
        if text.is_empty() {
            continue;
        }
        if seen.insert(text.clone()) {
            values.push(text);
        }
    }

    values
}

fn extract_inline_table_footnotes(html: &str) -> Vec<String> {
    let mut footnotes = Vec::new();
    let mut seen = HashSet::new();

    if let Some(tfoot_html) = extract_raw_tag_html(html, "tfoot") {
        for note in extract_tag_texts(&tfoot_html, "p") {
            push_unique_text(&mut footnotes, &mut seen, note);
        }
        for note in extract_tag_texts(&tfoot_html, "li") {
            push_unique_text(&mut footnotes, &mut seen, note);
        }
        if footnotes.is_empty() {
            let text = normalize_text_with_sup(&tfoot_html);
            if !text.is_empty() {
                push_unique_text(&mut footnotes, &mut seen, text);
            }
        }
    }

    for note in extract_classed_footnotes(html) {
        push_unique_text(&mut footnotes, &mut seen, note);
    }

    for note in extract_sup_prefixed_footnotes(html) {
        push_unique_text(&mut footnotes, &mut seen, note);
    }

    footnotes
}

fn extract_raw_tag_html(html: &str, tag: &str) -> Option<String> {
    let re = Regex::new(&format!(r"(?s)<{tag}[^>]*>(.*?)</{tag}>")).unwrap();
    re.captures(html)
        .and_then(|cap| cap.get(1))
        .map(|m| m.as_str().to_string())
}

fn strip_html_tags(html: &str) -> String {
    let re = Regex::new(r"(?s)<[^>]*>").unwrap();
    re.replace_all(html, "").to_string()
}

fn normalize_text_with_sup(text: &str) -> String {
    let with_sup = replace_superscripts(text);
    normalize_text(&with_sup)
}

fn normalize_text(text: &str) -> String {
    let stripped = strip_html_tags(text);
    decode_html_entities(&stripped)
        .split_whitespace()
        .collect::<Vec<_>>()
        .join(" ")
}

fn replace_superscripts(html: &str) -> String {
    let re = Regex::new(r"(?s)<sup[^>]*>(.*?)</sup>").unwrap();
    re.replace_all(html, |caps: &regex::Captures| {
        let inner = caps.get(1).map(|m| m.as_str()).unwrap_or("");
        let text = normalize_text(inner);
        if text.is_empty() {
            String::new()
        } else {
            format!("[{}]", text)
        }
    })
    .to_string()
}

fn extract_classed_footnotes(html: &str) -> Vec<String> {
    let re = Regex::new(
        r#"(?is)<(?:p|div|span|td|tr)[^>]*(?:class|className)=['"][^'"]*(footnote|note)[^'"]*['"][^>]*>(.*?)</(?:p|div|span|td|tr)>"#,
    )
    .unwrap();
    let mut notes = Vec::new();
    let mut seen = HashSet::new();

    for cap in re.captures_iter(html) {
        let text = normalize_text_with_sup(cap.get(2).map(|m| m.as_str()).unwrap_or(""));
        if text.is_empty() {
            continue;
        }
        if seen.insert(text.clone()) {
            notes.push(text);
        }
    }

    notes
}

fn extract_sup_prefixed_footnotes(html: &str) -> Vec<String> {
    let re = Regex::new(r"(?is)<(?:p|li)[^>]*>\s*(<sup[^>]*>.*?</sup>\s*.*?)</(?:p|li)>").unwrap();
    let mut notes = Vec::new();
    let mut seen = HashSet::new();

    for cap in re.captures_iter(html) {
        let text = normalize_text_with_sup(cap.get(1).map(|m| m.as_str()).unwrap_or(""));
        if text.is_empty() {
            continue;
        }
        if seen.insert(text.clone()) {
            notes.push(text);
        }
    }

    notes
}

fn push_unique_text(target: &mut Vec<String>, seen: &mut HashSet<String>, value: String) {
    if value.is_empty() {
        return;
    }
    if seen.insert(value.clone()) {
        target.push(value);
    }
}

fn decode_html_entities(text: &str) -> String {
    text.replace("&nbsp;", " ")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&quot;", "\"")
        .replace("&#39;", "'")
        .replace("&amp;", "&")
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
