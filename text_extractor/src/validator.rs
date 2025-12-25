/// Validation module for verifying extracted MKSAP data
/// This module scans the mksap_data folder and verifies that extracted questions
/// match the specification structure and contain required fields

use serde_json::Value;
use std::collections::HashMap;
use std::fs;
use std::path::Path;
use tracing::{warn, error};
use anyhow::Result;
use crate::config;

#[derive(Debug, Clone, serde::Serialize)]
pub struct ValidationResult {
    pub total_questions: usize,
    pub valid_questions: usize,
    pub invalid_questions: Vec<String>,
    pub missing_fields: Vec<(String, Vec<String>)>,
    pub missing_json: Vec<String>,
    pub missing_metadata: Vec<String>,
    pub parse_errors: Vec<String>,
    pub schema_invalid: Vec<String>,
    pub systems_verified: Vec<SystemValidation>,
}

#[derive(Debug, Clone, serde::Serialize)]
pub struct SystemValidation {
    pub system_id: String,
    pub system_name: String,
    pub found_count: usize,
    pub expected_count: u32,
    pub valid_count: usize,
    pub issues: Vec<String>,
}

pub struct DataValidator;

enum ValidationOutcome {
    Valid,
    SchemaInvalid,
    MissingJson,
    MissingMetadata,
    ParseError(String),
}

impl DataValidator {
    fn normalize_system_id(system_id: &str) -> &str {
        system_id
    }

    fn display_system_id(system_id: &str) -> &str {
        Self::normalize_system_id(system_id)
    }

    /// Scan the entire mksap_data directory and validate all extracted questions
    pub fn validate_extraction(mksap_data_dir: &str) -> Result<ValidationResult> {
        let mut result = ValidationResult {
            total_questions: 0,
            valid_questions: 0,
            invalid_questions: Vec::new(),
            missing_fields: Vec::new(),
            missing_json: Vec::new(),
            missing_metadata: Vec::new(),
            parse_errors: Vec::new(),
            schema_invalid: Vec::new(),
            systems_verified: Vec::new(),
        };
        let mut system_map: HashMap<String, SystemValidation> = HashMap::new();

        let path = Path::new(mksap_data_dir);
        if !path.exists() {
            error!("mksap_data directory not found at {}", mksap_data_dir);
            return Ok(result);
        }

        // Iterate through all organ systems
        for entry in fs::read_dir(path)? {
            let entry = entry?;
            let system_path = entry.path();

            if !system_path.is_dir() {
                continue;
            }

            let system_id = system_path.file_name()
                .and_then(|n| n.to_str())
                .unwrap_or("unknown")
                .to_string();
            let system_id = Self::normalize_system_id(&system_id).to_string();
            if system_id == ".checkpoints" {
                continue;
            }

            let system_config = config::get_organ_system_by_id(&system_id);

            let system_validation = system_map.entry(system_id.clone()).or_insert_with(|| {
                SystemValidation {
                    system_id: system_id.clone(),
                    system_name: system_config.as_ref().map(|s| s.name.clone()).unwrap_or_default(),
                    found_count: 0,
                    expected_count: system_config.as_ref().map(|s| s.total_questions).unwrap_or(0),
                    valid_count: 0,
                    issues: Vec::new(),
                }
            });

            // Scan all questions in this system
            for question_entry in fs::read_dir(&system_path)? {
                let question_entry = question_entry?;
                let question_path = question_entry.path();

                if !question_path.is_dir() {
                    continue;
                }

                let question_id = question_path.file_name()
                    .and_then(|n| n.to_str())
                    .unwrap_or("unknown")
                    .to_string();

                system_validation.found_count += 1;
                result.total_questions += 1;

                // Validate this question
                match Self::validate_question_detailed(&question_path, &question_id) {
                    ValidationOutcome::Valid => {
                        result.valid_questions += 1;
                        system_validation.valid_count += 1;
                    }
                    ValidationOutcome::SchemaInvalid => {
                        result.invalid_questions.push(question_id.clone());
                        result.schema_invalid.push(question_id.clone());
                        system_validation.issues.push(format!("Question {} has missing or invalid fields", question_id));
                    }
                    ValidationOutcome::MissingJson => {
                        result.invalid_questions.push(question_id.clone());
                        result.missing_json.push(question_id.clone());
                        system_validation.issues.push(format!(
                            "Question {}: Missing JSON file: {}",
                            question_id,
                            question_path.join(format!("{}.json", question_id)).display()
                        ));
                    }
                    ValidationOutcome::MissingMetadata => {
                        result.invalid_questions.push(question_id.clone());
                        result.missing_metadata.push(question_id.clone());
                        system_validation.issues.push(format!(
                            "Question {}: Missing metadata file: {}",
                            question_id,
                            question_path.join(format!("{}_metadata.txt", question_id)).display()
                        ));
                    }
                    ValidationOutcome::ParseError(error) => {
                        result.invalid_questions.push(question_id.clone());
                        result.parse_errors.push(question_id.clone());
                        system_validation.issues.push(format!("Question {}: {}", question_id, error));
                    }
                }
            }
        }

        let mut systems: Vec<SystemValidation> = system_map.into_values().collect();
        systems.sort_by(|a, b| a.system_id.cmp(&b.system_id));
        for system_validation in systems.iter_mut() {
            if system_validation.found_count != system_validation.expected_count as usize {
                let msg = format!(
                    "System {} found {} questions, expected {}",
                    system_validation.system_id,
                    system_validation.found_count,
                    system_validation.expected_count
                );
                system_validation.issues.push(msg);
            }
        }
        result.systems_verified = systems;

        Ok(result)
    }

