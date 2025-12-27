use serde_json::Value;

#[derive(Clone, Debug, Default)]
pub struct ImageInfo {
    pub extension: Option<String>,
    pub width: Option<u32>,
    pub height: Option<u32>,
}

#[derive(Clone, Debug)]
pub struct FigureSnapshot {
    pub figure_id: String,
    pub title: Option<String>,
    pub short_title: Option<String>,
    pub number: Option<String>,
    pub image_info: ImageInfo,
}

pub fn resolve_metadata_id<'a>(value: &'a Value, fallback_id: Option<&'a str>) -> &'a str {
    value
        .get("id")
        .and_then(|v| v.as_str())
        .or(fallback_id)
        .unwrap_or("unknown")
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

pub fn parse_figure_snapshot(value: &Value, fallback_id: Option<&str>) -> FigureSnapshot {
    FigureSnapshot {
        figure_id: resolve_metadata_id(value, fallback_id).to_string(),
        title: extract_html_text(value.get("title")),
        short_title: extract_html_text(value.get("shortTitle")),
        number: value
            .get("number")
            .and_then(|val| val.as_str())
            .map(|val| val.to_string()),
        image_info: extract_image_info(value),
    }
}

pub fn for_each_figure_snapshot<F>(metadata: &Value, mut f: F)
where
    F: FnMut(&Value, FigureSnapshot),
{
    for_each_metadata_item(metadata, "figures", |fallback_id, figure| {
        let snapshot = parse_figure_snapshot(figure, fallback_id);
        f(figure, snapshot);
    });
}
