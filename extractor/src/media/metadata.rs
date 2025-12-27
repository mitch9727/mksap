use serde_json::Value;

#[derive(Clone, Debug, Default)]
pub struct ImageInfo {
    pub extension: Option<String>,
    pub width: Option<u32>,
    pub height: Option<u32>,
}

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

pub fn extract_image_info(value: &Value) -> ImageInfo {
    let mut info = ImageInfo::default();
    let image_info = value.get("imageInfo").and_then(|v| v.as_object());
    if let Some(image_info) = image_info {
        info.extension = image_info
            .get("extension")
            .and_then(|ext| ext.as_str())
            .map(|ext| ext.to_ascii_lowercase());
        info.width = image_info
            .get("width")
            .and_then(|val| val.as_u64())
            .map(|val| val as u32);
        info.height = image_info
            .get("height")
            .and_then(|val| val.as_u64())
            .map(|val| val as u32);
    }
    info
}
