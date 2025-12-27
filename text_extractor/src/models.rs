use serde::de::Deserializer;
use serde::{Deserialize, Serialize};
use std::collections::HashSet;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct QuestionData {
    pub question_id: String,
    pub category: String,
    pub educational_objective: String,
    pub metadata: QuestionMetadata,
    pub question_text: String,
    pub question_stem: String,
    pub options: Vec<AnswerOption>,
    pub user_performance: UserPerformance,
    pub critique: String,
    #[serde(default)]
    pub critique_links: Vec<CritiqueLink>,
    pub key_points: Vec<String>,
    pub references: String,
    pub related_content: RelatedContent,
    pub media: MediaFiles,
    #[serde(default)]
    pub media_metadata: Option<serde_json::Value>,
    pub extracted_at: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CritiqueLink {
    pub href: String,
    pub text: String,
    pub target: Option<String>,
    pub title: Option<String>,
    pub rel: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct QuestionMetadata {
    pub care_types: Vec<String>,
    pub patient_types: Vec<String>,
    pub high_value_care: bool,
    pub question_updated: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AnswerOption {
    pub letter: String,
    pub text: String,
    pub peer_percentage: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UserPerformance {
    pub user_answer: Option<String>,
    pub correct_answer: Option<String>,
    pub result: Option<String>,
    pub time_taken: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RelatedContent {
    pub syllabus: Vec<String>,
    pub learning_plan_topic: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MediaFiles {
    pub tables: Vec<String>,
    pub images: Vec<String>,
    pub svgs: Vec<String>,
    pub videos: Vec<String>,
}

impl Default for MediaFiles {
    fn default() -> Self {
        Self {
            tables: Vec::new(),
            images: Vec::new(),
            svgs: Vec::new(),
            videos: Vec::new(),
        }
    }
}

/// API response structure from MKSAP API endpoint
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ApiQuestionResponse {
    #[serde(default)]
    pub id: String,

    #[serde(default)]
    pub invalidated: bool,

    #[serde(rename = "correctAnswer", default)]
    pub correct_answer: String,

    #[serde(default, deserialize_with = "deserialize_objective_or_default")]
    pub objective: ApiObjective,

    #[serde(default, deserialize_with = "deserialize_vec_or_null")]
    pub options: Vec<ApiAnswerOption>,

    #[serde(default, deserialize_with = "deserialize_vec_or_null")]
    pub stimulus: Vec<serde_json::Value>,

    #[serde(default, deserialize_with = "deserialize_vec_or_null")]
    pub prompt: Vec<serde_json::Value>,

    #[serde(default, deserialize_with = "deserialize_vec_or_null")]
    pub exposition: Vec<serde_json::Value>,

    #[serde(default, deserialize_with = "deserialize_vec_or_null")]
    pub keypoints: Vec<serde_json::Value>,

    #[serde(default, deserialize_with = "deserialize_vec_or_null")]
    pub references: Vec<serde_json::Value>,

    #[serde(rename = "relatedSection", default)]
    pub related_section: String,

    #[serde(rename = "peerComparison", default)]
    pub peer_comparison: serde_json::Value,

    #[serde(default)]
    pub hospitalist: bool,

    #[serde(default)]
    pub hvc: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(untagged)]
pub enum ApiObjective {
    Html {
        #[serde(rename = "__html")]
        html: String,
    },
    Text(String),
}

impl Default for ApiObjective {
    fn default() -> Self {
        ApiObjective::Text(String::new())
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ApiAnswerOption {
    pub letter: String,
    pub text: ApiTextValue,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(untagged)]
pub enum ApiTextValue {
    Text(String),
    Node(serde_json::Value),
}

impl ApiQuestionResponse {
    /// Convert API response to QuestionData format
    pub fn into_question_data(self, category: String) -> QuestionData {
        // Extract text content from HTML-like structures
        let objective_text = match self.objective {
            ApiObjective::Html { html } => html,
            ApiObjective::Text(text) => text,
        };
        let stimulus_text = extract_text_from_nodes(&self.stimulus);
        let prompt_text = extract_text_from_nodes(&self.prompt);
        let exposition_text = extract_text_from_nodes(&self.exposition);
        let critique_links = extract_links_from_nodes(&self.exposition);
        let keypoints_list = extract_keypoints(&self.keypoints);
        let references_text = extract_references(&self.references);

        QuestionData {
            question_id: self.id.clone(),
            category,
            educational_objective: objective_text,
            metadata: QuestionMetadata {
                care_types: Vec::new(),
                patient_types: Vec::new(),
                high_value_care: self.hvc,
                question_updated: chrono::Local::now().format("%m/%d/%Y").to_string(),
            },
            question_text: stimulus_text,
            question_stem: prompt_text,
            options: self
                .options
                .into_iter()
                .map(|o| AnswerOption {
                    letter: o.letter,
                    text: extract_text_from_value(&o.text),
                    peer_percentage: 0,
                })
                .collect(),
            user_performance: UserPerformance {
                user_answer: None,
                correct_answer: Some(self.correct_answer),
                result: None,
                time_taken: None,
            },
            critique: exposition_text,
            critique_links,
            key_points: keypoints_list,
            references: references_text,
            related_content: RelatedContent {
                syllabus: vec![self.related_section],
                learning_plan_topic: String::new(),
            },
            media: MediaFiles::default(),
            media_metadata: None,
            extracted_at: chrono::Local::now().to_rfc3339(),
        }
    }
}

fn deserialize_vec_or_null<'de, D, T>(deserializer: D) -> Result<Vec<T>, D::Error>
where
    D: Deserializer<'de>,
    T: Deserialize<'de>,
{
    Ok(Option::<Vec<T>>::deserialize(deserializer)?.unwrap_or_default())
}

fn deserialize_objective_or_default<'de, D>(deserializer: D) -> Result<ApiObjective, D::Error>
where
    D: Deserializer<'de>,
{
    Ok(Option::<ApiObjective>::deserialize(deserializer)?.unwrap_or_default())
}

/// Helper function to extract plain text from JSON node structures
fn extract_text_from_nodes(nodes: &[serde_json::Value]) -> String {
    let mut text = String::new();

    for node in nodes {
        text.push_str(&extract_text_from_json(node));
    }

    text.trim().to_string()
}

fn extract_text_from_value(value: &ApiTextValue) -> String {
    match value {
        ApiTextValue::Text(text) => text.clone(),
        ApiTextValue::Node(node) => extract_text_from_json(node),
    }
}

fn extract_text_from_json(node: &serde_json::Value) -> String {
    let mut text = String::new();

    match node {
        serde_json::Value::String(s) => text.push_str(s),
        serde_json::Value::Object(obj) => {
            if let Some(children) = obj.get("children").and_then(|c| c.as_array()) {
                for child in children {
                    text.push_str(&extract_text_from_json(child));
                }
            }
        }
        serde_json::Value::Array(items) => {
            for item in items {
                text.push_str(&extract_text_from_json(item));
            }
        }
        _ => {}
    }

    text
}

fn extract_links_from_nodes(nodes: &[serde_json::Value]) -> Vec<CritiqueLink> {
    let mut links = Vec::new();
    let mut seen = HashSet::new();

    for node in nodes {
        extract_links_from_value(node, &mut links, &mut seen);
    }

    links
}

fn extract_links_from_value(
    value: &serde_json::Value,
    links: &mut Vec<CritiqueLink>,
    seen: &mut HashSet<(String, String, Option<String>, Option<String>, Option<String>)>,
) {
    match value {
        serde_json::Value::Object(obj) => {
            if is_anchor_tag(obj) {
                if let Some(attrs) = obj.get("attrs") {
                    if let Some(href) = extract_attr_string(attrs, "href") {
                        let text = extract_link_text(
                            obj.get("children"),
                            attrs,
                            &href,
                        );
                        let target = extract_attr_string(attrs, "target");
                        let title = extract_attr_string(attrs, "title");
                        let rel = extract_attr_string(attrs, "rel");
                        let key = (
                            href.clone(),
                            text.clone(),
                            target.clone(),
                            title.clone(),
                            rel.clone(),
                        );
                        if seen.insert(key) {
                            links.push(CritiqueLink {
                                href,
                                text,
                                target,
                                title,
                                rel,
                            });
                        }
                    }
                }
            }

            for child in obj.values() {
                extract_links_from_value(child, links, seen);
            }
        }
        serde_json::Value::Array(items) => {
            for item in items {
                extract_links_from_value(item, links, seen);
            }
        }
        _ => {}
    }
}

fn is_anchor_tag(obj: &serde_json::Map<String, serde_json::Value>) -> bool {
    if let Some(tag) = obj.get("tagName").and_then(|t| t.as_str()) {
        if tag.eq_ignore_ascii_case("a") {
            return true;
        }
    }
    if let Some(tag) = obj.get("tag").and_then(|t| t.as_str()) {
        if tag.eq_ignore_ascii_case("a") {
            return true;
        }
    }
    if let Some(tag) = obj.get("type").and_then(|t| t.as_str()) {
        if tag.eq_ignore_ascii_case("a") {
            return true;
        }
    }
    false
}

fn extract_attr_string(attrs: &serde_json::Value, key: &str) -> Option<String> {
    let value = attrs.get(key)?;
    match value {
        serde_json::Value::String(text) => Some(text.clone()),
        serde_json::Value::Object(obj) => obj
            .get("__html")
            .and_then(|val| val.as_str())
            .map(|text| text.to_string()),
        _ => None,
    }
}

fn extract_link_text(
    children: Option<&serde_json::Value>,
    attrs: &serde_json::Value,
    href: &str,
) -> String {
    let mut text = match children {
        Some(serde_json::Value::Array(items)) => items
            .iter()
            .map(extract_text_from_json)
            .collect::<Vec<_>>()
            .join(""),
        Some(serde_json::Value::String(text)) => text.clone(),
        Some(other) => extract_text_from_json(other),
        None => String::new(),
    };

    text = compact_text(&text);
    if !text.is_empty() {
        return text;
    }

    if let Some(label) = extract_attr_string(attrs, "aria-label")
        .or_else(|| extract_attr_string(attrs, "ariaLabel"))
    {
        let label = compact_text(&label);
        if !label.is_empty() {
            return label;
        }
    }

    if let Some(title) = extract_attr_string(attrs, "title") {
        let title = compact_text(&title);
        if !title.is_empty() {
            return title;
        }
    }

    href.to_string()
}

fn compact_text(text: &str) -> String {
    text.split_whitespace().collect::<Vec<_>>().join(" ")
}

/// Helper function to extract keypoints from the keypoints array
fn extract_keypoints(nodes: &[serde_json::Value]) -> Vec<String> {
    nodes
        .iter()
        .filter_map(|node| {
            if let Some(obj) = node.as_object() {
                if let Some(children) = obj.get("children").and_then(|c| c.as_array()) {
                    let text = children
                        .iter()
                        .filter_map(|child| match child {
                            serde_json::Value::String(s) => Some(s.clone()),
                            serde_json::Value::Object(o) => o
                                .get("children")
                                .and_then(|c| c.as_array())
                                .and_then(|a| a.first())
                                .and_then(|v| v.as_str())
                                .map(|s| s.to_string()),
                            _ => None,
                        })
                        .collect::<Vec<_>>()
                        .join("");

                    if !text.is_empty() {
                        return Some(text);
                    }
                }
            }
            None
        })
        .collect()
}

/// Helper function to extract references
fn extract_references(refs: &[serde_json::Value]) -> String {
    refs.iter()
        .filter_map(|r| {
            if let Some(arr) = r.as_array() {
                let ref_text = arr
                    .iter()
                    .filter_map(|item| match item {
                        serde_json::Value::String(s) => Some(s.clone()),
                        serde_json::Value::Object(o) => o
                            .get("children")
                            .and_then(|c| c.as_array())
                            .and_then(|a| a.first())
                            .and_then(|v| v.as_str())
                            .map(|s| s.to_string()),
                        _ => None,
                    })
                    .collect::<Vec<_>>()
                    .join("");

                if !ref_text.is_empty() {
                    return Some(ref_text);
                }
            }
            None
        })
        .collect::<Vec<_>>()
        .join("\n")
}

/// Discovery metadata for a single organ system
/// Tracks statistics from the discovery phase to provide accurate completion metrics
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DiscoveryMetadata {
    /// Organ system code (e.g., "cv", "en", "gi")
    pub system_code: String,
    /// Number of questions discovered via API HEAD requests
    pub discovered_count: usize,
    /// ISO 8601 timestamp of when discovery was performed
    pub discovery_timestamp: String,
    /// Total number of question ID candidates tested during discovery
    pub candidates_tested: usize,
    /// Hit rate: discovered_count / candidates_tested
    pub hit_rate: f64,
    /// Question types found (e.g., ["mcq", "qqq", "vdx", "cor"])
    pub question_types_found: Vec<String>,
}

/// Collection of discovery metadata for all organ systems
/// Used as source of truth for completion percentages (replaces hardcoded expected counts)
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DiscoveryMetadataCollection {
    /// Schema version for future compatibility
    pub version: String,
    /// ISO 8601 timestamp of last update (any system)
    pub last_updated: String,
    /// Discovery metadata for each organ system
    pub systems: Vec<DiscoveryMetadata>,
}
