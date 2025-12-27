use serde_json::Value;

pub fn for_each_metadata_item<'a, F>(metadata: &'a Value, key: &str, mut f: F)
where
    F: FnMut(Option<&'a str>, &'a Value),
{
    match metadata.get(key) {
        Some(Value::Array(items)) => {
            for item in items {
                f(None, item);
            }
        }
        Some(Value::Object(items)) => {
            for (key, item) in items {
                f(Some(key.as_str()), item);
            }
        }
        _ => {}
    }
}

pub fn extract_html_text(value: Option<&Value>) -> Option<String> {
    match value {
        Some(Value::String(text)) => Some(text.clone()),
        Some(Value::Object(obj)) => obj
            .get("__html")
            .and_then(|val| val.as_str())
            .map(|text| text.to_string()),
        _ => None,
    }
}
