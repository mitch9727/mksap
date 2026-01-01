use anyhow::{Context, Result};
use chrono::Utc;
use futures::stream::{self, StreamExt};
use std::collections::HashSet;
use std::env;
use std::fs;
use std::path::Path;
use std::sync::Arc;
use std::time::Duration;
use tokio::time::sleep;
use tracing::debug;

use crate::models::{DiscoveryMetadata, DiscoveryMetadataCollection};
use crate::utils::parse_env;

use super::{MKSAPExtractor, CHECKPOINT_DIR_NAME, QUESTION_TYPE_CODES};

impl MKSAPExtractor {
    pub(crate) async fn load_or_discover_ids(
        &self,
        category_code: &str,
        question_prefix: &str,
        existing_ids: &HashSet<String>,
    ) -> Result<Vec<String>> {
        let refresh = env::var("MKSAP_REFRESH_DISCOVERY")
            .map(|value| value == "1" || value.eq_ignore_ascii_case("true"))
            .unwrap_or(false);

        if !refresh {
            if let Some(ids) = self.load_checkpoint_ids(category_code)? {
                if !ids.is_empty() {
                    debug!("Loaded {} valid question IDs from checkpoint", ids.len());
                    return Ok(ids);
                }
            }
        }

        let ids = self
            .discover_questions(question_prefix, existing_ids)
            .await?;
        self.save_checkpoint_ids(category_code, &ids)?;
        Ok(ids)
    }

    /// Phase 1: Discover all valid question IDs
    pub async fn discover_questions(
        &self,
        question_prefix: &str,
        existing_ids: &HashSet<String>,
    ) -> Result<Vec<String>> {
        let question_ids = self.generate_question_ids(question_prefix);
        let total_to_try = question_ids.len();
        let concurrency = Self::concurrency_limit();

        debug!("Testing {} potential question IDs...", total_to_try);

        let existing_ids = Arc::new(existing_ids.clone());
        let mut tested = 0usize;

        let mut stream = stream::iter(question_ids.into_iter())
            .map(|question_id| {
                let existing_ids = Arc::clone(&existing_ids);
                async move {
                    if existing_ids.contains(&question_id) {
                        return Ok((question_id, true));
                    }
                    let exists = self.question_exists(&question_id).await?;
                    Ok((question_id, exists))
                }
            })
            .buffer_unordered(concurrency);

        let mut valid_ids = Vec::new();
        while let Some(result) = stream.next().await {
            tested += 1;
            if tested.is_multiple_of(1000) || tested == total_to_try {
                debug!(
                    "Discovery progress: {}/{} tested - {} found so far",
                    tested,
                    total_to_try,
                    valid_ids.len()
                );
            }

            match result {
                Ok((question_id, true)) => valid_ids.push(question_id),
                Ok((_question_id, false)) => {}
                Err(e) => return Err(e),
            }
        }

        let question_types_found = self.collect_question_types(&valid_ids);

        // Create and save metadata
        let discovered_count = valid_ids.len();
        let hit_rate = if total_to_try > 0 {
            discovered_count as f64 / total_to_try as f64
        } else {
            0.0
        };

        let metadata = DiscoveryMetadata {
            system_code: question_prefix.to_string(),
            discovered_count,
            discovery_timestamp: Utc::now().to_rfc3339(),
            candidates_tested: total_to_try,
            hit_rate,
            question_types_found: question_types_found.clone(),
        };

        // Update or create metadata collection
        let mut collection = self.load_discovery_metadata()?.unwrap_or_default();

        // Replace or add system metadata
        collection
            .systems
            .retain(|s| s.system_code != question_prefix);
        collection.systems.push(metadata);
        collection.last_updated = Utc::now().to_rfc3339();

        self.save_discovery_metadata(&collection)?;
        debug!(
            "Discovery complete for {}: found {} valid questions out of {} candidates ({:.2}% hit rate)",
            question_prefix, discovered_count, total_to_try, hit_rate * 100.0
        );
        Ok(valid_ids)
    }

    fn collect_question_types(&self, question_ids: &[String]) -> Vec<String> {
        let mut question_types_found: HashSet<String> = HashSet::new();
        for id in question_ids {
            if let Some(type_code) = self.extract_question_type(id) {
                question_types_found.insert(type_code);
            }
        }

        question_types_found.into_iter().collect()
    }

    /// Extract question type from a question ID
    /// Pattern: {system}{type}{year}{number}
    /// Example: "cvmcq24001" -> "mcq"
    fn extract_question_type(&self, question_id: &str) -> Option<String> {
        let type_codes = QUESTION_TYPE_CODES;
        for type_code in type_codes {
            if question_id.contains(type_code) {
                return Some(type_code.to_string());
            }
        }
        None
    }

