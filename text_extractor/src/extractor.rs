use anyhow::{Result, Context};
use reqwest::Client;
use std::fs;
use std::path::Path;
use std::collections::HashSet;
use std::env;
use std::sync::Arc;
use tokio::time::sleep;
use std::time::Duration;
use tracing::{info, error, warn, debug};
use serde_json::json;
use futures::stream::{self, StreamExt};
use rand::seq::SliceRandom;
use rand::thread_rng;
use chrono::Utc;

use crate::models::{QuestionData, ApiQuestionResponse, DiscoveryMetadata, DiscoveryMetadataCollection};
use crate::media::MediaExtractor;
use crate::validator::DataValidator;

const QUESTION_TYPE_CODES: [&str; 6] = ["mcq", "qqq", "vdx", "cor", "mqq", "sq"];
const CHECKPOINT_DIR_NAME: &str = ".checkpoints";
const FAILED_DIR_NAME: &str = "mksap_data_failed";

pub struct MKSAPExtractor {
    base_url: String,
    output_dir: String,
    pub client: Client,
    authenticated: bool,
}

impl MKSAPExtractor {
    pub fn new(base_url: &str, output_dir: &str) -> Result<Self> {
        fs::create_dir_all(output_dir)
            .context("Failed to create output directory")?;

        Ok(Self {
            base_url: base_url.to_string(),
            output_dir: output_dir.to_string(),
            client: Client::new(),
            authenticated: false,
        })
    }

    pub fn with_session_cookie(mut self, session_cookie_value: &str) -> Self {
        // Create a new client with the session cookie in the default headers
        let mut headers = reqwest::header::HeaderMap::new();
        headers.insert(
            reqwest::header::COOKIE,
            format!("_mksap19_session={}", session_cookie_value)
                .parse()
                .unwrap(),
        );

        self.client = Client::builder()
            .default_headers(headers)
            .build()
            .unwrap_or_else(|_| Client::new());

        self
    }

    pub async fn login(&mut self, username: &str, password: &str) -> Result<()> {
        info!("Attempting to authenticate with MKSAP as {}...", username);

        // Try multiple possible login endpoints
        let endpoints = vec![
            format!("{}/api/auth/login", self.base_url),
            format!("{}/api/login", self.base_url),
            format!("{}/auth/login", self.base_url),
            format!("{}/login", self.base_url),
        ];

        let credentials = json!({
            "email": username,
            "password": password,
        });

        for endpoint in endpoints {
            info!("Trying authentication endpoint: {}", endpoint);

            match self.client
                .post(&endpoint)
                .json(&credentials)
                .send()
                .await
            {
                Ok(response) => {
                    let status = response.status();

                    if status.is_success() {
                        self.authenticated = true;
                        info!("Successfully authenticated with MKSAP!");
                        return Ok(());
                    } else if status.as_u16() == 404 {
                        // Try next endpoint
                        continue;
                    } else {
                        let error_text = response.text().await.unwrap_or_default();
                        warn!("Authentication endpoint {} returned {}: {}", endpoint, status, error_text);
                    }
                }
                Err(e) => {
                    warn!("Request to {} failed: {}", endpoint, e);
                    continue;
                }
            }
        }

        warn!("Could not find a valid authentication endpoint. Proceeding without authentication.");
        // Continue anyway - some content might be accessible
        Ok(())
    }

    pub fn is_authenticated(&self) -> bool {
        self.authenticated
    }

    pub fn set_authenticated(&mut self, authenticated: bool) {
        self.authenticated = authenticated;
    }

    pub async fn is_already_authenticated(&self) -> Result<bool> {
        let url = format!("{}/app/question-bank/content-areas/cv/answered-questions", self.base_url);

        match self.client.get(&url).send().await {
            Ok(response) => {
                let is_auth = response.status() == 200;
                if is_auth {
                    info!("✓ Already authenticated (received 200 from question bank page)");
                } else {
                    info!("Not yet authenticated (received {} from question bank page)", response.status());
                }
                Ok(is_auth)
            }
            Err(e) => {
                info!("Could not check authentication status: {}", e);
                Ok(false)
            }
        }
    }

