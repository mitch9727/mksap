use anyhow::{Context, Result};
use regex::Regex;
use std::fs;
use std::path::Path;
use tracing::{error, info, warn};

use crate::config;
use crate::models::QuestionData;

#[derive(Debug, Default)]
pub struct StandardizationStats {
    pub total_files: usize,
    pub files_reordered: usize,
    pub files_whitespace_compacted: usize,
    pub files_unchanged: usize,
    pub media_validated: usize,
    pub media_missing: Vec<String>,
    pub errors: Vec<(String, String)>,
}

pub async fn run_standardization(
    output_dir: &str,
    dry_run: bool,
    system_filter: Option<&str>,
) -> Result<()> {
    let mut stats = StandardizationStats::default();

    // Load all organ systems from config
    let systems = config::init_organ_systems();

    if dry_run {
        info!("DRY RUN MODE: No files will be modified\n");
    }

    if let Some(filter) = system_filter {
        info!("Processing only system: {}\n", filter);
    }

    for system in systems {
        // Apply filter if provided
        if let Some(filter) = system_filter {
            if system.id != filter {
                continue;
            }
        }

        let system_dir = Path::new(output_dir).join(&system.id);
        if !system_dir.exists() {
            continue;
        }

        info!("Processing system: {} ({})", system.id, system.name);

        // Process all question directories
        let entries = match fs::read_dir(&system_dir) {
            Ok(entries) => entries,
            Err(e) => {
                error!("Failed to read system directory {}: {}", system.id, e);
                continue;
            }
        };

        for entry in entries {
            let entry = match entry {
                Ok(e) => e,
                Err(e) => {
                    warn!("Failed to read directory entry: {}", e);
                    continue;
                }
            };

            let question_dir = entry.path();
            if !question_dir.is_dir() {
                continue;
            }

            let question_id = question_dir
                .file_name()
                .and_then(|n| n.to_str())
                .unwrap_or_default();

            let json_path = question_dir.join(format!("{}.json", question_id));

            if !json_path.exists() {
                warn!("Missing JSON file for: {}", question_id);
                continue;
            }

            match process_question_json(&json_path, &question_dir, dry_run, &mut stats) {
                Ok(_) => stats.total_files += 1,
                Err(e) => {
                    stats.errors.push((question_id.to_string(), e.to_string()));
                    error!("Error processing {}: {}", question_id, e);
                }
            }
        }
    }

    print_standardization_report(&stats, dry_run);
    Ok(())
}

fn process_question_json(
    json_path: &Path,
    question_dir: &Path,
    dry_run: bool,
    stats: &mut StandardizationStats,
) -> Result<()> {
    // 1. Read original JSON
    let original_content = fs::read_to_string(json_path)
        .with_context(|| format!("Failed to read JSON file: {:?}", json_path))?;

    // 2. Deserialize into QuestionData struct
    let mut question: QuestionData = serde_json::from_str(&original_content)
        .with_context(|| format!("Failed to parse JSON file: {:?}", json_path))?;

    // 3. Compact whitespace in HTML fields
    let whitespace_changed = compact_whitespace(&mut question);
    if whitespace_changed {
        stats.files_whitespace_compacted += 1;
    }

    // 4. Validate media file existence
    validate_media_files(&question, question_dir, stats)?;

    // 5. Re-serialize (automatically uses current struct field order)
    let standardized_content = serde_json::to_string_pretty(&question)
        .context("Failed to serialize standardized JSON")?;

    // 6. Detect if field order changed
    let ordering_changed = !fields_match_order(&original_content, &standardized_content);
    if ordering_changed {
        stats.files_reordered += 1;
    }

    // 7. Write if changed (atomic write to prevent corruption)
    if (ordering_changed || whitespace_changed) && !dry_run {
        atomic_write(json_path, &standardized_content)?;
    } else if !ordering_changed && !whitespace_changed {
        stats.files_unchanged += 1;
    }

    Ok(())
}

fn compact_whitespace(question: &mut QuestionData) -> bool {
    let mut changed = false;

    // Compact question_text
    let compacted = compact_html_whitespace(&question.question_text);
    if compacted != question.question_text {
        question.question_text = compacted;
        changed = true;
    }

    // Compact critique
    let compacted = compact_html_whitespace(&question.critique);
    if compacted != question.critique {
        question.critique = compacted;
        changed = true;
    }

    // Compact key_points array
    for point in &mut question.key_points {
        let compacted = compact_html_whitespace(point);
        if compacted != *point {
            *point = compacted;
            changed = true;
        }
    }

    changed
}

