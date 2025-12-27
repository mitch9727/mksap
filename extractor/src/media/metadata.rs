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

pub fn extract_dimensions(value: &Value) -> (Option<u32>, Option<u32>) {
    let mut width = None;
    let mut height = None;

    if let Some(info) = value.get("videoInfo").and_then(|v| v.as_object()) {
        width = info.get("width").and_then(|v| v.as_u64()).map(|v| v as u32);
        height = info
            .get("height")
            .and_then(|v| v.as_u64())
            .map(|v| v as u32);
    }

    if width.is_none() || height.is_none() {
        if let Some(info) = value.get("imageInfo").and_then(|v| v.as_object()) {
            width = width.or_else(|| info.get("width").and_then(|v| v.as_u64()).map(|v| v as u32));
            height = height.or_else(|| {
                info.get("height")
                    .and_then(|v| v.as_u64())
                    .map(|v| v as u32)
            });
        }
    }

    if width.is_none() || height.is_none() {
        if let Some(info) = value.get("dimensions").and_then(|v| v.as_object()) {
            width = width.or_else(|| info.get("width").and_then(|v| v.as_u64()).map(|v| v as u32));
            height = height.or_else(|| {
                info.get("height")
                    .and_then(|v| v.as_u64())
                    .map(|v| v as u32)
            });
        }
    }

    if width.is_none() || height.is_none() {
        width = width.or_else(|| {
            value
                .get("width")
                .and_then(|v| v.as_u64())
                .map(|v| v as u32)
        });
        height = height.or_else(|| {
            value
                .get("height")
                .and_then(|v| v.as_u64())
                .map(|v| v as u32)
        });
    }

    (width, height)
}
