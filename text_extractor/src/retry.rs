use anyhow::{Context, Result};
use futures::stream::{self, StreamExt};
use std::collections::HashSet;
use std::fs;
use std::path::Path;
use tracing::{error, info, warn};

use super::{MKSAPExtractor, CHECKPOINT_DIR_NAME};

impl MKSAPExtractor {
    pub async fn retry_missing_json(&self) -> Result<usize> {
        let missing = self.find_missing_json_ids()?;
        let failed = self.find_failed_deserialize_ids()?;
        let checkpoint_missing = self.find_missing_checkpoint_ids()?;
        let mut targets = Vec::new();
        targets.extend(missing);
        targets.extend(failed);
        targets.extend(checkpoint_missing);

        let mut unique = HashSet::new();
        targets.retain(|(category, question_id)| {
            unique.insert(format!("{}::{}", category, question_id))
        });

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
                    self.extract_question(&category_code, &question_id, false)
                        .await,
                )
            })
            .buffer_unordered(concurrency);

        while let Some((question_id, result)) = stream.next().await {
            processed += 1;
            if processed % 10 == 0 || processed == total_to_process {
                info!(
                    "Progress: {}/{} missing questions retried",
                    processed, total_to_process
                );
            }

            match result {
                Ok(true) => recovered += 1,
                Ok(false) => warn!("Missing question {} still returned 404", question_id),
                Err(e) => error!("Error re-extracting {}: {}", question_id, e),
            }
        }

        info!(
            "Recovered {}/{} missing/failed entries",
            recovered, total_to_process
        );
        Ok(recovered)
    }

    pub async fn list_remaining_ids(
        &self,
        categories: &[crate::categories::Category],
    ) -> Result<usize> {
        let mut remaining: Vec<String> = Vec::new();

        for category in categories {
            let existing_ids = self.load_existing_question_ids(&category.code)?;
            let valid_ids = self
                .load_or_discover_ids(&category.code, &category.question_prefix, &existing_ids)
                .await?;

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

    fn scan_question_directories<F>(
        &self,
        root_path: &Path,
        skip_dirs: &std::collections::HashSet<&str>,
        predicate: F,
    ) -> Result<Vec<(String, String)>>
    where
        F: Fn(&str, &Path, &str) -> bool,
    {
        let mut results = Vec::new();

        if !root_path.exists() {
            return Ok(results);
        }

        // Iterate through system directories
        for system_entry in fs::read_dir(root_path).context("Failed to read root directory")? {
            let system_entry = system_entry.context("Failed to read system entry")?;
            let system_path = system_entry.path();

            if !system_path.is_dir() {
                continue;
            }

            let system_id = match system_path.file_name().and_then(|n| n.to_str()) {
                Some(name) if !skip_dirs.contains(name) => name.to_string(),
                _ => continue,
            };

            // Iterate through question directories within system
            for question_entry in
                fs::read_dir(&system_path).context("Failed to read system directory")?
            {
                let question_entry = question_entry.context("Failed to read question entry")?;
                let question_path = question_entry.path();

                if !question_path.is_dir() {
                    continue;
                }

                let question_id = match question_path.file_name().and_then(|n| n.to_str()) {
                    Some(name) => name.to_string(),
                    None => continue,
                };

                // Apply user-provided predicate to filter
                if predicate(&system_id, &question_path, &question_id) {
                    results.push((system_id.clone(), question_id));
                }
            }
        }

        Ok(results)
    }

    fn find_missing_json_ids(&self) -> Result<Vec<(String, String)>> {
        let root = Path::new(&self.output_dir);
        let mut skip_dirs = std::collections::HashSet::new();
        skip_dirs.insert(CHECKPOINT_DIR_NAME);

        self.scan_question_directories(
            root,
            &skip_dirs,
            |_system_id, question_path, question_id| {
                let json_path = question_path.join(format!("{}.json", question_id));
                !json_path.exists()
            },
        )
    }

    fn find_failed_deserialize_ids(&self) -> Result<Vec<(String, String)>> {
        let failed_root = self.failed_root().join("deserialize");
        let skip_dirs = std::collections::HashSet::new();

        // Predicate always returns true (collect all failed deserialize entries)
        self.scan_question_directories(
            &failed_root,
            &skip_dirs,
            |_system_id, _question_path, _question_id| true,
        )
    }

    fn find_missing_checkpoint_ids(&self) -> Result<Vec<(String, String)>> {
        let checkpoint_dir = Path::new(&self.output_dir).join(CHECKPOINT_DIR_NAME);
        if !checkpoint_dir.exists() {
            return Ok(Vec::new());
        }

        let mut missing = Vec::new();

        for entry in fs::read_dir(&checkpoint_dir).context("Failed to read checkpoint directory")? {
            let entry = entry.context("Failed to read checkpoint entry")?;
            let path = entry.path();

            if !path.is_file() {
                continue;
            }

            let (system_id, content) = self.read_checkpoint_file(&path)?;
            if system_id.is_empty() {
                continue;
            }

            for question_id in content.lines().map(str::trim).filter(|q| !q.is_empty()) {
                let json_path = self.question_json_path(&system_id, question_id);

                if !json_path.exists() {
                    missing.push((system_id.clone(), question_id.to_string()));
                }
            }
        }

        Ok(missing)
    }

    /// Helper to read a checkpoint file and extract system ID.
    /// Returns (system_id, content) tuple. system_id will be empty if filename doesn't match pattern.
    fn read_checkpoint_file(&self, path: &Path) -> Result<(String, String)> {
        let filename = path.file_name().and_then(|n| n.to_str()).unwrap_or("");
        let system_id = filename.strip_suffix("_ids.txt").unwrap_or("").to_string();
        let content = fs::read_to_string(path).context("Failed to read checkpoint file")?;
        Ok((system_id, content))
    }
}
