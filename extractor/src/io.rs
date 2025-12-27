use anyhow::{Context, Result};
use std::collections::HashSet;
use std::env;
use std::fs;
use std::path::{Path, PathBuf};
use tracing::debug;

use crate::checkpoints::read_checkpoint_ids;
use crate::models::QuestionData;
use crate::validator::DataValidator;

use super::{MKSAPExtractor, CHECKPOINT_DIR_NAME, QUESTION_TYPE_CODES};

impl MKSAPExtractor {
    pub(super) fn question_dir(&self, category_code: &str, question_id: &str) -> PathBuf {
        Path::new(&self.output_dir)
            .join(category_code)
            .join(question_id)
    }

    pub(super) fn question_json_path(&self, category_code: &str, question_id: &str) -> PathBuf {
        self.question_dir(category_code, question_id)
            .join(format!("{}.json", question_id))
    }

    pub(super) fn looks_like_question_id(category_code: &str, question_id: &str) -> bool {
        if !question_id.starts_with(category_code) {
            return false;
        }

        QUESTION_TYPE_CODES
            .iter()
            .any(|type_code| question_id.contains(type_code))
    }

    pub(super) fn is_valid_question_json(json_path: &Path, expected_id: &str) -> bool {
        let contents = match fs::read_to_string(json_path) {
            Ok(contents) => contents,
            Err(_) => return false,
        };

        let question: QuestionData = match serde_json::from_str(&contents) {
            Ok(question) => question,
            Err(_) => return false,
        };

        if question.question_id != expected_id {
            debug!(
                "Question JSON id mismatch at {} (expected {}, got {})",
                json_path.display(),
                expected_id,
                question.question_id
            );
            return false;
        }

        true
    }

    pub fn load_existing_question_ids(&self, category_code: &str) -> Result<HashSet<String>> {
        let mut existing_ids = HashSet::new();
        let category_dir = Path::new(&self.output_dir).join(category_code);

        if !category_dir.exists() {
            return Ok(existing_ids);
        }

        for entry in fs::read_dir(&category_dir).context("Failed to read category directory")? {
            let entry = entry.context("Failed to read directory entry")?;
            let path = entry.path();

            if path.is_dir() {
                if let Some(dir_name) = path.file_name().and_then(|s| s.to_str()) {
                    if !Self::looks_like_question_id(category_code, dir_name) {
                        continue;
                    }

                    let json_path = path.join(format!("{}.json", dir_name));
                    if json_path.exists() && Self::is_valid_question_json(&json_path, dir_name) {
                        existing_ids.insert(dir_name.to_string());
                    }
                }
                continue;
            }

            if !path.is_file() {
                continue;
            }

            if path.extension().and_then(|s| s.to_str()) != Some("json") {
                continue;
            }

            let file_stem = match path.file_stem().and_then(|s| s.to_str()) {
                Some(stem) => stem,
                None => continue,
            };

            if !Self::looks_like_question_id(category_code, file_stem) {
                continue;
            }

            if Self::is_valid_question_json(&path, file_stem) {
                existing_ids.insert(file_stem.to_string());
            }
        }

        Ok(existing_ids)
    }

    fn checkpoint_path(&self, category_code: &str) -> std::path::PathBuf {
        Path::new(&self.output_dir)
            .join(CHECKPOINT_DIR_NAME)
            .join(format!("{}_ids.txt", category_code))
    }

    pub fn load_checkpoint_ids(&self, category_code: &str) -> Result<Option<Vec<String>>> {
        let path = self.checkpoint_path(category_code);
        if !path.exists() {
            return Ok(None);
        }
        Ok(Some(read_checkpoint_ids(&path)?))
    }

    pub fn save_checkpoint_ids(&self, category_code: &str, ids: &[String]) -> Result<()> {
        let checkpoint_dir = Path::new(&self.output_dir).join(CHECKPOINT_DIR_NAME);
        fs::create_dir_all(&checkpoint_dir).context("Failed to create checkpoint directory")?;

        let path = self.checkpoint_path(category_code);
        let mut unique_ids: Vec<String> = ids.to_vec();
        unique_ids.sort();
        unique_ids.dedup();
        let content = unique_ids.join("\n");

        fs::write(&path, content).context("Failed to write checkpoint file")?;
        Ok(())
    }