    /// Validate a single question's JSON structure
    pub fn validate_question(question_path: &Path, question_id: &str) -> Result<bool> {
        match Self::validate_question_detailed(question_path, question_id) {
            ValidationOutcome::Valid => Ok(true),
            ValidationOutcome::SchemaInvalid => Ok(false),
            ValidationOutcome::MissingJson => Err(anyhow::anyhow!(
                "Missing JSON file: {}",
                question_path.join(format!("{}.json", question_id)).display()
            )),
            ValidationOutcome::MissingMetadata => Err(anyhow::anyhow!(
                "Missing metadata file: {}",
                question_path.join(format!("{}_metadata.txt", question_id)).display()
            )),
            ValidationOutcome::ParseError(error) => Err(anyhow::anyhow!(error)),
        }
    }

    fn validate_question_detailed(question_path: &Path, question_id: &str) -> ValidationOutcome {
        let json_file = question_path.join(format!("{}.json", question_id));
        let metadata_file = question_path.join(format!("{}_metadata.txt", question_id));

        // Check if both files exist
        if !json_file.exists() {
            return ValidationOutcome::MissingJson;
        }

        if !metadata_file.exists() {
            return ValidationOutcome::MissingMetadata;
        }

        // Parse and validate JSON structure
        let json_content = match fs::read_to_string(&json_file) {
            Ok(content) => content,
            Err(e) => return ValidationOutcome::ParseError(e.to_string()),
        };
        let value: Value = match serde_json::from_str(&json_content) {
            Ok(parsed) => parsed,
            Err(e) => return ValidationOutcome::ParseError(e.to_string()),
        };

        // Check required fields per specification
        let required_fields = vec![
            "question_id",
            "category",
            "educational_objective",
            "question_text",
            "question_stem",
            "options",
            "user_performance",
            "critique",
            "key_points",
            "references",
            "related_content",
            "media",
            "extracted_at",
        ];

        let mut all_valid = true;

        for field in required_fields {
            if value.get(field).is_none() {
                warn!("Question {} missing field: {}", question_id, field);
                all_valid = false;
            }
        }

        // Validate options structure
        if let Some(options) = value.get("options").and_then(|o| o.as_array()) {
            for (idx, option) in options.iter().enumerate() {
                if option.get("letter").is_none() || option.get("text").is_none() {
                    warn!("Question {} option {} missing letter or text", question_id, idx);
                    all_valid = false;
                }
            }
        }

        // Validate user_performance structure
        if let Some(perf) = value.get("user_performance") {
            if perf.get("correct_answer").is_none() {
                warn!("Question {} missing correct_answer in user_performance", question_id);
                all_valid = false;
            }
        }

        if all_valid {
            ValidationOutcome::Valid
        } else {
            ValidationOutcome::SchemaInvalid
        }
    }

