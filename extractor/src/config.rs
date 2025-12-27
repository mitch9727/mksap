//! Configuration for MKSAP question system codes.
//!
//! # Purpose
//!
//! This module defines all 16 two-letter system codes used in MKSAP question IDs.
//! These codes are used in API calls and question ID patterns (e.g., cvmcq24001).
//! **NOTE**: These are NOT the same as the 12 content area groupings in the MKSAP browser.
//!
//! # Architecture
//!
//! MKSAP has 12 content areas visible in the browser UI, but uses 16 distinct
//! two-letter system codes in question IDs and API endpoints. Some browser content
//! areas map to multiple system codes:
//!
//! **Browser content area → Multiple system codes**:
//! - "Gastroenterology AND Hepatology" → "gi" (Gastroenterology) & "hp" (Hepatology)
//! - "Pulmonary AND Critical Care" → "pm" (Pulmonary Medicine) & "cc" (Critical Care Medicine)
//! - "General Internal Medicine" → "in" (Interdisciplinary Medicine) & "dm" (Dermatology)
//! - "Foundations of Clinical Practice" → "fc" (Foundations of Clinical Practice) & "cs" (Common Symptoms)
//!
//! # Question ID Pattern
//!
//! Question IDs are constructed as: `{system_code}{type}{year}{number}`
//!
//! Example: `cvmcq24001`
//! - System code: `cv` (Cardiovascular Medicine)
//! - Type: `mcq` (Multiple Choice Question)
//! - Year: `24` (2024)
//! - Number: `001` (first question)

/// Represents a single question system code within MKSAP.
///
/// System codes are two-letter identifiers used in question IDs and API endpoints.
#[derive(Debug, Clone)]
pub struct OrganSystem {
    /// Two-letter system code identifier - used in question IDs, filesystem directory names,
    /// and checkpoint files.
    /// Examples: "cv", "en", "fc", "cs", "gi", "hm", etc.
    pub id: String,

    /// Display name of this system code (human-readable).
    /// Examples: "Cardiovascular Medicine", "Endocrinology and Metabolism"
    pub name: String,

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

#[derive(Debug, Clone)]
pub struct Category {
    pub code: String,
    pub name: String,
    pub question_prefix: String,
}

/// Initialize all MKSAP question system codes (16 total).
///
/// # Returns
///
/// Vector of all 16 question system code definitions.
///
/// # Question System Codes
///
/// | Code | Name | Questions (2024 baseline) |
/// |------|------|------------------------|
/// | cv | Cardiovascular Medicine | 216 |
/// | en | Endocrinology and Metabolism | 136 |
/// | fc | Foundations of Clinical Practice | 0 (TBD) |
/// | cs | Common Symptoms | 98 |
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
/// use mksap_extractor::config::init_organ_systems;
///
/// let systems = init_organ_systems();
/// assert_eq!(systems.len(), 16);
/// assert_eq!(systems[0].id, "cv");
/// ```
pub fn init_organ_systems() -> Vec<OrganSystem> {
    vec![
        OrganSystem {
            id: "cv".to_string(),
            name: "Cardiovascular Medicine".to_string(),
            baseline_2024_count: 216,
        },
        OrganSystem {
            id: "en".to_string(),
            name: "Endocrinology and Metabolism".to_string(),
            baseline_2024_count: 136,
        },
        OrganSystem {
            id: "fc".to_string(),
            name: "Foundations of Clinical Practice".to_string(),
            baseline_2024_count: 0, // To be discovered via API
        },
        OrganSystem {
            id: "cs".to_string(),
            name: "Common Symptoms".to_string(),
            baseline_2024_count: 98, // Actual discovered count
        },
        OrganSystem {
            id: "gi".to_string(),
            name: "Gastroenterology".to_string(),
            baseline_2024_count: 77, // Estimated split from original 154
        },
        OrganSystem {
            id: "hp".to_string(),
            name: "Hepatology".to_string(),
            baseline_2024_count: 77, // Estimated split from original 154
        },
        OrganSystem {
            id: "hm".to_string(),
            name: "Hematology".to_string(),
            baseline_2024_count: 125,
        },
        OrganSystem {
            id: "id".to_string(),
            name: "Infectious Disease".to_string(),
            baseline_2024_count: 205,
        },
        OrganSystem {
            id: "in".to_string(),
            name: "Interdisciplinary Medicine".to_string(),
            baseline_2024_count: 100, // Estimated split from original 199
        },
        OrganSystem {
            id: "dm".to_string(),
            name: "Dermatology".to_string(),
            baseline_2024_count: 99, // Estimated split from original 199
        },
        OrganSystem {
            id: "np".to_string(),
            name: "Nephrology".to_string(),
            baseline_2024_count: 155,
        },
        OrganSystem {
            id: "nr".to_string(),
            name: "Neurology".to_string(),
            baseline_2024_count: 118,
        },
        OrganSystem {
            id: "on".to_string(),
            name: "Oncology".to_string(),
            baseline_2024_count: 103,
        },
        OrganSystem {
            id: "pm".to_string(),
            name: "Pulmonary Medicine".to_string(),
            baseline_2024_count: 131,
        },
        OrganSystem {
            id: "cc".to_string(),
            name: "Critical Care Medicine".to_string(),
            baseline_2024_count: 55,
        },
        OrganSystem {
            id: "rm".to_string(),
            name: "Rheumatology".to_string(),
            baseline_2024_count: 131,
        },
    ]
}

pub fn build_categories_from_config() -> Vec<Category> {
    init_organ_systems()
        .into_iter()
        .map(|sys| {
            let id = sys.id;
            Category {
                code: id.clone(),
                name: sys.name,
                question_prefix: id,
            }
        })
        .collect()
}

/// Look up a question system code by its unique identifier.
///
/// # Arguments
///
/// * `id` - The two-letter system code (e.g., "cv", "en", "fc", "cs")
///
/// # Returns
///
/// `Some(OrganSystem)` if the system code exists, `None` otherwise.
///
/// # Examples
///
/// ```ignore
/// use mksap_extractor::config::get_organ_system_by_id;
///
/// let cv = get_organ_system_by_id("cv").unwrap();
/// assert_eq!(cv.name, "Cardiovascular Medicine");
///
/// assert!(get_organ_system_by_id("invalid").is_none());
/// ```
pub fn get_organ_system_by_id(id: &str) -> Option<OrganSystem> {
    init_organ_systems().into_iter().find(|s| s.id == id)
}
