// Submodules
mod statistics;
mod types;

// Re-exports
pub use statistics::DiscoveryStatistics;
pub use types::{
    FigureReference, QuestionMedia, SvgReference, SvgSource, TableReference, VideoReference,
};

use anyhow::{Context, Result};
use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::fs;
use std::path::Path;
use tracing::{info, warn};

use super::media_ids::{
    count_inline_tables, extract_content_ids, extract_table_ids_from_tables_content, is_figure_id,
    is_svg_id, is_table_id, is_video_id,
};

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
// API-Based Discovery
// ============================================================================

use reqwest::Client;
use std::collections::{HashMap, HashSet};
use std::sync::Arc;
use tokio::sync::Semaphore;

/// Discover questions with media by scanning question JSON for media references:
/// 1. Load all discovered question IDs from text_extractor checkpoints
/// 2. Fetch each question JSON and collect media references
/// 3. Keep only questions that contain any media references
pub async fn discover_media_questions(
    client: &Client,
    base_url: &str,
    concurrent_limit: usize,
) -> Result<DiscoveryResults> {
    info!("Step 1: Loading all discovered question IDs from checkpoints...");

    let all_question_ids = load_all_question_ids_from_checkpoints()?;
    info!("Loaded {} total question IDs", all_question_ids.len());

    info!("Step 2: Loading content metadata for figure formats...");
    let figures_by_id = Arc::new(load_figure_metadata(client, base_url).await?);
    info!("Loaded {} figure metadata entries", figures_by_id.len());

    info!("Step 3: Scanning questions for media references...");

    let (questions_with_media, mut stats) = scan_questions_for_media(
        client,
        base_url,
        &all_question_ids,
        concurrent_limit,
        figures_by_id,
    )
    .await?;

    info!("Found {} questions with media", questions_with_media.len());

    stats.finalize(all_question_ids.len(), questions_with_media.len());

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

/// Scan questions via API to find which contain media references
async fn scan_questions_for_media(
    client: &Client,
    base_url: &str,
    question_ids: &HashSet<String>,
    concurrent_limit: usize,
    figures_by_id: Arc<HashMap<String, FigureReference>>,
) -> Result<(Vec<QuestionMedia>, DiscoveryStatistics)> {
    let semaphore = Arc::new(Semaphore::new(concurrent_limit));
    let mut handles = vec![];

    for question_id in question_ids {
        let client = client.clone();
        let base_url = base_url.to_string();
        let question_id_clone = question_id.clone();
        let sem = semaphore.clone();
        let figures_by_id = figures_by_id.clone();

        let handle = tokio::spawn(async move {
            let _permit = sem.acquire().await.unwrap();
            fetch_question_media(&client, &base_url, &question_id_clone, &figures_by_id).await
        });

        handles.push((question_id.clone(), handle));
    }

    let mut questions_with_media = Vec::new();
    let mut stats = DiscoveryStatistics::default();
    let mut processed = 0;
    let total = handles.len();

    for (question_id, handle) in handles {
        match handle.await {
            Ok(Ok(Some(media))) => {
                stats.update_with_question(&media);
                questions_with_media.push(media);
            }
            Ok(Ok(None)) => {}
            Ok(Err(e)) => {
                warn!("Failed to check {}: {}", question_id, e);
                stats.failed_requests += 1;
            }
            Err(e) => {
                warn!("Task failed for {}: {}", question_id, e);
                stats.failed_requests += 1;
            }
        }

        processed += 1;
        if processed % 100 == 0 {
            info!("Progress: {}/{} questions checked", processed, total);
        }
    }

    info!("Completed checking all {} questions", total);
    Ok((questions_with_media, stats))
}

/// Fetch a specific question and collect media references
async fn fetch_question_media(
    client: &Client,
    base_url: &str,
    question_id: &str,
    figures_by_id: &HashMap<String, FigureReference>,
) -> Result<Option<QuestionMedia>> {
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

    Ok(build_question_media(question_id, &json, figures_by_id))
}

/// Extract system code from question ID (e.g., "cvmcq24001" -> "cv")
fn extract_system_code(question_id: &str) -> &str {
    if question_id.len() >= 2 {
        &question_id[0..2]
    } else {
        "unknown"
    }
}

fn build_question_media(
    question_id: &str,
    json: &Value,
    figures_by_id: &HashMap<String, FigureReference>,
) -> Option<QuestionMedia> {
    let content_ids = extract_content_ids(json);
    let mut figures = Vec::new();
    let mut tables = Vec::new();
    let mut videos = Vec::new();
    let mut svgs = Vec::new();

    let mut seen_figures = HashSet::new();
    let mut seen_tables = HashSet::new();
    let mut seen_videos = HashSet::new();
    let mut seen_svgs = HashSet::new();

    for content_id in content_ids {
        if is_figure_id(&content_id) {
            if seen_figures.insert(content_id.clone()) {
                if let Some(reference) = figures_by_id.get(&content_id) {
                    figures.push(reference.clone());
                } else {
                    figures.push(FigureReference {
                        figure_id: content_id,
                        extension: "unknown".to_string(),
                        title: None,
                        width: 0,
                        height: 0,
                    });
                }
            }
            continue;
        }

        if is_table_id(&content_id) {
            if seen_tables.insert(content_id.clone()) {
                tables.push(TableReference {
                    table_id: content_id,
                    title: None,
                });
            }
            continue;
        }

        if is_video_id(&content_id) {
            if seen_videos.insert(content_id.clone()) {
                videos.push(VideoReference {
                    video_id: content_id.clone(),
                    title: None,
                    canonical_location: question_id.to_string(),
                });
            }
            continue;
        }

        if is_svg_id(&content_id) {
            if seen_svgs.insert(content_id.clone()) {
                svgs.push(SvgReference {
                    svg_id: content_id.clone(),
                    source: SvgSource::ContentId(content_id),
                });
            }
        }
    }

    for table_id in extract_table_ids_from_tables_content(json) {
        if seen_tables.insert(table_id.clone()) {
            tables.push(TableReference {
                table_id,
                title: None,
            });
        }
    }

    let inline_table_count = count_inline_tables(json);
    for idx in 0..inline_table_count {
        let table_id = format!("inline_table_{}", idx + 1);
        if seen_tables.insert(table_id.clone()) {
            tables.push(TableReference {
                table_id,
                title: None,
            });
        }
    }

    if figures.is_empty() && tables.is_empty() && videos.is_empty() && svgs.is_empty() {
        return None;
    }

    let system_code = extract_system_code(question_id);

    Some(QuestionMedia {
        question_id: question_id.to_string(),
        array_id: None,
        subspecialty: Some(system_code.to_string()),
        product_type: None,
        figures,
        tables,
        videos,
        svgs,
    })
}

async fn load_figure_metadata(
    client: &Client,
    base_url: &str,
) -> Result<HashMap<String, FigureReference>> {
    let url = format!("{}/api/content_metadata.json", base_url);
    let response = client
        .get(&url)
        .send()
        .await
        .context("Failed to fetch content metadata")?;

    if !response.status().is_success() {
        anyhow::bail!(
            "Content metadata request failed: HTTP {}",
            response.status()
        );
    }

    let metadata: Value = response.json().await.context("Failed to parse metadata")?;
    let mut figures_by_id = HashMap::new();

    let figures_value = metadata.get("figures");
    match figures_value {
        Some(Value::Array(figures)) => {
            for figure in figures {
                insert_figure_reference(&mut figures_by_id, None, figure);
            }
        }
        Some(Value::Object(figures)) => {
            for (key, figure) in figures {
                insert_figure_reference(&mut figures_by_id, Some(key.as_str()), figure);
            }
        }
        _ => {}
    }

    Ok(figures_by_id)
}

fn insert_figure_reference(
    figures_by_id: &mut HashMap<String, FigureReference>,
    fallback_id: Option<&str>,
    figure: &Value,
) {
    let figure_id = figure
        .get("id")
        .and_then(|v| v.as_str())
        .or(fallback_id)
        .unwrap_or("unknown");

    let extension = figure
        .get("imageInfo")
        .and_then(|info| info.get("extension"))
        .and_then(|ext| ext.as_str())
        .map(|ext| ext.to_ascii_lowercase())
        .unwrap_or_else(|| "unknown".to_string());

    let title = extract_html_text(figure.get("title"));

    let width = figure
        .get("imageInfo")
        .and_then(|info| info.get("width"))
        .and_then(|val| val.as_u64())
        .unwrap_or(0) as u32;

    let height = figure
        .get("imageInfo")
        .and_then(|info| info.get("height"))
        .and_then(|val| val.as_u64())
        .unwrap_or(0) as u32;

    figures_by_id.insert(
        figure_id.to_string(),
        FigureReference {
            figure_id: figure_id.to_string(),
            extension,
            title,
            width,
            height,
        },
    );
}

fn extract_html_text(value: Option<&Value>) -> Option<String> {
    match value {
        Some(Value::String(text)) => Some(text.clone()),
        Some(Value::Object(obj)) => obj
            .get("__html")
            .and_then(|val| val.as_str())
            .map(|text| text.to_string()),
        _ => None,
    }
}
