use anyhow::{Context, Result};
use futures::stream::{self, StreamExt};
use std::collections::HashSet;
use std::fs;
use std::path::Path;
use tracing::{error, info, warn};

use super::{MKSAPExtractor, CHECKPOINT_DIR_NAME};
use crate::io::{checkpoint_system_id, read_checkpoint_lines, scan_question_directories};

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
        categories: &[crate::config::Category],
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

    fn find_missing_json_ids(&self) -> Result<Vec<(String, String)>> {
        let root = Path::new(&self.output_dir);
        let mut skip_dirs = std::collections::HashSet::new();
        skip_dirs.insert(CHECKPOINT_DIR_NAME);

        let entries = scan_question_directories(root, &skip_dirs, |entry| {
            let json_path = entry.path.join(format!("{}.json", entry.question_id));
            !json_path.exists()
        })?;

        Ok(entries
            .into_iter()
            .map(|entry| (entry.system_id, entry.question_id))
            .collect())
    }

    fn find_failed_deserialize_ids(&self) -> Result<Vec<(String, String)>> {
        let failed_root = self.failed_root().join("deserialize");
        let skip_dirs = std::collections::HashSet::new();

        let entries = scan_question_directories(&failed_root, &skip_dirs, |_entry| true)?;

        Ok(entries
            .into_iter()
            .map(|entry| (entry.system_id, entry.question_id))
            .collect())
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
        let system_id = checkpoint_system_id(path).unwrap_or_default();
        let content = read_checkpoint_lines(path)?.join("\n");
        Ok((system_id, content))
    }
}
