use serde_json::Value;
use std::collections::HashSet;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum ContentIdKind {
    Figure,
    Table,
    Video,
    Svg,
}

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

pub fn collect_inline_table_nodes(value: &Value) -> Vec<&Value> {
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

fn matches_prefix(content_id: &str, prefixes: &[&str]) -> bool {
    let lower = content_id.to_ascii_lowercase();
    prefixes.iter().any(|prefix| {
        lower.starts_with(prefix) || lower.get(2..).is_some_and(|tail| tail.starts_with(prefix))
    })
}

pub fn is_figure_id(content_id: &str) -> bool {
    matches_prefix(content_id, &["fig"])
}

pub fn is_table_id(content_id: &str) -> bool {
    matches_prefix(content_id, &["tab"])
}

pub fn is_video_id(content_id: &str) -> bool {
    matches_prefix(content_id, &["vid"])
}

pub fn is_svg_id(content_id: &str) -> bool {
    matches_prefix(content_id, &["svg"])
}

pub fn classify_content_id(content_id: &str) -> Option<ContentIdKind> {
    if is_figure_id(content_id) {
        return Some(ContentIdKind::Figure);
    }
    if is_table_id(content_id) {
        return Some(ContentIdKind::Table);
    }
    if is_video_id(content_id) {
        return Some(ContentIdKind::Video);
    }
    if is_svg_id(content_id) {
        return Some(ContentIdKind::Svg);
    }
    None
}

pub fn inline_table_id(index: usize) -> String {
    format!("inline_table_{}", index + 1)
}
