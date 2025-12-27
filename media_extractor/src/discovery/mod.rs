// Submodules
mod helpers;
mod scanner;
mod statistics;
mod types;

// Re-exports
pub use scanner::MediaDiscovery;
pub use statistics::DiscoveryStatistics;
pub use types::{
    FigureReference, MediaType, QuestionMedia, SvgReference, SvgSource, TableReference,
    VideoReference,
};

use anyhow::{Context, Result};
use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::fs;
use std::path::{Path, PathBuf};
use tracing::{info, warn};

// ============================================================================
// Discovery Configuration
// ============================================================================

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DiscoveryConfig {
    pub concurrent_requests: usize,
    pub base_url: String,
}

// ============================================================================
// Discovery Results Container
// ============================================================================

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DiscoveryResults {
    pub questions_with_media: Vec<QuestionMedia>,
    pub statistics: DiscoveryStatistics,
    pub timestamp: String,
    pub config: DiscoveryConfig,
}

impl DiscoveryResults {
    pub(crate) fn new(
        questions_with_media: Vec<QuestionMedia>,
        statistics: DiscoveryStatistics,
        base_url: String,
        concurrent_requests: usize,
    ) -> Self {
        Self {
            questions_with_media,
            statistics,
            timestamp: chrono::Utc::now().to_rfc3339(),
            config: DiscoveryConfig {
                concurrent_requests,
                base_url,
            },
        }
    }

    /// Generate human-readable text report
    pub fn generate_report(&self) -> String {
        self.statistics.generate_report(&self.timestamp)
    }

    /// Save to JSON file
    pub fn save_to_file(&self, path: &Path) -> Result<()> {
        let json = serde_json::to_string_pretty(self)?;
        std::fs::write(path, json)?;
        Ok(())
    }

    /// Load from JSON file
    pub fn load_from_file(path: &Path) -> Result<Self> {
        let json = std::fs::read_to_string(path)?;
        Ok(serde_json::from_str(&json)?)
    }
}

// ============================================================================
// API-Based Discovery with Inverse Logic
// ============================================================================

use reqwest::Client;
use std::collections::HashSet;
use std::sync::Arc;
use tokio::sync::Semaphore;

/// Discover questions with media using inverse logic:
/// 1. Load all discovered question IDs from text_extractor checkpoints
/// 2. Check each question via API to see if it contains ONLY text
/// 3. Questions that aren't text-only = questions with media
pub async fn discover_media_questions(
    client: &Client,
    base_url: &str,
    concurrent_limit: usize,
) -> Result<DiscoveryResults> {
    info!("Step 1: Loading all discovered question IDs from checkpoints...");

    let all_question_ids = load_all_question_ids_from_checkpoints()?;
    info!("Loaded {} total question IDs", all_question_ids.len());

    info!("Step 2: Checking each question via API to identify text-only questions...");

    let text_only_ids = find_text_only_questions(
        client,
        base_url,
        &all_question_ids,
        concurrent_limit,
    )
    .await?;

    info!("Found {} text-only questions", text_only_ids.len());

    info!("Step 3: Computing media questions (inverse logic)...");

    let media_question_ids: HashSet<String> = all_question_ids
        .iter()
        .filter(|id| !text_only_ids.contains(*id))
        .cloned()
        .collect();

    info!("Found {} questions with media", media_question_ids.len());

    // Convert to QuestionMedia format for reporting
    let mut questions_with_media = Vec::new();
    let mut stats = DiscoveryStatistics::default();

    for question_id in &media_question_ids {
        let system_code = extract_system_code(question_id);

        let media = QuestionMedia {
            question_id: question_id.clone(),
            array_id: None,
            subspecialty: Some(system_code.to_string()),
            product_type: None,
            figures: vec![], // Details not known from inverse logic
            tables: vec![],
            videos: vec![],
            svgs: vec![],
        };

        stats.update_with_question(&media);
        questions_with_media.push(media);
    }

    stats.total_questions_scanned = all_question_ids.len();
    stats.total_questions_with_media = media_question_ids.len();
    stats.total_questions_without_media = text_only_ids.len();
    stats.percentage_with_media = if stats.total_questions_scanned > 0 {
        (stats.total_questions_with_media as f64 / stats.total_questions_scanned as f64) * 100.0
    } else {
        0.0
    };

    Ok(DiscoveryResults::new(
        questions_with_media,
        stats,
        base_url.to_string(),
        concurrent_limit,
    ))
}