fn compact_html_whitespace(html: &str) -> String {
    // Replace 2+ consecutive whitespace chars with single space
    let re = Regex::new(r"\s{2,}").unwrap();
    let compacted = re.replace_all(html, " ");

    compacted.trim().to_string()
}

fn validate_media_files(
    question: &QuestionData,
    question_dir: &Path,
    stats: &mut StandardizationStats,
) -> Result<()> {
    let media = &question.media;

    // Check all media types
    for path in &media.tables {
        check_media_file(question_dir, path, &question.question_id, stats)?;
    }
    for path in &media.images {
        check_media_file(question_dir, path, &question.question_id, stats)?;
    }
    for path in &media.svgs {
        check_media_file(question_dir, path, &question.question_id, stats)?;
    }
    for path in &media.videos {
        check_media_file(question_dir, path, &question.question_id, stats)?;
    }

    Ok(())
}

fn check_media_file(
    question_dir: &Path,
    relative_path: &str,
    question_id: &str,
    stats: &mut StandardizationStats,
) -> Result<()> {
    let full_path = question_dir.join(relative_path);

    if full_path.exists() {
        stats.media_validated += 1;
    } else {
        warn!("Missing media: {} ({})", relative_path, question_id);
        stats
            .media_missing
            .push(format!("{}: {}", question_id, relative_path));
    }

    Ok(())
}

fn atomic_write(target_path: &Path, content: &str) -> Result<()> {
    let temp_path = target_path.with_extension("json.tmp");

    // Write to temp file
    fs::write(&temp_path, content).context("Failed to write temp file")?;

    // Validate temp file is valid JSON
    let validation = fs::read_to_string(&temp_path).context("Failed to read temp file")?;
    serde_json::from_str::<serde_json::Value>(&validation)
        .context("Temp file validation failed - invalid JSON")?;

    // Atomic rename (original untouched until this point)
    fs::rename(&temp_path, target_path).context("Failed to rename temp file to target")?;

    Ok(())
}

fn fields_match_order(json1: &str, json2: &str) -> bool {
    // Compare first 500 characters (where field order differences appear)
    // Use char_indices to ensure we don't slice at invalid UTF-8 boundaries
    let prefix1 = json1
        .char_indices()
        .nth(500)
        .map(|(idx, _)| &json1[..idx])
        .unwrap_or(json1);

    let prefix2 = json2
        .char_indices()
        .nth(500)
        .map(|(idx, _)| &json2[..idx])
        .unwrap_or(json2);

    prefix1 == prefix2
}

fn print_standardization_report(stats: &StandardizationStats, dry_run: bool) {
    info!("\n=== STANDARDIZATION REPORT ===");
    info!("Total files processed: {}", stats.total_files);
    info!("Files with reordered fields: {}", stats.files_reordered);
    info!(
        "Files with compacted whitespace: {}",
        stats.files_whitespace_compacted
    );
    info!("Files unchanged: {}", stats.files_unchanged);
    info!("Media files validated: {}", stats.media_validated);
    info!("Media files missing: {}", stats.media_missing.len());
    info!("Errors: {}", stats.errors.len());

    if !stats.media_missing.is_empty() {
        warn!("\n=== MISSING MEDIA FILES ===");
        for missing in &stats.media_missing {
            warn!("  {}", missing);
        }
    }

    if !stats.errors.is_empty() {
        error!("\n=== ERRORS ===");
        for (file, err) in &stats.errors {
            error!("  {}: {}", file, err);
        }
    }

    if dry_run {
        info!("\nDRY RUN: No files modified");
    } else {
        info!("\nStandardization complete!");
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_compact_whitespace_basic() {
        let input = "The   patient  has\n\n  multiple\t\tcomorbidities.";
        let expected = "The patient has multiple comorbidities.";
        assert_eq!(compact_html_whitespace(input), expected);
    }

    #[test]
    fn test_compact_whitespace_preserves_tags() {
        let input = "<p>Some  text</p>  <strong>Bold</strong>";
        let expected = "<p>Some text</p> <strong>Bold</strong>";
        assert_eq!(compact_html_whitespace(input), expected);
    }

    #[test]
    fn test_fields_match_order_same() {
        let json1 = r#"{"question_id": "test", "category": "cv"}"#;
        let json2 = r#"{"question_id": "test", "category": "cv"}"#;
        assert!(fields_match_order(json1, json2));
    }

    #[test]
    fn test_fields_match_order_different() {
        let json1 = r#"{"question_id": "test", "category": "cv"}"#;
        let json2 = r#"{"category": "cv", "question_id": "test"}"#;
        assert!(!fields_match_order(json1, json2));
    }

    #[test]
    fn test_fields_match_order_empty() {
        let json1 = "";
        let json2 = "";
        assert!(fields_match_order(json1, json2));
    }
}
