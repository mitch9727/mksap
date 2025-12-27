use anyhow::Result;
use std::collections::HashSet;
use std::fs;
use std::path::Path;
use std::time::Duration;
use tracing::{info, warn};

use crate::models::ApiQuestionResponse;

use super::{MKSAPExtractor, CHECKPOINT_DIR_NAME};

impl MKSAPExtractor {
    pub async fn cleanup_retired_questions(&self) -> Result<usize> {
        let mut moved_count = 0;
        let retired_dir = self.failed_root().join("retired");
        fs::create_dir_all(&retired_dir)?;

        info!("Scanning extracted questions for retired entries...");

        let mut skip_dirs = HashSet::new();
        skip_dirs.insert(CHECKPOINT_DIR_NAME);
        let entries = crate::io::scan_question_directories(
            Path::new(&self.output_dir),
            &skip_dirs,
            |_entry| true,
        )?;

        for entry in entries {
            if let Ok(true) = self.is_question_retired(&entry.question_id).await {
                let dest = retired_dir.join(&entry.question_id);
                match fs::rename(&entry.path, &dest) {
                    Ok(()) => {
                        info!("Moved retired question: {}", entry.question_id);
                        moved_count += 1;
                    }
                    Err(e) => {
                        warn!(
                            "Failed to move retired question {}: {}",
                            entry.question_id, e
                        );
                    }
                }
            }
        }

        Ok(moved_count)
    }

    pub fn cleanup_flat_duplicates(&self) -> Result<usize> {
        let mut deleted_count = 0;

        for system_entry in fs::read_dir(&self.output_dir)? {
            let system_entry = match system_entry {
                Ok(entry) => entry,
                Err(_) => continue,
            };
            let system_path = system_entry.path();
            if !system_path.is_dir() {
                continue;
            }

            let system_id = match system_path.file_name().and_then(|n| n.to_str()) {
                Some(name) => name.to_string(),
                None => continue,
            };

            if system_id == CHECKPOINT_DIR_NAME {
                continue;
            }

            for entry in fs::read_dir(&system_path)? {
                let entry = match entry {
                    Ok(entry) => entry,
                    Err(_) => continue,
                };
                let path = entry.path();

                if !path.is_file() {
                    continue;
                }

                if path.extension().and_then(|s| s.to_str()) != Some("json") {
                    continue;
                }

                let question_id = match path.file_stem().and_then(|s| s.to_str()) {
                    Some(stem) => stem.to_string(),
                    None => continue,
                };

                if !Self::looks_like_question_id(&system_id, &question_id) {
                    continue;
                }

                let nested_json = self.question_json_path(&system_id, &question_id);

                if !nested_json.exists() {
                    continue;
                }

                if !Self::is_valid_question_json(&nested_json, &question_id) {
                    warn!(
                        "Skipping duplicate cleanup for {} (nested JSON invalid)",
                        nested_json.display()
                    );
                    continue;
                }

                match fs::remove_file(&path) {
                    Ok(()) => {
                        info!("Deleted duplicate flat JSON {}", path.display());
                        deleted_count += 1;
                    }
                    Err(e) => {
                        warn!("Failed to delete duplicate JSON {}: {}", path.display(), e);
                    }
                }
            }
        }

        Ok(deleted_count)
    }

    /// Check if a question is marked as retired/invalidated via API.
    async fn is_question_retired(&self, question_id: &str) -> Result<bool> {
        let api_url = crate::endpoints::question_json(&self.base_url, question_id);

        let response = match crate::http::send_with_timeout(
            self.client.get(&api_url),
            Duration::from_secs(10),
        )
        .await
        {
            Ok(resp) if resp.status().is_success() => resp,
            _ => return Ok(false),
        };

        let json_text = match response.text().await {
            Ok(text) => text,
            Err(_) => return Ok(false),
        };

        match serde_json::from_str::<ApiQuestionResponse>(&json_text) {
            Ok(api_response) => Ok(api_response.invalidated),
            Err(_) => Ok(false),
        }
    }
}
