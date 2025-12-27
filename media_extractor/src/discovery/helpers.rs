use serde_json::Value;
use std::collections::HashSet;

/// Extract all content IDs from a question's JSON structure.
pub fn extract_content_ids(question: &Value) -> Vec<String> {
    let mut ids = Vec::new();
    let mut seen = HashSet::new();
    walk_for_content_ids(question, &mut ids, &mut seen);
    ids
}

fn walk_for_content_ids(value: &Value, ids: &mut Vec<String>, seen: &mut HashSet<String>) {
    match value {
        Value::Object(map) => {
            if let Some(Value::Array(content_ids)) = map.get("contentIds") {
                for id in content_ids {
                    if let Some(id_str) = id.as_str() {
                        if seen.insert(id_str.to_string()) {
                            ids.push(id_str.to_string());
                        }
                    }
                }
            }

            for v in map.values() {
                walk_for_content_ids(v, ids, seen);
            }
        }
        Value::Array(items) => {
            for item in items {
                walk_for_content_ids(item, ids, seen);
            }
        }
        _ => {}
    }
}