    pub async fn browser_login(&mut self) -> Result<()> {
        use crate::browser::BrowserLogin;
        info!("Falling back to interactive browser login...");

        // Create a detection closure that checks authentication
        let base_url = self.base_url.clone();
        let client = self.client.clone();

        let detection_fn = || async {
            let url = format!("{}/app/question-bank/content-areas/cv/answered-questions", base_url);
            match client.get(&url).send().await {
                Ok(response) => Ok(response.status() == 200),
                Err(_) => Ok(false),
            }
        };

        BrowserLogin::interactive_login(&self.base_url, Some(detection_fn)).await?;
        self.authenticated = true;
        Ok(())
    }

    pub async fn cleanup_retired_questions(&self) -> Result<usize> {
        let mut moved_count = 0;
        let retired_dir = format!("{}/retired", FAILED_DIR_NAME);
        fs::create_dir_all(&retired_dir)?;

        info!("Scanning extracted questions for retired entries...");

        // Scan all extracted question directories
        for category_entry in fs::read_dir(&self.output_dir)? {
            let category_path = match category_entry {
                Ok(entry) => entry.path(),
                Err(_) => continue,
            };
            if !category_path.is_dir() {
                continue;
            }

            for question_entry in fs::read_dir(&category_path)? {
                let question_path = match question_entry {
                    Ok(entry) => entry.path(),
                    Err(_) => continue,
                };
                if !question_path.is_dir() {
                    continue;
                }

                let question_id = match question_path.file_name() {
                    Some(name) => match name.to_str() {
                        Some(id) => id.to_string(),
                        None => continue,
                    },
                    None => continue,
                };

                // Re-fetch from API to check invalidated status
                let api_url = format!("{}/api/questions/{}.json", self.base_url, question_id);
                match tokio::time::timeout(
                    Duration::from_secs(10),
                    self.client.get(&api_url).send()
                ).await {
                    Ok(Ok(response)) if response.status().is_success() => {
                        match response.text().await {
                            Ok(json_text) => {
                                if let Ok(api_response) = serde_json::from_str::<ApiQuestionResponse>(&json_text) {
                                    if api_response.invalidated {
                                        // Move to retired directory
                                        let dest = Path::new(&retired_dir).join(&question_id);
                                        if let Err(e) = fs::rename(&question_path, &dest) {
                                            warn!("Failed to move retired question {}: {}", question_id, e);
                                        } else {
                                            info!("Moved retired question: {}", question_id);
                                            moved_count += 1;
                                        }
                                    }
                                }
                            }
                            Err(_) => continue,
                        }
                    }
                    _ => continue,
                }
            }
        }

        Ok(moved_count)
    }

    pub async fn extract_category(&self, category: &crate::Category) -> Result<usize> {
        info!("Extracting: {}", category.name);

        let existing_ids = self.load_existing_question_ids(&category.code)?;
        let concurrency = Self::concurrency_limit();

        // Phase 1: Discovery - find all valid questions
        debug!("Phase 1: Discovering valid questions for {}...", category.name);
        let refresh = env::var("MKSAP_REFRESH_DISCOVERY")
            .map(|value| value == "1" || value.eq_ignore_ascii_case("true"))
            .unwrap_or(false);
        let valid_ids = if !refresh {
            match self.load_checkpoint_ids(&category.code)? {
                Some(ids) if !ids.is_empty() => {
                    info!("✓ Loaded {} valid question IDs from checkpoint", ids.len());
                    ids
                }
                _ => {
                    let ids = self.discover_questions(&category.question_prefix, &existing_ids).await?;
                    self.save_checkpoint_ids(&category.code, &ids)?;
                    ids
                }
            }
        } else {
            let ids = self.discover_questions(&category.question_prefix, &existing_ids).await?;
            self.save_checkpoint_ids(&category.code, &ids)?;
            ids
        };
        info!("✓ Found {} valid questions", valid_ids.len());

        // Phase 2: Setup - create folders for valid questions
        debug!("Phase 2: Creating directories for {} questions...", valid_ids.len());
        for question_id in &valid_ids {
            let question_folder = Path::new(&self.output_dir)
                .join(&category.code)
                .join(question_id);
            fs::create_dir_all(&question_folder)
                .context("Failed to create question folder")?;
        }
        debug!("✓ Directories created");

        // Phase 3: Extraction - download and process only valid questions
        debug!(
            "Phase 3: Extracting data for {} questions (concurrency: {})...",
            valid_ids.len(),
            concurrency
        );
        let mut questions_extracted = 0;
        let mut questions_skipped = 0;

        let targets: Vec<String> = valid_ids
            .into_iter()
            .filter(|question_id| {
                if existing_ids.contains(question_id) {
                    questions_skipped += 1;
                    false
                } else {
                    true
                }
            })
            .collect();

        let total_to_process = targets.len();
        let mut processed = 0usize;

        let mut stream = stream::iter(targets.into_iter())
            .map(|question_id| async move { (question_id.clone(), self.extract_question(&category.code, &question_id).await) })
            .buffer_unordered(concurrency);

        while let Some((question_id, result)) = stream.next().await {
            processed += 1;
            if processed % 10 == 0 || processed == total_to_process {
                info!("Progress: {}/{} questions processed", processed, total_to_process);
            }

            match result {
                Ok(true) => {
                    questions_extracted += 1;
                }
                Ok(false) => {
                    warn!("Question {} returned 404 despite being in discovery list", question_id);
                }
                Err(e) => {
                    error!("Error extracting {}: {}", question_id, e);
                }
            }
        }

        // Skip count will be included in per-system summary from main.rs

        Ok(questions_extracted)
    }

