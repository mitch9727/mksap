// Submodules
mod discovery_statistics;
mod discovery_types;

// Re-exports
pub use discovery_statistics::DiscoveryStatistics;
pub use discovery_types::{
    FigureReference, QuestionMedia, SvgReference, SvgSource, TableReference, VideoReference,
};

use anyhow::Result;
use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::collections::HashMap;
use std::path::Path;
use tracing::{info, warn};

use super::api::fetch_question_json;
use super::media_ids::{
    classify_content_id, count_inline_tables, extract_content_ids,
    extract_table_ids_from_tables_content, inline_table_id, ContentIdKind,
};
use super::metadata::{
    extract_html_text, extract_image_info, for_each_metadata_item, resolve_metadata_id,
};
use crate::checkpoints::read_all_checkpoint_ids;

// ============================================================================
// Discovery Configuration
// ============================================================================

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DiscoveryConfig {
    pub concurrent_requests: usize,
    pub base_url: String,
}

// ============================================================================
// Discovery Metadata Container
// ============================================================================

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DiscoveryMetadata {
    pub version: String,
    pub timestamp: String,
    pub config: DiscoveryConfig,
    pub statistics: DiscoveryStatistics,
}

// ============================================================================
// Discovery Results Container
// ============================================================================

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DiscoveryResults {
    pub metadata: DiscoveryMetadata,
    pub questions: HashMap<String, QuestionMedia>,
}

impl DiscoveryResults {
    pub(crate) fn new(
        questions: HashMap<String, QuestionMedia>,
        statistics: DiscoveryStatistics,
        base_url: String,
        concurrent_requests: usize,
    ) -> Self {
        Self {
            metadata: DiscoveryMetadata {
                version: "1.0.0".to_string(),
                timestamp: chrono::Utc::now().to_rfc3339(),
                config: DiscoveryConfig {
                    concurrent_requests,
                    base_url,
                },
                statistics,
            },
            questions,
        }
    }

    /// Generate human-readable text report
    pub fn generate_report(&self) -> String {
        self.metadata
            .statistics
            .generate_report(&self.metadata.timestamp)
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
use std::collections::HashSet;
use std::sync::Arc;
use tokio::sync::Semaphore;

/// Discover questions with media by scanning question JSON for media references:
/// 1. Load all discovered question IDs from extractor checkpoints
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

/// Load all question IDs from extractor checkpoint files
fn load_all_question_ids_from_checkpoints() -> Result<HashSet<String>> {
    let checkpoint_dir = Path::new("../mksap_data/.checkpoints");

    if !checkpoint_dir.exists() {
        anyhow::bail!(
            "Checkpoint directory not found: {}. Run the extractor first to discover questions.",
            checkpoint_dir.display()
        );
    }

    read_all_checkpoint_ids(checkpoint_dir)
}

/// Scan questions via API to find which contain media references
async fn scan_questions_for_media(
    client: &Client,
    base_url: &str,
    question_ids: &HashSet<String>,
    concurrent_limit: usize,
    figures_by_id: Arc<HashMap<String, FigureReference>>,
) -> Result<(HashMap<String, QuestionMedia>, DiscoveryStatistics)> {
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

    let mut questions_with_media = HashMap::new();
    let mut stats = DiscoveryStatistics::default();
    let mut processed = 0;
    let total = handles.len();

    for (question_id, handle) in handles {
        match handle.await {
            Ok(Ok(Some(media))) => {
                stats.update_with_question(&question_id, &media);
                questions_with_media.insert(question_id, media);
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
    let json = fetch_question_json(client, base_url, question_id).await?;
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
        match classify_content_id(&content_id) {
            Some(ContentIdKind::Figure) => {
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
            }
            Some(ContentIdKind::Table) => {
                if seen_tables.insert(content_id.clone()) {
                    tables.push(TableReference {
                        table_id: content_id,
                        title: None,
                    });
                }
            }
            Some(ContentIdKind::Video) => {
                if seen_videos.insert(content_id.clone()) {
                    videos.push(VideoReference {
                        video_id: content_id.clone(),
                        title: None,
                        canonical_location: question_id.to_string(),
                    });
                }
            }
            Some(ContentIdKind::Svg) => {
                if seen_svgs.insert(content_id.clone()) {
                    svgs.push(SvgReference {
                        svg_id: content_id.clone(),
                        source: SvgSource::ContentId(content_id),
                    });
                }
            }
            None => {}
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
        let table_id = inline_table_id(idx);
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
        subspecialty: Some(system_code.to_string()),
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
    let metadata = super::fetch_content_metadata(client, base_url).await?;
    let mut figures_by_id = HashMap::new();

    for_each_metadata_item(&metadata, "figures", |fallback_id, figure| {
        insert_figure_reference(&mut figures_by_id, fallback_id, figure);
    });

    Ok(figures_by_id)
}

fn insert_figure_reference(
    figures_by_id: &mut HashMap<String, FigureReference>,
    fallback_id: Option<&str>,
    figure: &Value,
) {
    let figure_id = resolve_metadata_id(figure, fallback_id);

    let image_info = extract_image_info(figure);
    let extension = image_info
        .extension
        .unwrap_or_else(|| "unknown".to_string());

    let title = extract_html_text(figure.get("title"));

    let width = image_info.width.unwrap_or(0);
    let height = image_info.height.unwrap_or(0);

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