/// Load all question IDs from text_extractor checkpoint files
fn load_all_question_ids_from_checkpoints() -> Result<HashSet<String>> {
    let checkpoint_dir = Path::new("../mksap_data/.checkpoints");

    if !checkpoint_dir.exists() {
        anyhow::bail!(
            "Checkpoint directory not found: {}. Run text_extractor first to discover questions.",
            checkpoint_dir.display()
        );
    }

    let mut all_ids = HashSet::new();

    for entry in fs::read_dir(checkpoint_dir).context("Failed to read checkpoint directory")? {
        let entry = entry?;
        let path = entry.path();

        // Only process files like "cv_ids.txt", "en_ids.txt", etc.
        if !path.is_file() || !path.to_string_lossy().ends_with("_ids.txt") {
            continue;
        }

        let content = fs::read_to_string(&path)
            .with_context(|| format!("Failed to read checkpoint: {}", path.display()))?;

        for line in content.lines() {
            let id = line.trim();
            if !id.is_empty() {
                all_ids.insert(id.to_string());
            }
        }
    }

    Ok(all_ids)
}

/// Check questions via API to find which are text-only
async fn find_text_only_questions(
    client: &Client,
    base_url: &str,
    question_ids: &HashSet<String>,
    concurrent_limit: usize,
) -> Result<HashSet<String>> {
    let semaphore = Arc::new(Semaphore::new(concurrent_limit));
    let mut handles = vec![];

    for question_id in question_ids {
        let client = client.clone();
        let base_url = base_url.to_string();
        let question_id_clone = question_id.clone();
        let sem = semaphore.clone();

        let handle = tokio::spawn(async move {
            let _permit = sem.acquire().await.unwrap();
            is_text_only_question(&client, &base_url, &question_id_clone).await
        });

        handles.push((question_id.clone(), handle));
    }

    let mut text_only_ids = HashSet::new();
    let mut checked = 0;
    let total = handles.len();

    for (question_id, handle) in handles {
        match handle.await {
            Ok(Ok(true)) => {
                text_only_ids.insert(question_id);
            }
            Ok(Ok(false)) => {
                // Has media, skip
            }
            Ok(Err(e)) => {
                warn!("Failed to check {}: {}", question_id, e);
            }
            Err(e) => {
                warn!("Task failed for {}: {}", question_id, e);
            }
        }

        checked += 1;
        if checked % 100 == 0 {
            info!("Progress: {}/{} questions checked", checked, total);
        }
    }

    info!("Completed checking all {} questions", total);
    Ok(text_only_ids)
}

/// Check if a specific question is text-only (no media)
async fn is_text_only_question(
    client: &Client,
    base_url: &str,
    question_id: &str,
) -> Result<bool> {
    let url = format!("{}/api/questions/{}.json", base_url, question_id);

    let response = client
        .get(&url)
        .send()
        .await
        .context("Failed to send request")?;

    if !response.status().is_success() {
        anyhow::bail!("HTTP {}: {}", response.status(), question_id);
    }

    let json: Value = response.json().await.context("Failed to parse JSON")?;

    // Check if media field exists and is empty
    let is_text_only = if let Some(media) = json.get("media").and_then(|m| m.as_object()) {
        // A question is text-only if ALL media arrays are empty
        let images_empty = media
            .get("images")
            .and_then(|i| i.as_array())
            .map(|arr| arr.is_empty())
            .unwrap_or(true);

        let tables_empty = media
            .get("tables")
            .and_then(|t| t.as_array())
            .map(|arr| arr.is_empty())
            .unwrap_or(true);

        let videos_empty = media
            .get("videos")
            .and_then(|v| v.as_array())
            .map(|arr| arr.is_empty())
            .unwrap_or(true);

        let svgs_empty = media
            .get("svgs")
            .and_then(|s| s.as_array())
            .map(|arr| arr.is_empty())
            .unwrap_or(true);

        images_empty && tables_empty && videos_empty && svgs_empty
    } else {
        // No media field = text-only
        true
    };

    Ok(is_text_only)
}

/// Extract system code from question ID (e.g., "cvmcq24001" -> "cv")
fn extract_system_code(question_id: &str) -> &str {
    if question_id.len() >= 2 {
        &question_id[0..2]
    } else {
        "unknown"
    }
}

// ============================================================================
// Local File Scanning (LEGACY - kept for reference)
// ============================================================================

/// Scan local mksap_data directory for questions with media
#[allow(dead_code)]
pub async fn scan_local_questions(data_dir: &Path) -> Result<DiscoveryResults> {
    info!("Scanning local question files in: {}", data_dir.display());

    let mut questions_with_media = Vec::new();
    let mut stats = DiscoveryStatistics::default();

    // Iterate through system code directories (cv, en, fc, etc.)
    for entry in fs::read_dir(data_dir).context("Failed to read data directory")? {
        let entry = entry?;
        let path = entry.path();

        if !path.is_dir() {
            continue;
        }

        let system_code = path
            .file_name()
            .and_then(|n| n.to_str())
            .unwrap_or("unknown");

        // Skip hidden directories and checkpoints
        if system_code.starts_with('.') {
            continue;
        }

        info!("Scanning system code: {}", system_code);

        // Scan questions within this system
        scan_system_directory(&path, &mut questions_with_media, &mut stats, system_code).await?;
    }

    info!("Scan complete! Found {} questions with media", questions_with_media.len());

    Ok(DiscoveryResults::new(
        questions_with_media,
        stats,
        "local".to_string(),
        0,
    ))
}