    /// Log a consolidated discovery result line
    #[allow(dead_code)]
    pub fn log_discovery_result(category_code: &str, discovered_count: usize, question_types: &[&str]) {
        if discovered_count > 0 {
            let types_str = if question_types.is_empty() {
                "0 types".to_string()
            } else {
                format!("{} types", question_types.len())
            };
            info!("✓ {}: Discovered {} questions ({})", category_code, discovered_count, types_str);
        }
    }

    pub async fn retry_missing_json(&self) -> Result<usize> {
        let missing = self.find_missing_json_ids()?;
        let failed = self.find_failed_deserialize_ids()?;
        let checkpoint_missing = self.find_missing_checkpoint_ids()?;
        let mut targets = Vec::new();
        targets.extend(missing);
        targets.extend(failed);
        targets.extend(checkpoint_missing);

        let mut unique = HashSet::new();
        targets.retain(|(category, question_id)| unique.insert(format!("{}::{}", category, question_id)));

        if targets.is_empty() {
            info!("No missing, failed-deserialize, or checkpoint-missing entries found.");
            return Ok(0);
        }

        let concurrency = Self::concurrency_limit();
        info!(
            "Retrying {} missing/failed entries (concurrency: {})...",
            targets.len(),
            concurrency
        );

        let total_to_process = targets.len();
        let mut processed = 0usize;
        let mut recovered = 0usize;

        let mut stream = stream::iter(targets.into_iter())
            .map(|(category_code, question_id)| async move {
                (
                    question_id.clone(),
                    self.extract_question(&category_code, &question_id).await,
                )
            })
            .buffer_unordered(concurrency);

        while let Some((question_id, result)) = stream.next().await {
            processed += 1;
            if processed % 10 == 0 || processed == total_to_process {
                info!("Progress: {}/{} missing questions retried", processed, total_to_process);
            }

            match result {
                Ok(true) => recovered += 1,
                Ok(false) => warn!("Missing question {} still returned 404", question_id),
                Err(e) => error!("Error re-extracting {}: {}", question_id, e),
            }
        }

        info!("Recovered {}/{} missing/failed entries", recovered, total_to_process);
        Ok(recovered)
    }

