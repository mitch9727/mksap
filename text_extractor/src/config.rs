/// Configuration for MKSAP organ systems
/// This module defines all organ systems with their question ID prefixes.
///
/// Note: Some content areas contain AND (e.g., "Pulmonary AND Critical Care Medicine")
/// and use multiple question ID prefixes. These are configured as separate systems
/// in this structure but come from the same content area in the web UI.

#[derive(Debug, Clone)]
pub struct OrganSystem {
    /// System identifier (used in filesystem and checkpoint files)
    pub id: String,

    /// Display name of this system
    pub name: String,

    /// Question ID prefixes to search for this system.
    /// Examples:
    /// - "Foundations of Clinical Practice": ["cs"]
    /// - "Pulmonary Medicine" (part of Pulmonary AND Critical Care): ["pm"]
    /// - "Critical Care Medicine" (part of Pulmonary AND Critical Care): ["cc"]
    /// - "Gastroenterology" (part of Gastroenterology AND Hepatology): ["gi"]
    /// - "Hepatology" (part of Gastroenterology AND Hepatology): ["hp"]
    #[allow(dead_code)]
    pub question_prefixes: Vec<String>,

    /// Historical baseline question count from MKSAP 2024 initial release.
    /// This is INFORMATIONAL ONLY and should NOT be used for validation.
    /// Use discovery metadata (from .checkpoints/discovery_metadata.json) for accurate completion tracking.
    /// The discovery phase determines the actual available questions via API HEAD requests.
    pub baseline_2024_count: u32,
}

impl OrganSystem {
}

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
            baseline_2024_count: 77,  // Estimated split from original 154
        },
        OrganSystem {
            id: "hp".to_string(),
            name: "Hepatology".to_string(),
            question_prefixes: vec!["hp".to_string()],
            baseline_2024_count: 77,  // Estimated split from original 154
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
            baseline_2024_count: 100,  // Estimated split from original 199
        },
        OrganSystem {
            id: "dm".to_string(),
            name: "Dermatology".to_string(),
            question_prefixes: vec!["dm".to_string()],
            baseline_2024_count: 99,  // Estimated split from original 199
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

pub fn get_organ_system_by_id(id: &str) -> Option<OrganSystem> {
    init_organ_systems().into_iter().find(|s| s.id == id)
}