    /// Check if a question exists (fast HTTP HEAD request)
    async fn question_exists(&self, question_id: &str) -> Result<bool> {
        let api_url = crate::endpoints::question_json(&self.base_url, question_id);
        let max_retries = parse_env("MKSAP_DISCOVERY_RETRIES", 3u32);
        let max_429_retries = parse_env("MKSAP_DISCOVERY_429_RETRIES", 8u32);
        let mut attempt = 0u32;
        let mut rate_limit_attempt = 0u32;

        loop {
            attempt += 1;
            match tokio::time::timeout(Duration::from_secs(10), self.client.head(&api_url).send())
                .await
            {
                Ok(Ok(response)) => match response.status() {
                    status if status.is_success() => return Ok(true),
                    reqwest::StatusCode::NOT_FOUND => return Ok(false),
                    reqwest::StatusCode::UNAUTHORIZED | reqwest::StatusCode::FORBIDDEN => {
                        return Err(anyhow::anyhow!("Authentication expired"));
                    }
                    reqwest::StatusCode::TOO_MANY_REQUESTS => {
                        rate_limit_attempt += 1;
                        if rate_limit_attempt <= max_429_retries {
                            let backoff = 2u64.saturating_pow(rate_limit_attempt.saturating_sub(1));
                            sleep(Duration::from_secs(backoff)).await;
                            continue;
                        }
                        return Err(anyhow::anyhow!(
                            "Rate limited after {} retries during discovery",
                            max_429_retries
                        ));
                    }
                    _status => {
                        if attempt <= max_retries {
                            sleep(Duration::from_millis(200)).await;
                            continue;
                        }
                        return Ok(false);
                    }
                },
                Ok(Err(err)) => {
                    if attempt <= max_retries {
                        sleep(Duration::from_millis(200)).await;
                        continue;
                    }
                    return Err(anyhow::anyhow!(
                        "Network error while checking {} after {} attempts: {}",
                        question_id,
                        attempt,
                        err
                    ));
                }
                Err(_) => {
                    if attempt <= max_retries {
                        sleep(Duration::from_millis(200)).await;
                        continue;
                    }
                    return Err(anyhow::anyhow!(
                        "Network timeout while checking {} after {} attempts",
                        question_id,
                        attempt
                    ));
                }
            }
        }
    }

    fn generate_question_ids(&self, category_code: &str) -> Vec<String> {
        let mut ids = Vec::new();

        let year_start = parse_env("MKSAP_YEAR_START", 23u32);
        let year_end = parse_env("MKSAP_YEAR_END", 26u32);
        let type_codes_env =
            env::var("MKSAP_QUESTION_TYPES").unwrap_or_else(|_| QUESTION_TYPE_CODES.join(","));
        let type_codes: Vec<String> = type_codes_env
            .split(',')
            .map(|value| value.trim().to_lowercase())
            .filter(|value| !value.is_empty())
            .collect();

        // Year range 2023-2026 by default (skip deprecated 2020-2022 questions).
        // Override with MKSAP_YEAR_START and MKSAP_YEAR_END environment variables.
        for type_code in type_codes {
            for year in year_start..=year_end {
                for num in 1..=999 {
                    ids.push(format!(
                        "{}{}{:02}{:03}",
                        category_code, type_code, year, num
                    ));
                }
            }
        }

        ids
    }

    /// Load discovery metadata from JSON file
    fn load_discovery_metadata(&self) -> Result<Option<DiscoveryMetadataCollection>> {
        let metadata_path = Path::new(&self.output_dir)
            .join(CHECKPOINT_DIR_NAME)
            .join("discovery_metadata.json");

        if !metadata_path.exists() {
            return Ok(None);
        }

        let contents =
            fs::read_to_string(&metadata_path).context("Failed to read discovery metadata file")?;
        let metadata =
            serde_json::from_str(&contents).context("Failed to parse discovery metadata JSON")?;
        Ok(Some(metadata))
    }

    /// Save discovery metadata to JSON file
    fn save_discovery_metadata(&self, metadata: &DiscoveryMetadataCollection) -> Result<()> {
        let checkpoint_dir = Path::new(&self.output_dir).join(CHECKPOINT_DIR_NAME);
        fs::create_dir_all(&checkpoint_dir).context("Failed to create checkpoint directory")?;

        let metadata_path = checkpoint_dir.join("discovery_metadata.json");
        let json = serde_json::to_string_pretty(metadata)
            .context("Failed to serialize discovery metadata")?;
        fs::write(&metadata_path, json).context("Failed to write discovery metadata file")?;
        Ok(())
    }
}