    /// Save extracted question data to nested folder structure.
    ///
    /// # Directory Structure
    ///
    /// Creates a nested folder hierarchy for organized question storage:
    /// ```text
    /// mksap_data/
    /// ├── {category_code}/          # e.g., cv, en, cs, gi, etc.
    /// │   ├── {question_id}/        # e.g., cvmcq24001, cvmcq24002
    /// │   │   ├── {question_id}.json     # JSON data only - no metadata files
    /// │   │   ├── figures/          # Downloaded images, SVGs, tables
    /// │   │   ├── videos/           # Downloaded video files
    /// │   │   └── ...               # Other media types
    /// │   └── {question_id}/
    /// │       └── {question_id}.json
    /// ```
    ///
    /// # Rationale
    ///
    /// - **One JSON file per question**: Contains all extracted structured data
    /// - **No metadata.txt files**: All metadata is included in the JSON file
    /// - **Nested directories**: Each question in its own folder for media organization
    /// - **Media co-location**: Images, videos, tables stored alongside question data
    ///
    /// # Arguments
    ///
    /// * `category_code` - The organ system code (e.g., "cv", "en")
    /// * `question` - The extracted question data to save
    ///
    /// # Errors
    ///
    /// Returns error if folder creation or file writing fails.
    pub fn save_question_data(&self, category_code: &str, question: &QuestionData) -> Result<()> {
        let question_folder = self.question_dir(category_code, &question.question_id);

        fs::create_dir_all(&question_folder).context("Failed to create question folder")?;

        // Save JSON - only JSON file, no metadata.txt
        let json_path = self.question_json_path(category_code, &question.question_id);
        let json_content = serde_json::to_string_pretty(&question)?;
        fs::write(&json_path, json_content).context("Failed to write JSON file")?;

        tracing::info!("Saved question data for {}", question.question_id);
        Ok(())
    }

    pub fn save_raw_question_json(
        &self,
        category_code: &str,
        question_id: &str,
        raw_json: &str,
        error_message: &str,
    ) -> Result<()> {
        let question_folder = self.question_dir(category_code, question_id);

        fs::create_dir_all(&question_folder).context("Failed to create raw question folder")?;

        let json_path = self.question_json_path(category_code, question_id);
        let error_path = question_folder.join(format!("{}_error.txt", question_id));

        if let Ok(value) = serde_json::from_str::<serde_json::Value>(raw_json) {
            let pretty = serde_json::to_string_pretty(&value)?;
            fs::write(&json_path, pretty).context("Failed to write raw JSON file")?;
        } else {
            let raw_path = question_folder.join(format!("{}_raw.txt", question_id));
            fs::write(&raw_path, raw_json).context("Failed to write raw response file")?;
        }

        fs::write(&error_path, error_message).context("Failed to write raw JSON error file")?;

        Ok(())
    }

    pub fn save_failed_payload(
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

        fs::create_dir_all(&failed_dir).context("Failed to create failed payload directory")?;

        let json_path = failed_dir.join(format!("{}.json", question_id));
        let error_path = failed_dir.join(format!("{}_error.txt", question_id));

        fs::write(json_path, raw_json).context("Failed to write failed JSON payload")?;
        fs::write(error_path, error_message).context("Failed to write failed JSON error")?;

        Ok(())
    }

    pub fn quarantine_if_invalid(&self, category_code: &str, question_id: &str) -> Result<()> {
        let enabled = env::var("MKSAP_QUARANTINE_INVALID")
            .map(|value| value == "1" || value.eq_ignore_ascii_case("true"))
            .unwrap_or(false);

        if !enabled {
            return Ok(());
        }

        let question_folder = self.question_dir(category_code, question_id);

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
            fs::create_dir_all(parent).context("Failed to create invalid quarantine directory")?;
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
}
