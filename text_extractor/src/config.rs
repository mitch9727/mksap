//! Configuration for MKSAP organ systems.
//!
//! # Purpose
//!
//! This module defines all 15 organ systems within the MKSAP question bank,
//! their system codes, human-readable names, and historical question counts
//! from MKSAP 2024.
//!
//! # Architecture
//!
//! Note: Some ACP content areas contain multiple organ systems (e.g.,
//! "Pulmonary AND Critical Care Medicine"). These are configured as separate
//! systems in this structure but come from the same content area in the MKSAP web UI.
//!
//! **Separate systems from AND content areas**:
//! - **Gastroenterology** ("gi") & **Hepatology** ("hp") - Split from "Gastroenterology AND Hepatology"
//! - **Pulmonary Medicine** ("pm") & **Critical Care Medicine** ("cc") - Split from "Pulmonary AND Critical Care"
//! - **Interdisciplinary Medicine** ("in") & **Dermatology** ("dm") - Split from joint category
//!
//! # Question ID Pattern
//!
//! Question IDs are constructed as: `{prefix}{type}{year}{number}`
//!
//! Example: `cvmcq24001`
//! - Prefix: `cv` (Cardiovascular)
//! - Type: `mcq` (Multiple Choice Question)
//! - Year: `24` (2024)
//! - Number: `001` (first question)

/// Represents a single organ system within MKSAP.
#[derive(Debug, Clone)]
pub struct OrganSystem {
    /// System identifier - used in filesystem directory names and checkpoint files.
    /// Examples: "cv", "en", "cs", "gi", "hm", etc.
    pub id: String,

    /// Display name of this system (human-readable).
    /// Examples: "Cardiovascular Medicine", "Endocrinology and Metabolism"
    pub name: String,

    /// Question ID prefixes to search for this system.
    /// Currently each system has exactly one prefix, but this is `Vec` to support
    /// future systems that might have multiple prefixes.
    ///
    /// # Examples
    ///
    /// - Cardiovascular ("cv"): `["cv"]`
    /// - Gastroenterology ("gi"): `["gi"]`
    /// - Pulmonary ("pm"): `["pm"]`
    #[allow(dead_code)]
    pub question_prefixes: Vec<String>,

    /// Historical baseline question count from MKSAP 2024 initial release.
    ///
    /// **IMPORTANT**: This is INFORMATIONAL ONLY and should NOT be used for validation.
    /// The discovery phase determines the actual available questions via API HEAD requests.
    /// See `discovery_metadata.json` in the `.checkpoints/` directory for accurate counts.
    pub baseline_2024_count: u32,
}

impl OrganSystem {
    // Intentionally empty - struct is pure configuration data
}

