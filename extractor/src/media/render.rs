use serde_json::Value;

pub fn render_table_html(value: &Value) -> String {
    let html = render_node(value);
    pretty_format_html(&html)
}

pub fn render_node(value: &Value) -> String {
    match value {
        Value::String(text) => escape_html(text),
        Value::Array(items) => items.iter().map(render_node).collect::<Vec<_>>().join(""),
        Value::Object(map) => {
            let children = map.get("children").map(render_node).unwrap_or_default();
            if let Some(Value::String(tag_name)) = map.get("tagName") {
                let attrs = render_attrs(map.get("attrs"));
                format!(
                    "<{tag}{attrs}>{children}</{tag}>",
                    tag = tag_name,
                    attrs = attrs,
                    children = children
                )
            } else if let Some(Value::String(node_type)) = map.get("type") {
                if node_type == "p" {
                    format!("<p>{}</p>", children)
                } else {
                    children
                }
            } else {
                children
            }
        }
        _ => String::new(),
    }
}

fn render_attrs(attrs: Option<&Value>) -> String {
    let Some(Value::Object(map)) = attrs else {
        return String::new();
    };

    let mut pairs = Vec::new();
    for (key, value) in map {
        if let Some(val_str) = value.as_str() {
            pairs.push(format!(" {}=\"{}\"", key, escape_html(val_str)));
        }
    }
    pairs.join("")
}

fn escape_html(input: &str) -> String {
    input
        .replace('&', "&amp;")
        .replace('<', "&lt;")
        .replace('>', "&gt;")
        .replace('"', "&quot;")
}

pub fn pretty_format_html(html: &str) -> String {
    let mut output = String::new();
    let mut indent = 0usize;
    let mut i = 0usize;
    let bytes = html.as_bytes();

    while i < bytes.len() {
        if bytes[i] == b'<' {
            let end = html[i..]
                .find('>')
                .map(|offset| i + offset)
                .unwrap_or(bytes.len() - 1);
            let tag = &html[i..=end];

            let (tag_name, is_end, is_self) = parse_tag(tag);
            let is_block = tag_name.as_deref().map(is_block_tag).unwrap_or(false);

            if is_block && is_end {
                indent = indent.saturating_sub(1);
            }

            if is_block {
                if !output.is_empty() {
                    output.push('\n');
                }
                output.push_str(&"  ".repeat(indent));
            }

            output.push_str(tag);

            if is_block && !is_end && !is_self {
                indent += 1;
            }

            i = end + 1;
            continue;
        }

        let next = html[i..]
            .find('<')
            .map(|offset| i + offset)
            .unwrap_or(bytes.len());
        let text = html[i..next].trim();
        if !text.is_empty() {
            if !output.is_empty() {
                output.push('\n');
            }
            output.push_str(&"  ".repeat(indent));
            output.push_str(text);
        }
        i = next;
    }

    output
}

fn parse_tag(tag: &str) -> (Option<String>, bool, bool) {
    if tag.starts_with("<!--") {
        return (None, false, true);
    }
    if tag.starts_with("<!") {
        return (None, false, true);
    }

    let is_end = tag.starts_with("</");
    let is_self = tag.ends_with("/>") || tag.starts_with("<?");

    let name_start = if is_end { 2 } else { 1 };
    let name = tag[name_start..]
        .trim_start()
        .split(|c: char| c == ' ' || c == '>' || c == '/')
        .next()
        .unwrap_or("")
        .to_string();

    if name.is_empty() {
        return (None, is_end, is_self);
    }

    (Some(name), is_end, is_self)
}

fn is_block_tag(tag: &str) -> bool {
    matches!(
        tag,
        "table" | "thead" | "tbody" | "tfoot" | "tr" | "th" | "td" | "caption"
    )
}
