use anyhow::{bail, Context, Result};
use std::collections::HashSet;
use std::fs;
use std::path::{Path, PathBuf};

use crate::discovery::DiscoveryResults;
use crate::model::QuestionEntry;
use crate::render::pretty_format_html;

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

pub fn select_targets(
    entries: &[QuestionEntry],
    question_id: Option<&str>,
    all: bool,
) -> Result<Vec<QuestionEntry>> {
    if all || question_id.is_none() {
        return Ok(entries.to_vec());
    }

    let qid = question_id.unwrap();
    let matches: Vec<QuestionEntry> = entries
        .iter()
        .filter(|entry| entry.question_id == qid)
        .cloned()
        .collect();

    if matches.is_empty() {
        bail!("Question ID not found in data directory: {}", qid);
    }

    Ok(matches)
}

pub fn load_discovery_results(path: &Path) -> Result<HashSet<String>> {
    let json = fs::read_to_string(path)
        .with_context(|| format!("Failed to read discovery results from {}", path.display()))?;

    let results: DiscoveryResults = serde_json::from_str(&json)
        .with_context(|| format!("Failed to parse discovery results from {}", path.display()))?;

    // Extract internal IDs from discovery results
    let ids: HashSet<String> = results
        .questions_with_media
        .iter()
        .map(|q| q.question_id.clone())
        .collect();

    Ok(ids)
}

pub fn update_question_json(json_path: &Path, update: &crate::model::MediaUpdate) -> Result<()> {
    let text = fs::read_to_string(json_path)
        .with_context(|| format!("Failed to read {}", json_path.display()))?;
    let mut value: serde_json::Value = serde_json::from_str(&text)
        .with_context(|| format!("Failed to parse {}", json_path.display()))?;

    let media = ensure_media_object(&mut value)?;
    insert_unique_strings(media, "tables", &update.tables);
    insert_unique_strings(media, "images", &update.images);
    insert_unique_strings(media, "videos", &update.videos);
    insert_unique_strings(media, "svgs", &update.svgs);

    let updated = serde_json::to_string_pretty(&value)?;
    fs::write(json_path, updated)
        .with_context(|| format!("Failed to write {}", json_path.display()))?;
    Ok(())
}

pub fn format_existing_tables(data_dir: &str) -> Result<usize> {
    let root = ensure_data_dir(data_dir)?;
    let mut files = Vec::new();
    collect_table_files(&root, &mut files)?;

    let mut formatted = 0usize;
    for path in files {
        let content = fs::read_to_string(&path)?;
        let pretty = pretty_format_html(&content);
        if content != pretty {
            fs::write(&path, pretty)?;
            formatted += 1;
        }
    }

    Ok(formatted)
}

fn ensure_data_dir(data_dir: &str) -> Result<PathBuf> {
    let root = PathBuf::from(data_dir);
    if root.exists() {
        return Ok(root);
    }
    bail!("Data directory not found: {}", data_dir)
}

fn collect_table_files(root: &Path, files: &mut Vec<PathBuf>) -> Result<()> {
    for entry in fs::read_dir(root).context("Failed to read directory")? {
        let entry = entry.context("Failed to read directory entry")?;
        let path = entry.path();
        if path.is_dir() {
            collect_table_files(&path, files)?;
            continue;
        }

        if path.extension().and_then(|s| s.to_str()) != Some("html") {
            continue;
        }

        if let Some(parent) = path.parent() {
            if parent.file_name().and_then(|s| s.to_str()) == Some("tables") {
                files.push(path);
            }
        }
    }
    Ok(())
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