async fn scan_system_directory(
    system_dir: &Path,
    questions_with_media: &mut Vec<QuestionMedia>,
    stats: &mut DiscoveryStatistics,
    system_code: &str,
) -> Result<()> {
    for entry in fs::read_dir(system_dir).context("Failed to read system directory")? {
        let entry = entry?;
        let path = entry.path();

        if !path.is_dir() {
            continue;
        }

        let question_id = path
            .file_name()
            .and_then(|n| n.to_str())
            .unwrap_or("unknown");

        // Look for the JSON file
        let json_path = path.join(format!("{}.json", question_id));
        if !json_path.exists() {
            continue;
        }

        // Parse JSON and extract media
        match parse_question_media(&json_path, question_id, system_code) {
            Ok(Some(media)) => {
                stats.update_with_question(&media);
                questions_with_media.push(media);
            }
            Ok(None) => {
                // No media found, that's fine
            }
            Err(e) => {
                warn!("Failed to parse {}: {}", json_path.display(), e);
            }
        }

        stats.total_questions_scanned += 1;
    }

    // Calculate final statistics
    stats.total_questions_with_media = questions_with_media.len();
    stats.total_questions_without_media = stats.total_questions_scanned - stats.total_questions_with_media;
    stats.percentage_with_media = if stats.total_questions_scanned > 0 {
        (stats.total_questions_with_media as f64 / stats.total_questions_scanned as f64) * 100.0
    } else {
        0.0
    };

    Ok(())
}

fn parse_question_media(
    json_path: &Path,
    question_id: &str,
    system_code: &str,
) -> Result<Option<QuestionMedia>> {
    let content = fs::read_to_string(json_path)?;
    let json: Value = serde_json::from_str(&content)?;

    let mut figures = Vec::new();
    let mut tables = Vec::new();
    let mut videos = Vec::new();
    let mut svgs = Vec::new();

    // Extract media from the "media" field
    // The extracted JSON structure is:
    // {
    //   "media": {
    //     "tables": [],
    //     "images": ["figures/cvfig24202.hash.jpg", ...],
    //     "svgs": [],
    //     "videos": []
    //   }
    // }
    if let Some(media) = json.get("media").and_then(|m| m.as_object()) {
        // Extract figures from "images" array
        if let Some(images) = media.get("images").and_then(|i| i.as_array()) {
            for (idx, img) in images.iter().enumerate() {
                if let Some(path_str) = img.as_str() {
                    // Parse filename like "figures/cvfig24202.hash.jpg"
                    let parts: Vec<&str> = path_str.split('/').collect();
                    if let Some(filename) = parts.last() {
                        // Extract figure_id and extension
                        let name_parts: Vec<&str> = filename.split('.').collect();
                        let figure_id = name_parts.first().unwrap_or(&"unknown").to_string();
                        let extension = name_parts.last().unwrap_or(&"jpg").to_string();

                        let figure = FigureReference {
                            figure_id,
                            extension,
                            title: None,
                            width: 0,  // Not available in extracted JSON
                            height: 0, // Not available in extracted JSON
                        };
                        figures.push(figure);
                    }
                }
            }
        }

        // Extract tables (stored as strings)
        if let Some(tabs) = media.get("tables").and_then(|t| t.as_array()) {
            for (idx, tab) in tabs.iter().enumerate() {
                if let Some(table_str) = tab.as_str() {
                    let table = TableReference {
                        table_id: format!("{}tab{:05}", system_code, idx + 1),
                        title: None,
                    };
                    tables.push(table);
                }
            }
        }

        // Extract videos (stored as strings)
        if let Some(vids) = media.get("videos").and_then(|v| v.as_array()) {
            for vid in vids.iter() {
                if let Some(video_str) = vid.as_str() {
                    // Video strings might be IDs or URLs
                    let video = VideoReference {
                        video_id: video_str.to_string(),
                        title: None,
                        canonical_location: video_str.to_string(),
                    };
                    videos.push(video);
                }
            }
        }

        // Extract SVGs (stored as strings)
        if let Some(svg_arr) = media.get("svgs").and_then(|s| s.as_array()) {
            for svg in svg_arr.iter() {
                if let Some(svg_str) = svg.as_str() {
                    let svg_ref = SvgReference {
                        svg_id: svg_str.to_string(),
                        source: SvgSource::ContentId(svg_str.to_string()),
                    };
                    svgs.push(svg_ref);
                }
            }
        }
    }

    // If no media found, return None
    if figures.is_empty() && tables.is_empty() && videos.is_empty() && svgs.is_empty() {
        return Ok(None);
    }

    Ok(Some(QuestionMedia {
        question_id: question_id.to_string(),
        array_id: None,
        subspecialty: Some(system_code.to_string()),
        product_type: None,
        figures,
        tables,
        videos,
        svgs,
    }))
}