    pub async fn list_remaining_ids(&self, categories: &[crate::Category]) -> Result<usize> {
        let refresh = env::var("MKSAP_REFRESH_DISCOVERY")
            .map(|value| value == "1" || value.eq_ignore_ascii_case("true"))
            .unwrap_or(false);

        let mut remaining: Vec<String> = Vec::new();

        for category in categories {
            let existing_ids = self.load_existing_question_ids(&category.code)?;
            let valid_ids = if !refresh {
                match self.load_checkpoint_ids(&category.code)? {
                    Some(ids) if !ids.is_empty() => ids,
                    _ => {
                        let ids = self
                            .discover_questions(&category.question_prefix, &existing_ids)
                            .await?;
                        self.save_checkpoint_ids(&category.code, &ids)?;
                        ids
                    }
                }
            } else {
                let ids = self
                    .discover_questions(&category.question_prefix, &existing_ids)
                    .await?;
                self.save_checkpoint_ids(&category.code, &ids)?;
                ids
            };

            for question_id in valid_ids {
                if !existing_ids.contains(&question_id) {
                    remaining.push(format!("{}/{}", category.code, question_id));
                }
            }
        }

        remaining.sort();
        remaining.dedup();

        let output_path = Path::new(&self.output_dir).join("remaining_ids.txt");
        fs::write(&output_path, remaining.join("\n"))
            .context("Failed to write remaining IDs file")?;

        info!(
            "Wrote {} remaining IDs to {}",
            remaining.len(),
            output_path.display()
        );

        Ok(remaining.len())
    }

