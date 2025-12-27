use anyhow::{Context, Result};
use futures::stream::{self, StreamExt};
use std::fs;
use std::time::Duration;
use tokio::time::sleep;
use tracing::{debug, error, info, warn};

use crate::models::{ApiQuestionResponse, MediaFiles, QuestionData};
use serde_json::Value;

use super::MKSAPExtractor;

impl MKSAPExtractor {
    pub async fn extract_category(
        &self,
        category: &crate::categories::Category,
        refresh_existing: bool,
    ) -> Result<usize> {
        info!("Extracting: {}", category.name);

        let existing_ids = self.load_existing_question_ids(&category.code)?;
        let concurrency = Self::concurrency_limit();

        // Phase 1: Discovery - find all valid questions
        debug!(
            "Phase 1: Discovering valid questions for {}...",
            category.name
        );
        let valid_ids = self
            .load_or_discover_ids(&category.code, &category.question_prefix, &existing_ids)
            .await?;
        info!("✓ Found {} valid questions", valid_ids.len());

        // Phase 2: Setup - create folders for valid questions
        debug!(
            "Phase 2: Creating directories for {} questions...",
            valid_ids.len()
        );
        for question_id in &valid_ids {
            let question_folder = self.question_dir(&category.code, question_id);
            fs::create_dir_all(&question_folder).context("Failed to create question folder")?;
        }
        debug!("✓ Directories created");

        // Phase 3: Extraction - download and process only valid questions
        debug!(
            "Phase 3: Extracting data for {} questions (concurrency: {})...",
            valid_ids.len(),
            concurrency
        );
        let mut questions_extracted = 0;
        let targets: Vec<String> = if refresh_existing {
            valid_ids
        } else {
            valid_ids
                .into_iter()
                .filter(|question_id| !existing_ids.contains(question_id))
                .collect()
        };

        let total_to_process = targets.len();
        let mut processed = 0usize;

        let mut stream = stream::iter(targets.into_iter())
            .map(|question_id| async move {
                (
                    question_id.clone(),
                    self.extract_question(&category.code, &question_id, refresh_existing)
                        .await,
                )
            })
            .buffer_unordered(concurrency);

        while let Some((question_id, result)) = stream.next().await {
            processed += 1;
            if processed % 10 == 0 || processed == total_to_process {
                info!(
                    "Progress: {}/{} questions processed",
                    processed, total_to_process
                );
            }

            match result {
                Ok(true) => {
                    questions_extracted += 1;
                }
                Ok(false) => {
                    warn!(
                        "Question {} returned 404 despite being in discovery list",
                        question_id
                    );
                }
                Err(e) => {
                    error!("Error extracting {}: {}", question_id, e);
                }
            }
        }

        // Skip count will be included in per-system summary from main.rs

        Ok(questions_extracted)
    }

    pub(super) async fn extract_question(
        &self,
        category_code: &str,
        question_id: &str,
        refresh_existing: bool,
    ) -> Result<bool> {
        let json_path = self.question_json_path(category_code, question_id);
        if !refresh_existing
            && json_path.exists()
            && Self::is_valid_question_json(&json_path, question_id)
        {
            info!("Skipping extraction for {} (already exists)", question_id);
            return Ok(true);
        }

        let api_url = format!("{}/api/questions/{}.json", self.base_url, question_id);

        let response =
            tokio::time::timeout(Duration::from_secs(30), self.client.get(&api_url).send())
                .await
                .context("Request timeout")?
                .context("Network error")?;

        match response.status() {
            status if status.is_success() => {
                let json_text = response.text().await?;

                let api_response: ApiQuestionResponse = match serde_json::from_str(&json_text) {
                    Ok(response) => response,
                    Err(e) => {
                        self.save_failed_payload(
                            category_code,
                            question_id,
                            &json_text,
                            &e.to_string(),
                        )
                        .ok();
                        self.save_raw_question_json(
                            category_code,
                            question_id,
                            &json_text,
                            &e.to_string(),
                        )
                        .ok();
                        return Ok(true);
                    }
                };

                // Skip retired/invalidated questions
                if api_response.invalidated {
                    info!("Skipping retired question: {}", question_id);
                    return Ok(true);
                }

                let mut question = api_response.into_question_data(category_code.to_string());
                if refresh_existing {
                    merge_existing_media(&mut question, &json_path);
                }

                self.save_question_data(category_code, &question)?;
                self.quarantine_if_invalid(category_code, &question.question_id)
                    .ok();

                Ok(true)
            }
            reqwest::StatusCode::NOT_FOUND => {
                // Expected with brute force
                Ok(false)
            }
            reqwest::StatusCode::UNAUTHORIZED | reqwest::StatusCode::FORBIDDEN => {
                warn!("Authentication expired for {}", question_id);
                Err(anyhow::anyhow!("Authentication expired"))
            }
            reqwest::StatusCode::TOO_MANY_REQUESTS => {
                warn!("Rate limited, backing off...");
                sleep(Duration::from_secs(60)).await;
                Err(anyhow::anyhow!("Rate limited"))
            }
            status => Err(anyhow::anyhow!("API error {}", status)),
        }
    }
}

fn merge_existing_media(question: &mut QuestionData, json_path: &std::path::Path) {
    let text = match fs::read_to_string(json_path) {
        Ok(text) => text,
        Err(_) => return,
    };
    let value: Value = match serde_json::from_str(&text) {
        Ok(value) => value,
        Err(_) => return,
    };

    if let Some(media_value) = value.get("media") {
        if let Ok(media) = serde_json::from_value::<MediaFiles>(media_value.clone()) {
            question.media = media;
        }
    }

    if let Some(media_metadata) = value.get("media_metadata") {
        if !media_metadata.is_null() {
            question.media_metadata = Some(media_metadata.clone());
        }
    }
}
