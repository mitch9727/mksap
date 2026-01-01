use crate::config;
use crate::models::DiscoveryMetadataCollection;
use anyhow::Result;
/// Validation module for verifying extracted MKSAP data
/// This module scans the mksap_data folder and verifies that extracted questions
/// match the specification structure and contain required fields
use serde_json::Value;
use std::collections::HashMap;
use std::fs;
use std::path::Path;
use tracing::{error, warn};

#[derive(Debug, Clone, serde::Serialize)]
pub struct ValidationResult {
    pub total_questions: usize,
    pub valid_questions: usize,
    pub invalid_questions: Vec<String>,
    pub missing_fields: Vec<(String, Vec<String>)>,
    pub missing_json: Vec<String>,
    pub parse_errors: Vec<String>,
    pub schema_invalid: Vec<String>,
    pub systems_verified: Vec<SystemValidation>,
}

#[derive(Debug, Clone, serde::Serialize)]
pub struct SystemValidation {
    pub system_id: String,
    pub system_name: String,
    pub found_count: usize,
    pub discovered_count: usize,
    pub discovery_timestamp: String,
    pub valid_count: usize,
    pub issues: Vec<String>,
}

pub struct DataValidator;

enum ValidationOutcome {
    Valid,
    SchemaInvalid,
    MissingJson,
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
            parse_errors: Vec::new(),
            schema_invalid: Vec::new(),
            systems_verified: Vec::new(),
        };
        let path = Path::new(mksap_data_dir);
        if !path.exists() {
            error!("mksap_data directory not found at {}", mksap_data_dir);
            return Ok(result);
        }

        // Load discovery metadata
        let metadata_path = Path::new(mksap_data_dir)
            .join(".checkpoints")
            .join("discovery_metadata.json");

        let discovery_metadata = if metadata_path.exists() {
            let contents = fs::read_to_string(&metadata_path)?;
            serde_json::from_str::<DiscoveryMetadataCollection>(&contents)?
        } else {
            return Err(anyhow::anyhow!(
                "Discovery metadata not found at {}. Run discovery or extraction first.",
                metadata_path.display()
            ));
        };

        let mut system_map: HashMap<String, SystemValidation> = HashMap::new();
        for system in &discovery_metadata.systems {
            let system_config = config::get_organ_system_by_id(&system.system_code);
            system_map.insert(
                system.system_code.clone(),
                SystemValidation {
                    system_id: system.system_code.clone(),
                    system_name: system_config
                        .as_ref()
                        .map(|s| s.name.clone())
                        .unwrap_or_default(),
                    found_count: 0,
                    discovered_count: system.discovered_count,
                    discovery_timestamp: system.discovery_timestamp.clone(),
                    valid_count: 0,
                    issues: Vec::new(),
                },
            );
        }

        // Iterate through all organ systems
        for entry in fs::read_dir(path)? {
            let entry = entry?;
            let system_path = entry.path();

            if !system_path.is_dir() {
                continue;
            }

            let system_id = system_path
                .file_name()
                .and_then(|n| n.to_str())
                .unwrap_or("unknown")
                .to_string();
            let system_id = Self::normalize_system_id(&system_id).to_string();
            if system_id == ".checkpoints" {
                continue;
            }

            let system_validation = match system_map.get_mut(&system_id) {
                Some(system_validation) => system_validation,
                None => {
                    return Err(anyhow::anyhow!(
                        "Discovery metadata missing for system {} (expected in {})",
                        system_id,
                        metadata_path.display()
                    ));
                }
            };

            // Scan all questions in this system
            for question_entry in fs::read_dir(&system_path)? {
                let question_entry = question_entry?;
                let question_path = question_entry.path();

                if !question_path.is_dir() {
                    continue;
                }

                let question_id = question_path
                    .file_name()
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
                    }
                    ValidationOutcome::MissingJson => {
                        result.invalid_questions.push(question_id.clone());
                        result.missing_json.push(question_id.clone());
                    }
                    ValidationOutcome::ParseError(error) => {
                        result.invalid_questions.push(question_id.clone());
                        result.parse_errors.push(question_id.clone());
                        warn!("Question {} parse error: {}", question_id, error);
                    }
                }
            }
        }

        let mut systems: Vec<SystemValidation> = system_map.into_values().collect();
        systems.sort_by(|a, b| a.system_id.cmp(&b.system_id));
        for system_validation in systems.iter_mut() {
            let discovered = system_validation.discovered_count;

            if system_validation.found_count > discovered {
                let msg = format!(
                    "⚠ Data Integrity Warning: {} extracted > {} discovered (possible stale checkpoint or manual additions)",
                    system_validation.found_count,
                    discovered
                );
                system_validation.issues.push(msg);
            }

            if system_validation.found_count < discovered {
                let msg = format!(
                    "System {} extracted {} / {} discovered ({:.1}%)",
                    system_validation.system_id,
                    system_validation.found_count,
                    discovered,
                    (system_validation.found_count as f64 / discovered as f64) * 100.0
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
                question_path
                    .join(format!("{}.json", question_id))
                    .display()
            )),
            ValidationOutcome::ParseError(error) => Err(anyhow::anyhow!(error)),
        }
    }

    fn validate_question_detailed(question_path: &Path, question_id: &str) -> ValidationOutcome {
        let json_file = question_path.join(format!("{}.json", question_id));

        // Check if JSON file exists
        if !json_file.exists() {
            return ValidationOutcome::MissingJson;
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
        let required_fields = [
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
        let mut all_valid = Self::validate_required_fields(&value, question_id, &required_fields);

        // Validate options structure
        if let Some(options) = value.get("options").and_then(|o| o.as_array()) {
            for (idx, option) in options.iter().enumerate() {
                if option.get("letter").is_none() || option.get("text").is_none() {
                    warn!(
                        "Question {} option {} missing letter or text",
                        question_id, idx
                    );
                    all_valid = false;
                }
            }
        }

        // Validate user_performance structure
        if let Some(perf) = value.get("user_performance") {
            if perf.get("correct_answer").is_none() {
                warn!(
                    "Question {} missing correct_answer in user_performance",
                    question_id
                );
                all_valid = false;
            }
        }

        if all_valid {
            ValidationOutcome::Valid
        } else {
            ValidationOutcome::SchemaInvalid
        }
    }

    fn validate_required_fields(value: &Value, question_id: &str, required: &[&str]) -> bool {
        let mut all_valid = true;
        for field in required {
            if value.get(*field).is_none() {
                warn!("Question {} missing field: {}", question_id, field);
                all_valid = false;
            }
        }
        all_valid
    }

    /// Generate a validation report
    pub fn generate_report(result: &ValidationResult) -> String {
        let mut report = String::new();

        report.push_str("=== MKSAP DATA VALIDATION REPORT ===\n\n");
        report.push_str(&format!(
            "Total Questions Found: {}\n",
            result.total_questions
        ));
        report.push_str(&format!(
            "Total Valid Questions: {}\n",
            result.valid_questions
        ));
        report.push_str(&format!(
            "Total Invalid Questions: {}\n\n",
            result.invalid_questions.len()
        ));

        report.push_str("=== INVALID BREAKDOWN ===\n");
        report.push_str(&format!("Missing JSON: {}\n", result.missing_json.len()));
        report.push_str(&format!("Parse Errors: {}\n", result.parse_errors.len()));
        report.push_str(&format!(
            "Schema Invalid: {}\n\n",
            result.schema_invalid.len()
        ));

        report.push_str("=== PER-SYSTEM SUMMARY ===\n");
        for system in &result.systems_verified {
            let display_id = Self::display_system_id(&system.system_id);

            let discovered = system.discovered_count;
            let percentage = if discovered > 0 {
                (system.found_count as f64 / discovered as f64) * 100.0
            } else {
                0.0
            };

            let status = if system.issues.is_empty() {
                "✓ OK"
            } else {
                "✗ ISSUES"
            };

            report.push_str(&format!(
                "{} {}: {}/{} questions ({} valid, {:.1}% of discovered)\n",
                status, display_id, system.found_count, discovered, system.valid_count, percentage
            ));

            if !system.issues.is_empty() {
                for issue in &system.issues {
                    report.push_str(&format!("  - {}\n", issue));
                }
            }
        }

        if !result.invalid_questions.is_empty() {
            report.push_str("\n=== ISSUE DETAILS (QUESTION IDS) ===\n");

            let mut missing_json = result.missing_json.clone();
            missing_json.sort();
            Self::append_issue_list(&mut report, "Missing JSON", &missing_json);

            let mut parse_errors = result.parse_errors.clone();
            parse_errors.sort();
            Self::append_issue_list(&mut report, "Parse Errors", &parse_errors);

            let mut schema_invalid = result.schema_invalid.clone();
            schema_invalid.sort();
            Self::append_issue_list(&mut report, "Schema Invalid", &schema_invalid);
        }

        report
    }

    /// Compare extracted data with specification expectations
    pub fn compare_with_specification(result: &ValidationResult) -> String {
        let mut comparison = String::new();

        comparison.push_str("=== SPECIFICATION COMPLIANCE REPORT ===\n\n");

        let mut total_discovered = 0usize;
        let mut total_found = 0usize;
        let mut systems = result.systems_verified.clone();
        systems.sort_by(|a, b| a.system_id.cmp(&b.system_id));

        for system in systems {
            let display_id = Self::display_system_id(&system.system_id);
            let found = system.found_count;
            let discovered = system.discovered_count;

            total_discovered += discovered;
            total_found += found;

            let percentage = if discovered > 0 {
                (found as f64 / discovered as f64) * 100.0
            } else {
                0.0
            };
            let status = Self::determine_status(found, discovered, 0.9);

            comparison.push_str(&format!(
                "{} {} ({}): {}/{} questions ({:.1}% of discovered)\n",
                status, display_id, system.system_name, found, discovered, percentage
            ));
        }

        if total_discovered > 0 {
            comparison.push_str(&format!(
                "\n=== OVERALL (DISCOVERY-BASED) ===\n{}/{} questions extracted ({:.1}%)\n",
                total_found,
                total_discovered,
                (total_found as f64 / total_discovered as f64) * 100.0
            ));
        } else {
            comparison
                .push_str("\n=== OVERALL (DISCOVERY-BASED) ===\n0/0 questions extracted (0.0%)\n");
        }

        comparison
    }

    fn determine_status(found: usize, expected: usize, threshold: f64) -> &'static str {
        match (found, expected) {
            (f, e) if f >= e => "✓",
            (f, e) if f > 0 && (f as f64) >= (e as f64 * threshold) => "◐",
            (f, _) if f > 0 => "⚠",
            _ => "✗",
        }
    }

    fn append_issue_list(report: &mut String, label: &str, ids: &[String]) {
        use std::fmt::Write;

        let _ = writeln!(report, "{}: {}", label, ids.len());
        if ids.is_empty() {
            return;
        }

        for chunk in ids.chunks(10) {
            let _ = writeln!(report, "  {}", chunk.join(", "));
        }
    }
}