    /// Phase 1: Discover all valid question IDs
    async fn discover_questions(
        &self,
        question_prefix: &str,
        existing_ids: &HashSet<String>,
    ) -> Result<Vec<String>> {
        let mut question_ids = self.generate_question_ids(question_prefix);
        let total_to_try = question_ids.len();
        let concurrency = Self::concurrency_limit();
        let shuffle = env::var("MKSAP_DISCOVERY_SHUFFLE")
            .map(|value| value == "1" || value.eq_ignore_ascii_case("true"))
            .unwrap_or(false);

        if shuffle {
            question_ids.shuffle(&mut thread_rng());
        }

        info!("Testing {} potential question IDs...", total_to_try);

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
            if tested % 1000 == 0 || tested == total_to_try {
                info!(
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

        // Track discovered question types
        let mut question_types_found: std::collections::HashSet<String> = std::collections::HashSet::new();
        for id in &valid_ids {
            if let Some(type_code) = self.extract_question_type(id) {
                question_types_found.insert(type_code);
            }
        }

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
            question_types_found: question_types_found.into_iter().collect(),
        };

        // Update or create metadata collection
        let mut collection = self.load_discovery_metadata()?.unwrap_or_else(|| {
            DiscoveryMetadataCollection {
                version: "1.0.0".to_string(),
                last_updated: Utc::now().to_rfc3339(),
                systems: Vec::new(),
            }
        });

        // Replace or add system metadata
        collection.systems.retain(|s| s.system_code != question_prefix);
        collection.systems.push(metadata);
        collection.last_updated = Utc::now().to_rfc3339();

        self.save_discovery_metadata(&collection)?;

        info!(
            "Discovery complete for {}: found {} valid questions out of {} candidates ({:.2}% hit rate)",
            question_prefix, discovered_count, total_to_try, hit_rate * 100.0
        );
        Ok(valid_ids)
    }

    fn load_existing_question_ids(&self, category_code: &str) -> Result<HashSet<String>> {
        let mut existing_ids = HashSet::new();
        let category_dir = Path::new(&self.output_dir).join(category_code);

        if !category_dir.exists() {
            return Ok(existing_ids);
        }

        for entry in fs::read_dir(&category_dir).context("Failed to read category directory")? {
            let entry = entry.context("Failed to read directory entry")?;
            let path = entry.path();
            if !path.is_dir() {
                continue;
            }

            if let Some(dir_name) = path.file_name().and_then(|s| s.to_str()) {
                let json_path = path.join(format!("{}.json", dir_name));
                if json_path.exists() {
                    existing_ids.insert(dir_name.to_string());
                }
            }
        }

        Ok(existing_ids)
    }

    fn checkpoint_path(&self, category_code: &str) -> std::path::PathBuf {
        Path::new(&self.output_dir)
            .join(CHECKPOINT_DIR_NAME)
            .join(format!("{}_ids.txt", category_code))
    }

    fn find_missing_json_ids(&self) -> Result<Vec<(String, String)>> {
        let mut missing = Vec::new();
        let root = Path::new(&self.output_dir);

        if !root.exists() {
            return Ok(missing);
        }

        for entry in fs::read_dir(root).context("Failed to read output directory")? {
            let entry = entry.context("Failed to read output directory entry")?;
            let system_path = entry.path();

            if !system_path.is_dir() {
                continue;
            }

            let system_id = match system_path.file_name().and_then(|n| n.to_str()) {
                Some(name) if name != CHECKPOINT_DIR_NAME => name.to_string(),
                _ => continue,
            };

            for question_entry in fs::read_dir(&system_path)
                .context("Failed to read system directory")?
            {
                let question_entry = question_entry.context("Failed to read question directory")?;
                let question_path = question_entry.path();
                if !question_path.is_dir() {
                    continue;
                }

                let question_id = match question_path.file_name().and_then(|n| n.to_str()) {
                    Some(name) => name.to_string(),
                    None => continue,
                };

                let json_path = question_path.join(format!("{}.json", question_id));
                if !json_path.exists() {
                    missing.push((system_id.clone(), question_id));
                }
            }
        }

        Ok(missing)
    }

    fn find_failed_deserialize_ids(&self) -> Result<Vec<(String, String)>> {
        let mut failed = Vec::new();
        let failed_root = self.failed_root().join("deserialize");
        if !failed_root.exists() {
            return Ok(failed);
        }

        for system_entry in fs::read_dir(&failed_root)
            .context("Failed to read failed deserialize directory")?
        {
            let system_entry = system_entry.context("Failed to read failed system entry")?;
            let system_path = system_entry.path();
            if !system_path.is_dir() {
                continue;
            }

            let system_id = match system_path.file_name().and_then(|n| n.to_str()) {
                Some(name) => name.to_string(),
                None => continue,
            };

            for question_entry in fs::read_dir(&system_path)
                .context("Failed to read failed question directory")?
            {
                let question_entry = question_entry.context("Failed to read failed question entry")?;
                let question_path = question_entry.path();
                if !question_path.is_dir() {
                    continue;
                }

                let question_id = match question_path.file_name().and_then(|n| n.to_str()) {
                    Some(name) => name.to_string(),
                    None => continue,
                };

                failed.push((system_id.clone(), question_id));
            }
        }

        Ok(failed)
    }

    fn find_missing_checkpoint_ids(&self) -> Result<Vec<(String, String)>> {
        let mut missing = Vec::new();
        let checkpoint_dir = Path::new(&self.output_dir).join(CHECKPOINT_DIR_NAME);
        if !checkpoint_dir.exists() {
            return Ok(missing);
        }

        for entry in fs::read_dir(&checkpoint_dir)
            .context("Failed to read checkpoint directory")?
        {
            let entry = entry.context("Failed to read checkpoint entry")?;
            let path = entry.path();
            if !path.is_file() {
                continue;
            }

            let filename = match path.file_name().and_then(|n| n.to_str()) {
                Some(name) => name,
                None => continue,
            };

            let system_id = match filename.strip_suffix("_ids.txt") {
                Some(prefix) => prefix.to_string(),
                None => continue,
            };

            let content = fs::read_to_string(&path).context("Failed to read checkpoint file")?;
            for line in content.lines() {
                let question_id = line.trim();
                if question_id.is_empty() {
                    continue;
                }

                let question_path = Path::new(&self.output_dir)
                    .join(&system_id)
                    .join(question_id);
                let json_path = question_path.join(format!("{}.json", question_id));
                if !json_path.exists() {
                    missing.push((system_id.clone(), question_id.to_string()));
                }
            }
        }

        Ok(missing)
    }

    fn load_checkpoint_ids(&self, category_code: &str) -> Result<Option<Vec<String>>> {
        let path = self.checkpoint_path(category_code);
        if !path.exists() {
            return Ok(None);
        }

        let content = fs::read_to_string(&path).context("Failed to read checkpoint file")?;
        let mut ids: Vec<String> = content
            .lines()
            .map(|line| line.trim())
            .filter(|line| !line.is_empty())
            .map(|line| line.to_string())
            .collect();

        ids.sort();
        ids.dedup();

        Ok(Some(ids))
    }

    fn save_checkpoint_ids(&self, category_code: &str, ids: &[String]) -> Result<()> {
        let checkpoint_dir = Path::new(&self.output_dir).join(CHECKPOINT_DIR_NAME);
        fs::create_dir_all(&checkpoint_dir)
            .context("Failed to create checkpoint directory")?;

        let path = self.checkpoint_path(category_code);
        let mut unique_ids: Vec<String> = ids.to_vec();
        unique_ids.sort();
        unique_ids.dedup();
        let content = unique_ids.join("\n");

        fs::write(&path, content).context("Failed to write checkpoint file")?;
        Ok(())
    }

    /// Load discovery metadata from JSON file
    fn load_discovery_metadata(&self) -> Result<Option<DiscoveryMetadataCollection>> {
        let metadata_path = Path::new(&self.output_dir)
            .join(CHECKPOINT_DIR_NAME)
            .join("discovery_metadata.json");

        if !metadata_path.exists() {
            return Ok(None);
        }

        let contents = fs::read_to_string(&metadata_path)
            .context("Failed to read discovery metadata file")?;
        let metadata = serde_json::from_str(&contents)
            .context("Failed to parse discovery metadata JSON")?;
        Ok(Some(metadata))
    }

    /// Save discovery metadata to JSON file
    fn save_discovery_metadata(&self, metadata: &DiscoveryMetadataCollection) -> Result<()> {
        let checkpoint_dir = Path::new(&self.output_dir).join(CHECKPOINT_DIR_NAME);
        fs::create_dir_all(&checkpoint_dir)
            .context("Failed to create checkpoint directory")?;

        let metadata_path = checkpoint_dir.join("discovery_metadata.json");
        let json = serde_json::to_string_pretty(metadata)
            .context("Failed to serialize discovery metadata")?;
        fs::write(&metadata_path, json)
            .context("Failed to write discovery metadata file")?;
        Ok(())
    }

    /// Get metadata for a specific system
    #[allow(dead_code)]
    fn get_system_discovery_metadata(&self, system_code: &str) -> Result<Option<DiscoveryMetadata>> {
        let collection = self.load_discovery_metadata()?;
        Ok(collection.and_then(|c| {
            c.systems.into_iter()
                .find(|s| s.system_code == system_code)
        }))
    }

    /// Extract question type from a question ID
    /// Pattern: {system}{type}{year}{number}
    /// Example: "cvmcq24001" -> "mcq"
    fn extract_question_type(&self, question_id: &str) -> Option<String> {
        let type_codes = ["mcq", "qqq", "vdx", "cor", "mqq", "sq"];
        for type_code in type_codes {
            if question_id.contains(type_code) {
                return Some(type_code.to_string());
            }
        }
        None
    }

    /// Check if a question exists (fast HTTP HEAD request)
    async fn question_exists(&self, question_id: &str) -> Result<bool> {
        let api_url = format!("{}/api/questions/{}.json", self.base_url, question_id);
        let max_retries = env::var("MKSAP_DISCOVERY_RETRIES")
            .ok()
            .and_then(|value| value.parse::<u32>().ok())
            .unwrap_or(3);
        let max_429_retries = env::var("MKSAP_DISCOVERY_429_RETRIES")
            .ok()
            .and_then(|value| value.parse::<u32>().ok())
            .unwrap_or(8);
        let mut attempt = 0u32;
        let mut rate_limit_attempt = 0u32;

        loop {
            attempt += 1;
            match tokio::time::timeout(
                Duration::from_secs(10),
                self.client.head(&api_url).send()
            ).await {
                Ok(Ok(response)) => {
                    match response.status() {
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
                    }
                }
                Ok(Err(_)) | Err(_) => {
                    if attempt <= max_retries {
                        sleep(Duration::from_millis(200)).await;
                        continue;
                    }
                    return Ok(false);
                }
            }
        }
    }

    fn generate_question_ids(&self, category_code: &str) -> Vec<String> {
        let mut ids = Vec::new();

        let year_start = env::var("MKSAP_YEAR_START")
            .ok()
            .and_then(|value| value.parse::<u32>().ok())
            .unwrap_or(23);
        let year_end = env::var("MKSAP_YEAR_END")
            .ok()
            .and_then(|value| value.parse::<u32>().ok())
            .unwrap_or(26);
        let type_codes_env = env::var("MKSAP_QUESTION_TYPES").unwrap_or_else(|_| {
            QUESTION_TYPE_CODES.join(",")
        });
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
                    ids.push(format!("{}{}{:02}{:03}", category_code, type_code, year, num));
                }
            }
        }

        ids
    }

    async fn extract_question(&self, category_code: &str, question_id: &str) -> Result<bool> {
        use crate::models::ApiQuestionResponse;

        let api_url = format!("{}/api/questions/{}.json", self.base_url, question_id);

        let response = tokio::time::timeout(
            Duration::from_secs(30),
            self.client.get(&api_url).send()
        ).await
            .context("Request timeout")?
            .context("Network error")?;

        match response.status() {
            status if status.is_success() => {
                let json_text = response.text().await?;

                let api_response: ApiQuestionResponse = match serde_json::from_str(&json_text) {
                    Ok(response) => response,
                    Err(e) => {
                        self.save_failed_payload(category_code, question_id, &json_text, &e.to_string()).ok();
                        self.save_raw_question_json(category_code, question_id, &json_text, &e.to_string()).ok();
                        return Ok(true);
                    }
                };

                // Skip retired/invalidated questions
                if api_response.invalidated {
                    info!("Skipping retired question: {}", question_id);
                    return Ok(true);
                }

                let question = api_response.into_question_data(category_code.to_string());

                self.download_media(&question).await.ok();
                self.save_question_data(category_code, &question)?;
                self.quarantine_if_invalid(category_code, &question.question_id).ok();

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
            status => {
                Err(anyhow::anyhow!("API error {}", status))
            }
        }
    }

    async fn download_media(&self, question: &QuestionData) -> Result<()> {
        let question_folder = std::path::Path::new(&self.output_dir)
            .join(&question.category)
            .join(&question.question_id);

        fs::create_dir_all(&question_folder)?;

        // Download images
        for (i, img_url) in question.media.images.iter().enumerate() {
            let full_url = if img_url.starts_with("http") {
                img_url.clone()
            } else {
                format!("{}{}", self.base_url, img_url)
            };

            match MediaExtractor::extract_images(
                &self.client,
                vec![&full_url],
                &question.question_id,
                &question_folder
            ).await {
                Ok(_) => {
                    info!("Downloaded image {}/{}", i+1, question.media.images.len());
                }
                Err(e) => {
                    warn!("Failed to download image: {}", e);
                }
            }
        }

        // Download videos
        for (i, video_url) in question.media.videos.iter().enumerate() {
            let full_url = if video_url.starts_with("http") {
                video_url.clone()
            } else {
                format!("{}{}", self.base_url, video_url)
            };

            match MediaExtractor::extract_videos(
                &self.client,
                vec![&full_url],
                &question.question_id,
                &question_folder
            ).await {
                Ok(_) => {
                    info!("Downloaded video {}/{}", i+1, question.media.videos.len());
                }
                Err(e) => {
                    warn!("Failed to download video: {}", e);
                }
            }
        }

        Ok(())
    }

    pub fn save_question_data(&self, category_code: &str, question: &QuestionData) -> Result<()> {
        let question_folder = Path::new(&self.output_dir)
            .join(category_code)
            .join(&question.question_id);

        fs::create_dir_all(&question_folder)
            .context("Failed to create question folder")?;

        // Save JSON
        let json_path = question_folder.join(format!("{}.json", question.question_id));
        let json_content = serde_json::to_string_pretty(&question)?;
        fs::write(&json_path, json_content)
            .context("Failed to write JSON file")?;

        // Save metadata
        self.save_metadata(&question_folder, question)?;

        info!("Saved question data for {}", question.question_id);
        Ok(())
    }

    fn save_metadata(&self, folder: &Path, question: &QuestionData) -> Result<()> {
        let metadata_path = folder.join(format!("{}_metadata.txt", question.question_id));

        let content = format!(
            "Question ID: {}\nCategory: {}\nEducational Objective: {}\nUser Performance: {}\nTime Taken: {}\nExtracted At: {}\n\nMedia Files:\n  Tables: {}\n  Images: {}\n  SVGs: {}\n  Videos: {}\n",
            question.question_id,
            question.category,
            question.educational_objective,
            question.user_performance.result.as_ref().unwrap_or(&"Unknown".to_string()),
            question.user_performance.time_taken.as_ref().unwrap_or(&"Unknown".to_string()),
            question.extracted_at,
            question.media.tables.len(),
            question.media.images.len(),
            question.media.svgs.len(),
            question.media.videos.len(),
        );

        fs::write(metadata_path, content)
            .context("Failed to write metadata file")?;

        Ok(())
    }

    fn save_raw_question_json(
        &self,
        category_code: &str,
        question_id: &str,
        raw_json: &str,
        error_message: &str,
    ) -> Result<()> {
        let question_folder = Path::new(&self.output_dir)
            .join(category_code)
            .join(question_id);

        fs::create_dir_all(&question_folder)
            .context("Failed to create raw question folder")?;

        let json_path = question_folder.join(format!("{}.json", question_id));
        let error_path = question_folder.join(format!("{}_error.txt", question_id));

        if let Ok(value) = serde_json::from_str::<serde_json::Value>(raw_json) {
            let pretty = serde_json::to_string_pretty(&value)?;
            fs::write(&json_path, pretty)
                .context("Failed to write raw JSON file")?;
        } else {
            let raw_path = question_folder.join(format!("{}_raw.txt", question_id));
            fs::write(&raw_path, raw_json)
                .context("Failed to write raw response file")?;
        }

        fs::write(&error_path, error_message)
            .context("Failed to write raw JSON error file")?;

        Ok(())
    }

    fn failed_root(&self) -> std::path::PathBuf {
        Path::new(&self.output_dir).with_file_name(FAILED_DIR_NAME)
    }

    fn save_failed_payload(
        &self,
        category_code: &str,
        question_id: &str,
        raw_json: &str,
        error_message: &str,
    ) -> Result<()> {
        let failed_root = self.failed_root();
        let failed_dir = failed_root
            .join("deserialize")
            .join(category_code)
            .join(question_id);

        fs::create_dir_all(&failed_dir)
            .context("Failed to create failed payload directory")?;

        let json_path = failed_dir.join(format!("{}.json", question_id));
        let error_path = failed_dir.join(format!("{}_error.txt", question_id));

        fs::write(json_path, raw_json).context("Failed to write failed JSON payload")?;
        fs::write(error_path, error_message).context("Failed to write failed JSON error")?;

        Ok(())
    }

    fn quarantine_if_invalid(&self, category_code: &str, question_id: &str) -> Result<()> {
        let enabled = env::var("MKSAP_QUARANTINE_INVALID")
            .map(|value| value == "1" || value.eq_ignore_ascii_case("true"))
            .unwrap_or(false);

        if !enabled {
            return Ok(());
        }

        let question_folder = Path::new(&self.output_dir)
            .join(category_code)
            .join(question_id);

        let validation_result = DataValidator::validate_question(&question_folder, question_id);
        match validation_result {
            Ok(true) => return Ok(()),
            Ok(false) => {}
            Err(_) => {}
        }

        let failed_root = self.failed_root();
        let failed_dir = failed_root
            .join("invalid")
            .join(category_code)
            .join(question_id);

        if let Some(parent) = failed_dir.parent() {
            fs::create_dir_all(parent)
                .context("Failed to create invalid quarantine directory")?;
        }

        if failed_dir.exists() {
            fs::remove_dir_all(&failed_dir)
                .context("Failed to clear existing invalid quarantine directory")?;
        }

        fs::rename(&question_folder, &failed_dir)
            .context("Failed to move invalid question to quarantine")?;

        if let Err(err) = validation_result {
            let error_path = failed_dir.join(format!("{}_error.txt", question_id));
            fs::write(error_path, err.to_string())
                .context("Failed to write invalid quarantine error")?;
        }

        Ok(())
    }

    fn concurrency_limit() -> usize {
        let default = std::thread::available_parallelism()
            .map(|count| count.get())
            .unwrap_or(4);

        env::var("MKSAP_CONCURRENCY")
            .ok()
            .and_then(|value| value.parse::<usize>().ok())
            .filter(|value| *value > 0)
            .unwrap_or(default)
    }
}
