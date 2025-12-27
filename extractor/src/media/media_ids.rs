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

pub fn extract_table_ids_from_tables_content(question: &Value) -> Vec<String> {
    question
        .get("tablesContent")
        .and_then(|tables| tables.as_object())
        .map(|tables| tables.keys().cloned().collect())
        .unwrap_or_default()
}

pub fn count_inline_tables(value: &Value) -> usize {
    collect_inline_table_nodes(value).len()
}

pub fn collect_inline_table_nodes<'a>(value: &'a Value) -> Vec<&'a Value> {
    fn walk<'a>(value: &'a Value, tables: &mut Vec<&'a Value>, in_tables_content: bool) {
        match value {
            Value::Object(map) => {
                if !in_tables_content {
                    if let Some(Value::String(tag)) = map.get("tagName") {
                        if tag.eq_ignore_ascii_case("table") {
                            tables.push(value);
                            return;
                        }
                    }
                }

                for (key, child) in map {
                    let next_in_tables_content = in_tables_content || key == "tablesContent";
                    walk(child, tables, next_in_tables_content);
                }
            }
            Value::Array(items) => {
                for item in items {
                    walk(item, tables, in_tables_content);
                }
            }
            _ => {}
        }
    }

    let mut tables = Vec::new();
    walk(value, &mut tables, false);
    tables
}

pub fn is_figure_id(content_id: &str) -> bool {
    let lower = content_id.to_ascii_lowercase();
    lower.starts_with("fig") || lower.get(2..).map_or(false, |tail| tail.starts_with("fig"))
}

pub fn is_table_id(content_id: &str) -> bool {
    let lower = content_id.to_ascii_lowercase();
    lower.starts_with("tab") || lower.get(2..).map_or(false, |tail| tail.starts_with("tab"))
}

pub fn is_video_id(content_id: &str) -> bool {
    let lower = content_id.to_ascii_lowercase();
    lower.starts_with("vid") || lower.get(2..).map_or(false, |tail| tail.starts_with("vid"))
}

pub fn is_svg_id(content_id: &str) -> bool {
    let lower = content_id.to_ascii_lowercase();
    lower.starts_with("svg") || lower.get(2..).map_or(false, |tail| tail.starts_with("svg"))
}