/// Initialize all MKSAP organ systems (15 total).
///
/// # Returns
///
/// Vector of all 15 organ system definitions.
///
/// # System List
///
/// | Code | Name | Questions (2024 baseline) |
/// |------|------|------------------------|
/// | cv | Cardiovascular Medicine | 216 |
/// | en | Endocrinology and Metabolism | 136 |
/// | cs | Foundations of Clinical Practice | 206 |
/// | gi | Gastroenterology | 77 |
/// | hp | Hepatology | 77 |
/// | hm | Hematology | 125 |
/// | id | Infectious Disease | 205 |
/// | in | Interdisciplinary Medicine | 100 |
/// | dm | Dermatology | 99 |
/// | np | Nephrology | 155 |
/// | nr | Neurology | 118 |
/// | on | Oncology | 103 |
/// | pm | Pulmonary Medicine | 131 |
/// | cc | Critical Care Medicine | 55 |
/// | rm | Rheumatology | 131 |
///
/// # Examples
///
/// ```ignore
/// use text_extractor::config::init_organ_systems;
///
/// let systems = init_organ_systems();
/// assert_eq!(systems.len(), 15);
/// assert_eq!(systems[0].id, "cv");
/// ```
pub fn init_organ_systems() -> Vec<OrganSystem> {
    vec![
        OrganSystem {
            id: "cv".to_string(),
            name: "Cardiovascular Medicine".to_string(),
            question_prefixes: vec!["cv".to_string()],
            baseline_2024_count: 216,
        },
        OrganSystem {
            id: "en".to_string(),
            name: "Endocrinology and Metabolism".to_string(),
            question_prefixes: vec!["en".to_string()],
            baseline_2024_count: 136,
        },
        OrganSystem {
            id: "cs".to_string(),
            name: "Foundations of Clinical Practice and Common Symptoms".to_string(),
            question_prefixes: vec!["cs".to_string()],
            baseline_2024_count: 206,
        },
        OrganSystem {
            id: "gi".to_string(),
            name: "Gastroenterology".to_string(),
            question_prefixes: vec!["gi".to_string()],
            baseline_2024_count: 77, // Estimated split from original 154
        },
        OrganSystem {
            id: "hp".to_string(),
            name: "Hepatology".to_string(),
            question_prefixes: vec!["hp".to_string()],
            baseline_2024_count: 77, // Estimated split from original 154
        },
        OrganSystem {
            id: "hm".to_string(),
            name: "Hematology".to_string(),
            question_prefixes: vec!["hm".to_string()],
            baseline_2024_count: 125,
        },
        OrganSystem {
            id: "id".to_string(),
            name: "Infectious Disease".to_string(),
            question_prefixes: vec!["id".to_string()],
            baseline_2024_count: 205,
        },
        OrganSystem {
            id: "in".to_string(),
            name: "Interdisciplinary Medicine".to_string(),
            question_prefixes: vec!["in".to_string()],
            baseline_2024_count: 100, // Estimated split from original 199
        },
        OrganSystem {
            id: "dm".to_string(),
            name: "Dermatology".to_string(),
            question_prefixes: vec!["dm".to_string()],
            baseline_2024_count: 99, // Estimated split from original 199
        },
        OrganSystem {
            id: "np".to_string(),
            name: "Nephrology".to_string(),
            question_prefixes: vec!["np".to_string()],
            baseline_2024_count: 155,
        },
        OrganSystem {
            id: "nr".to_string(),
            name: "Neurology".to_string(),
            question_prefixes: vec!["nr".to_string()],
            baseline_2024_count: 118,
        },
        OrganSystem {
            id: "on".to_string(),
            name: "Oncology".to_string(),
            question_prefixes: vec!["on".to_string()],
            baseline_2024_count: 103,
        },
        OrganSystem {
            id: "pm".to_string(),
            name: "Pulmonary Medicine".to_string(),
            question_prefixes: vec!["pm".to_string()],
            baseline_2024_count: 131,
        },
        OrganSystem {
            id: "cc".to_string(),
            name: "Critical Care Medicine".to_string(),
            question_prefixes: vec!["cc".to_string()],
            baseline_2024_count: 55,
        },
        OrganSystem {
            id: "rm".to_string(),
            name: "Rheumatology".to_string(),
            question_prefixes: vec!["rm".to_string()],
            baseline_2024_count: 131,
        },
    ]
}

/// Look up an organ system by its unique identifier.
///
/// # Arguments
///
/// * `id` - The system code (e.g., "cv", "en", "cs")
///
/// # Returns
///
/// `Some(OrganSystem)` if the system exists, `None` otherwise.
///
/// # Examples
///
/// ```ignore
/// use text_extractor::config::get_organ_system_by_id;
///
/// let cv = get_organ_system_by_id("cv").unwrap();
/// assert_eq!(cv.name, "Cardiovascular Medicine");
///
/// assert!(get_organ_system_by_id("invalid").is_none());
/// ```
pub fn get_organ_system_by_id(id: &str) -> Option<OrganSystem> {
    init_organ_systems().into_iter().find(|s| s.id == id)
}
