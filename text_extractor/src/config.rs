/// Configuration for MKSAP organ systems
/// This module defines all 12 organ systems with their correct IDs per the specification

#[derive(Debug, Clone)]
pub struct OrganSystem {
    pub id: String,
    pub name: String,
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
            baseline_2024_count: 216,
        },
        OrganSystem {
            id: "en".to_string(),
            name: "Endocrinology and Metabolism".to_string(),
            baseline_2024_count: 136,
        },
        OrganSystem {
            id: "cs".to_string(),
            name: "Foundations of Clinical Practice and Common Symptoms".to_string(),
            baseline_2024_count: 206,
        },
        OrganSystem {
            id: "gi".to_string(),
            name: "Gastroenterology and Hepatology".to_string(),
            baseline_2024_count: 154,
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
            name: "Interdisciplinary Medicine and Dermatology".to_string(),
            baseline_2024_count: 199,
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

pub fn get_organ_system_by_id(id: &str) -> Option<OrganSystem> {
    init_organ_systems().into_iter().find(|s| s.id == id)
}