    /// Generate a validation report
    pub fn generate_report(result: &ValidationResult) -> String {
        let mut report = String::new();

        report.push_str("=== MKSAP DATA VALIDATION REPORT ===\n\n");
        report.push_str(&format!("Total Questions Found: {}\n", result.total_questions));
        report.push_str(&format!("Total Valid Questions: {}\n", result.valid_questions));
        report.push_str(&format!("Total Invalid Questions: {}\n\n", result.invalid_questions.len()));

        report.push_str("=== INVALID BREAKDOWN ===\n");
        report.push_str(&format!("Missing JSON: {}\n", result.missing_json.len()));
        report.push_str(&format!("Missing Metadata: {}\n", result.missing_metadata.len()));
        report.push_str(&format!("Parse Errors: {}\n", result.parse_errors.len()));
        report.push_str(&format!("Schema Invalid: {}\n\n", result.schema_invalid.len()));

        report.push_str("=== PER-SYSTEM SUMMARY ===\n");
        for system in &result.systems_verified {
            let display_id = Self::display_system_id(&system.system_id);
            let status = if system.issues.is_empty() { "✓ OK" } else { "✗ ISSUES" };
            report.push_str(&format!(
                "{} {}: {}/{} questions ({} valid)\n",
                status,
                display_id,
                system.found_count,
                system.expected_count,
                system.valid_count
            ));

            if !system.issues.is_empty() {
                for issue in &system.issues {
                    report.push_str(&format!("  - {}\n", issue));
                }
            }
        }

        if !result.invalid_questions.is_empty() {
            report.push_str("\n=== INVALID QUESTIONS ===\n");
            for question in result.invalid_questions.iter().take(20) {
                report.push_str(&format!("- {}\n", question));
            }
            if result.invalid_questions.len() > 20 {
                report.push_str(&format!("... and {} more\n", result.invalid_questions.len() - 20));
            }
        }

        report
    }

    /// Compare extracted data with specification expectations
    pub fn compare_with_specification(result: &ValidationResult) -> String {
        let organ_systems = config::init_organ_systems();
        let mut comparison = String::new();

        comparison.push_str("=== SPECIFICATION COMPLIANCE REPORT ===\n\n");

        let mut total_expected = 0;
        let mut total_found = 0;

        for system in organ_systems {
            let display_id = Self::display_system_id(&system.id);
            let found = result.systems_verified.iter()
                .find(|s| s.system_id == system.id)
                .map(|s| s.found_count)
                .unwrap_or(0);

            total_expected += system.total_questions;
            total_found += found;

            let percentage = if system.total_questions > 0 {
                (found as f64 / system.total_questions as f64) * 100.0
            } else {
                0.0
            };

            let status = if found >= system.total_questions as usize {
                "✓"
            } else if found > 0 {
                "⚠"
            } else {
                "✗"
            };

            comparison.push_str(&format!(
                "{} {} ({}): {}/{} questions ({:.1}%)\n",
                status,
                display_id,
                system.name,
                found,
                system.total_questions,
                percentage
            ));
        }

        comparison.push_str(&format!(
            "\n=== OVERALL ===\n{}/{} questions extracted ({:.1}%)\n",
            total_found,
            total_expected,
            (total_found as f64 / total_expected as f64) * 100.0
        ));

        comparison
    }
}
