use anyhow::Result;
use reqwest::Client;
use serde_json::Value;
use std::collections::HashMap;
use std::sync::Arc;
use tokio::sync::Semaphore;
use tracing::{info, warn};

use super::helpers::{
    build_figures_index, build_videos_index, categorize_content_ids, extract_content_ids,
    extract_product_type, extract_related_section, extract_subspecialty, is_invalidated,
};
use super::statistics::DiscoveryStatistics;
use super::types::{QuestionMedia, VideoReference};
use super::DiscoveryResults;

// ============================================================================
// Main Discovery Engine
// ============================================================================

pub struct MediaDiscovery {
    client: Client,
    base_url: String,
    concurrent_limit: usize,
    semaphore: Arc<Semaphore>,
    content_metadata: Option<Value>,
}

impl MediaDiscovery {
    pub async fn new(concurrent_limit: usize, base_url: String, client: Client) -> Result<Self> {
        let semaphore = Arc::new(Semaphore::new(concurrent_limit));

        Ok(Self {
            client,
            base_url,
            concurrent_limit,
            semaphore,
            content_metadata: None,
        })
    }

    /// Initialize by fetching and caching content metadata
    pub async fn initialize(&mut self) -> Result<()> {
        info!("Fetching content metadata...");
        let url = format!("{}/api/content_metadata.json", self.base_url);
        let response = self.client.get(&url).send().await?;
        let metadata: Value = response.json().await?;
        self.content_metadata = Some(metadata);
        info!("Content metadata cached successfully");
        Ok(())
    }

    /// Scan all questions for media
    pub async fn scan_all_questions(&self) -> Result<DiscoveryResults> {
        let metadata = self
            .content_metadata
            .as_ref()
            .ok_or_else(|| anyhow::anyhow!("Content metadata not initialized"))?;

        let figures_by_location = build_figures_index(metadata);
        let videos_by_location = build_videos_index(metadata);

        let questions = self.get_questions_map(metadata)?;

        info!(
            "Scanning {} questions with {} concurrent requests...",
            questions.len(),
            self.concurrent_limit
        );

        let (discovered, stats) = self
            .process_all_questions(questions, &figures_by_location, &videos_by_location)
            .await?;

        info!("Discovery complete!");
        info!(
            "Found {} questions with media ({:.1}%)",
            stats.total_questions_with_media, stats.percentage_with_media
        );

        Ok(DiscoveryResults::new(discovered, stats, self.base_url.clone(), self.concurrent_limit))
    }

    fn get_questions_map<'a>(
        &self,
        metadata: &'a Value,
    ) -> Result<&'a serde_json::Map<String, Value>> {
        metadata
            .get("questions")
            .and_then(|q| q.as_object())
            .ok_or_else(|| anyhow::anyhow!("No questions found in metadata"))
    }

    async fn process_all_questions(
        &self,
        questions: &serde_json::Map<String, Value>,
        figures_by_location: &HashMap<String, Vec<super::types::FigureReference>>,
        videos_by_location: &HashMap<String, Vec<VideoReference>>,
    ) -> Result<(Vec<QuestionMedia>, DiscoveryStatistics)> {
        let mut handles = vec![];
        let mut stats = DiscoveryStatistics::default();

        for (array_id_str, question_meta) in questions {
            if is_invalidated(question_meta) {
                stats.skipped_questions += 1;
                continue;
            }

            let handle = self
                .spawn_question_task(
                    array_id_str,
                    question_meta,
                    figures_by_location,
                    videos_by_location,
                )
                .await;

            handles.push(handle);

            if (handles.len() % 100) == 0 {
                info!("Queued: {}/{}", handles.len(), questions.len());
            }
        }

        self.collect_results(handles, questions.len(), &mut stats)
            .await
    }

    async fn spawn_question_task(
        &self,
        array_id_str: &str,
        question_meta: &Value,
        figures_by_location: &HashMap<String, Vec<super::types::FigureReference>>,
        videos_by_location: &HashMap<String, Vec<VideoReference>>,
    ) -> tokio::task::JoinHandle<Result<Option<QuestionMedia>>> {
        let array_id: u32 = array_id_str.parse().unwrap_or(0);
        let internal_id = question_meta
            .get("id")
            .and_then(|v| v.as_str())
            .unwrap_or("")
            .to_string();

        let permit = Arc::clone(&self.semaphore);
        let client = self.client.clone();
        let base_url = self.base_url.clone();
        let figures_by_location = figures_by_location.clone();
        let videos_by_location = videos_by_location.clone();
        let question_meta = question_meta.clone();

        tokio::spawn(async move {
            let _permit = permit.acquire().await;

            discover_question_media(
                &client,
                &base_url,
                array_id,
                &internal_id,
                &question_meta,
                &figures_by_location,
                &videos_by_location,
            )
            .await
        })
    }

    async fn collect_results(
        &self,
        handles: Vec<tokio::task::JoinHandle<Result<Option<QuestionMedia>>>>,
        total_questions: usize,
        stats: &mut DiscoveryStatistics,
    ) -> Result<(Vec<QuestionMedia>, DiscoveryStatistics)> {
        info!("Waiting for all discovery tasks to complete...");
        let mut discovered = Vec::new();
        let mut processed = 0;

        for handle in handles {
            match handle.await {
                Ok(Ok(Some(question_media))) => {
                    stats.update_with_question(&question_media);
                    discovered.push(question_media);
                }
                Ok(Ok(None)) => {}
                Ok(Err(e)) => {
                    warn!("Discovery failed: {}", e);
                    stats.failed_requests += 1;
                }
                Err(e) => {
                    warn!("Task join error: {}", e);
                    stats.failed_requests += 1;
                }
            }

            processed += 1;
            if (processed % 100) == 0 {
                info!("Progress: {}/{}", processed, total_questions);
            }
        }

        stats.finalize(processed, discovered.len());

        Ok((discovered, stats.clone()))
    }
}

// ============================================================================
// Question Processing (static function for tokio::spawn)
// ============================================================================

async fn discover_question_media(
    client: &Client,
    base_url: &str,
    array_id: u32,
    internal_id: &str,
    question_meta: &Value,
    figures_by_location: &HashMap<String, Vec<super::types::FigureReference>>,
    videos_by_location: &HashMap<String, Vec<VideoReference>>,
) -> Result<Option<QuestionMedia>> {
    let subspecialty = extract_subspecialty(question_meta);
    let product_type = extract_product_type(question_meta);

    let question = fetch_question_json(client, base_url, internal_id).await?;
    let content_ids = extract_content_ids(&question);
    let related_section = extract_related_section(question_meta);

    let categorized = categorize_content_ids(content_ids, figures_by_location, related_section);

    let videos = videos_by_location
        .get(internal_id)
        .cloned()
        .unwrap_or_default();

    if categorized.figures.is_empty()
        && categorized.tables.is_empty()
        && videos.is_empty()
        && categorized.svgs.is_empty()
    {
        return Ok(None);
    }

    Ok(Some(QuestionMedia {
        question_id: internal_id.to_string(),
        array_id: Some(array_id),
        subspecialty,
        product_type,
        figures: categorized.figures,
        tables: categorized.tables,
        videos,
        svgs: categorized.svgs,
    }))
}

async fn fetch_question_json(client: &Client, base_url: &str, internal_id: &str) -> Result<Value> {
    let url = format!("{}/api/questions/{}.json", base_url, internal_id);
    let response = client.get(&url).send().await?;
    Ok(response.json().await?)
}
