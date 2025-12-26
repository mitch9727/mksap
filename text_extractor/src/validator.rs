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

    // NEW: Discovery-based metrics (source of truth)
    pub discovered_count: Option<usize>, // From checkpoint metadata
    pub discovery_timestamp: Option<String>,

    // DEPRECATED: Hardcoded baseline (informational only)
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

        // NEW: Load discovery metadata
        let metadata_path = Path::new(mksap_data_dir)
            .join(".checkpoints")
            .join("discovery_metadata.json");

        let discovery_metadata = if metadata_path.exists() {
            let contents = fs::read_to_string(&metadata_path)?;
            Some(serde_json::from_str::<DiscoveryMetadataCollection>(
                &contents,
            )?)
        } else {
            warn!("No discovery metadata found - completion percentages will use baseline counts");
            None
        };

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

            let system_config = config::get_organ_system_by_id(&system_id);

            // Get discovered count from discovery metadata if available
            let (discovered_count, discovery_timestamp) = discovery_metadata
                .as_ref()
                .and_then(|m| m.systems.iter().find(|s| s.system_code == system_id))
                .map(|s| {
                    (
                        Some(s.discovered_count),
                        Some(s.discovery_timestamp.clone()),
                    )
                })
                .unwrap_or((None, None));

            let system_validation =
                system_map
                    .entry(system_id.clone())
                    .or_insert_with(|| SystemValidation {
                        system_id: system_id.clone(),
                        system_name: system_config
                            .as_ref()
                            .map(|s| s.name.clone())
                            .unwrap_or_default(),
                        found_count: 0,
                        discovered_count,
                        discovery_timestamp,
                        expected_count: system_config
                            .as_ref()
                            .map(|s| s.baseline_2024_count)
                            .unwrap_or(0),
                        valid_count: 0,
                        issues: Vec::new(),
                    });

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
                        system_validation.issues.push(format!(
                            "Question {} has missing or invalid fields",
                            question_id
                        ));
                    }
                    ValidationOutcome::MissingJson => {
                        result.invalid_questions.push(question_id.clone());
                        result.missing_json.push(question_id.clone());
                        system_validation.issues.push(format!(
                            "Question {}: Missing JSON file: {}",
                            question_id,
                            question_path
                                .join(format!("{}.json", question_id))
                                .display()
                        ));
                    }
                    ValidationOutcome::MissingMetadata => {
                        result.invalid_questions.push(question_id.clone());
                        result.missing_metadata.push(question_id.clone());
                        system_validation.issues.push(format!(
                            "Question {}: Missing metadata file: {}",
                            question_id,
                            question_path
                                .join(format!("{}_metadata.txt", question_id))
                                .display()
                        ));
                    }
                    ValidationOutcome::ParseError(error) => {
                        result.invalid_questions.push(question_id.clone());
                        result.parse_errors.push(question_id.clone());
                        system_validation
                            .issues
                            .push(format!("Question {}: {}", question_id, error));
                    }
                }
            }
        }

        let mut systems: Vec<SystemValidation> = system_map.into_values().collect();
        systems.sort_by(|a, b| a.system_id.cmp(&b.system_id));
        for system_validation in systems.iter_mut() {
            // NEW: Use discovered count if available, otherwise fall back to expected (baseline)
            let check_against = system_validation
                .discovered_count
                .unwrap_or(system_validation.expected_count as usize);

            // Check for data integrity issues
            if let Some(discovered) = system_validation.discovered_count {
                if system_validation.found_count > discovered {
                    let msg = format!(
                        "⚠ Data Integrity Warning: {} extracted > {} discovered (possible stale checkpoint or manual additions)",
                        system_validation.found_count,
                        discovered
                    );
                    system_validation.issues.push(msg);
                }
            }

            // Check for incomplete extraction (only if using discovered count)
            if system_validation.discovered_count.is_some()
                && system_validation.found_count < check_against
            {
                let msg = format!(
                    "System {} extracted {} / {} discovered ({:.1}%)",
                    system_validation.system_id,
                    system_validation.found_count,
                    check_against,
                    (system_validation.found_count as f64 / check_against as f64) * 100.0
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
            ValidationOutcome::MissingMetadata => Err(anyhow::anyhow!(
                "Missing metadata file: {}",
                question_path
                    .join(format!("{}_metadata.txt", question_id))
                    .display()
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
        report.push_str(&format!(
            "Missing Metadata: {}\n",
            result.missing_metadata.len()
        ));
        report.push_str(&format!("Parse Errors: {}\n", result.parse_errors.len()));
        report.push_str(&format!(
            "Schema Invalid: {}\n\n",
            result.schema_invalid.len()
        ));

        report.push_str("=== PER-SYSTEM SUMMARY ===\n");
        for system in &result.systems_verified {
            let display_id = Self::display_system_id(&system.system_id);

            // NEW: Use discovered count if available
            let check_against = system
                .discovered_count
                .unwrap_or(system.expected_count as usize);
            let percentage = if check_against > 0 {
                (system.found_count as f64 / check_against as f64) * 100.0
            } else {
                0.0
            };

            let status = if system.issues.is_empty() {
                "✓ OK"
            } else {
                "✗ ISSUES"
            };
            let metadata_label = if system.discovered_count.is_some() {
                "discovered"
            } else {
                "expected"
            };

            report.push_str(&format!(
                "{} {}: {}/{} questions ({} valid, {:.1}% of {})\n",
                status,
                display_id,
                system.found_count,
                check_against,
                system.valid_count,
                percentage,
                metadata_label
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
                report.push_str(&format!(
                    "... and {} more\n",
                    result.invalid_questions.len() - 20
                ));
            }
        }

        report
    }

    /// Generate detailed discovery-aware validation report with metadata
    #[allow(dead_code)]
    pub fn generate_discovery_report(
        result: &ValidationResult,
        discovery_metadata: &Option<DiscoveryMetadataCollection>,
    ) -> String {
        let mut report = String::new();

        report.push_str("# MKSAP Extraction Validation Report (Discovery-Based)\n\n");
        report.push_str(&format!(
            "Generated: {}\n\n",
            chrono::Local::now().to_rfc2822()
        ));

        // Overall statistics
        report.push_str("## Overall Statistics\n\n");

        if let Some(ref metadata) = discovery_metadata {
            let total_discovered: usize = metadata.systems.iter().map(|s| s.discovered_count).sum();

            let total_extracted = result.valid_questions;
            let overall_pct = if total_discovered > 0 {
                (total_extracted as f64 / total_discovered as f64) * 100.0
            } else {
                0.0
            };

            report.push_str(&format!(
                "- **Total Discovered** (via API): {} questions\n",
                total_discovered
            ));
            report.push_str(&format!(
                "- **Total Extracted**: {} questions\n",
                total_extracted
            ));
            report.push_str(&format!(
                "- **Overall Completion**: {:.1}%\n\n",
                overall_pct
            ));
            report.push_str(&format!(
                "- **Discovery Last Updated**: {}\n\n",
                metadata.last_updated
            ));
        } else {
            report.push_str(
                "- **Discovery Metadata**: Not available (no discovery has been performed)\n",
            );
            report.push_str(&format!(
                "- **Total Extracted**: {} questions\n\n",
                result.valid_questions
            ));
        }

        // Historical baseline (informational)
        let total_baseline: u32 = config::init_organ_systems()
            .iter()
            .map(|s| s.baseline_2024_count)
            .sum();
        report.push_str(&format!(
            "- **Historical Baseline** (MKSAP 2024 initial release): {} questions (informational only)\n\n",
            total_baseline
        ));

        // Per-system breakdown
        report.push_str("## System Breakdown\n\n");
        report.push_str("| System | Extracted | Discovered | Baseline | % Complete | Status |\n");
        report.push_str("|--------|-----------|------------|----------|------------|--------|\n");

        for system_val in &result.systems_verified {
            let discovered_str = system_val
                .discovered_count
                .map(|d| d.to_string())
                .unwrap_or_else(|| "?".to_string());

            let percentage = if let Some(discovered) = system_val.discovered_count {
                if discovered > 0 {
                    (system_val.found_count as f64 / discovered as f64) * 100.0
                } else {
                    0.0
                }
            } else {
                0.0
            };

            let status = if system_val.found_count > system_val.discovered_count.unwrap_or(0) {
                "⚠ Over-extracted"
            } else if percentage >= 100.0 {
                "✓ Complete"
            } else if percentage >= 90.0 {
                "◐ 90%+"
            } else {
                "○ Incomplete"
            };

            report.push_str(&format!(
                "| {} | {} | {} | {} | {:.1}% | {} |\n",
                system_val.system_id,
                system_val.found_count,
                discovered_str,
                system_val.expected_count,
                percentage,
                status
            ));
        }

        // Data integrity warnings
        report.push_str("\n## Data Integrity Checks\n\n");

        let mut warnings_found = false;
        for system_val in &result.systems_verified {
            if let Some(discovered) = system_val.discovered_count {
                if system_val.found_count > discovered {
                    if !warnings_found {
                        warnings_found = true;
                    }
                    report.push_str(&format!(
                        "⚠ **WARNING**: System `{}` has {} extracted but only {} discovered.\n",
                        system_val.system_id, system_val.found_count, discovered
                    ));
                    report.push_str("  - Possible causes: Stale discovery checkpoint, manual additions, or extraction errors.\n");
                    report.push_str(&format!(
                        "  - Recommendation: Re-run discovery phase for system `{}`.\n\n",
                        system_val.system_id
                    ));
                }
            }
        }

        if !warnings_found {
            report.push_str("✓ No data integrity warnings detected.\n\n");
        }

        // Discovery statistics
        if let Some(ref metadata) = discovery_metadata {
            report.push_str("## Discovery Statistics\n\n");

            for sys_meta in &metadata.systems {
                report.push_str(&format!("### System: {}\n\n", sys_meta.system_code));
                report.push_str(&format!(
                    "- Discovered: {} questions\n",
                    sys_meta.discovered_count
                ));
                report.push_str(&format!(
                    "- Candidates Tested: {}\n",
                    sys_meta.candidates_tested
                ));
                report.push_str(&format!("- Hit Rate: {:.2}%\n", sys_meta.hit_rate * 100.0));
                report.push_str(&format!(
                    "- Question Types Found: {}\n",
                    sys_meta.question_types_found.join(", ")
                ));
                report.push_str(&format!(
                    "- Last Discovery: {}\n\n",
                    sys_meta.discovery_timestamp
                ));
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
        let mut total_discovered = 0;
        let mut total_found = 0;
        let has_discovery_metadata = result
            .systems_verified
            .iter()
            .any(|s| s.discovered_count.is_some());

        for system in organ_systems {
            let display_id = Self::display_system_id(&system.id);
            let system_val = result
                .systems_verified
                .iter()
                .find(|s| s.system_id == system.id);

            let found = system_val.map(|s| s.found_count).unwrap_or(0);

            // NEW: Use discovered count if available, otherwise use baseline
            let check_against = system_val
                .and_then(|s| s.discovered_count)
                .unwrap_or(system.baseline_2024_count as usize);

            total_expected += system.baseline_2024_count;
            if let Some(sys) = system_val {
                if let Some(discovered) = sys.discovered_count {
                    total_discovered += discovered;
                }
            }
            total_found += found;

            let percentage = if check_against > 0 {
                (found as f64 / check_against as f64) * 100.0
            } else {
                0.0
            };

            let status = if let Some(discovered) = system_val.and_then(|s| s.discovered_count) {
                // Use discovered count for status
                if found >= discovered {
                    "✓"
                } else if found > 0 && found >= (discovered as f64 * 0.9) as usize {
                    "◐"
                } else if found > 0 {
                    "⚠"
                } else {
                    "✗"
                }
            } else {
                // Fallback to baseline
                if found >= system.baseline_2024_count as usize {
                    "✓"
                } else if found > 0 {
                    "⚠"
                } else {
                    "✗"
                }
            };

            let denominator_label = if system_val.and_then(|s| s.discovered_count).is_some() {
                "discovered"
            } else {
                "baseline"
            };

            comparison.push_str(&format!(
                "{} {} ({}): {}/{} questions ({:.1}% of {})\n",
                status,
                display_id,
                system.name,
                found,
                check_against,
                percentage,
                denominator_label
            ));
        }

        // NEW: Show overall statistics with discovery-based totals if available
        if has_discovery_metadata && total_discovered > 0 {
            comparison.push_str(&format!(
                "\n=== OVERALL (DISCOVERY-BASED) ===\n{}/{} questions extracted ({:.1}%)\n",
                total_found,
                total_discovered,
                (total_found as f64 / total_discovered as f64) * 100.0
            ));
        } else {
            comparison.push_str(&format!(
                "\n=== OVERALL (BASELINE) ===\n{}/{} questions extracted ({:.1}%)\n",
                total_found,
                total_expected,
                (total_found as f64 / total_expected as f64) * 100.0
            ));
        }

        comparison
    }
}
