use anyhow::{bail, Result};
use reqwest::Client;
use serde_json::Value;
use std::collections::{HashMap, HashSet};
use std::path::Path;
use tracing::{info, warn};

use super::api::{download_figure, download_table, fetch_question_json, TableResponse};
use super::file_store::{
    collect_question_entries, load_discovery_results, update_question_json, FigureMetadata,
    MediaUpdate, QuestionEntry, TableMetadata,
};
use super::media_ids::{
    classify_content_id, collect_inline_table_nodes, extract_content_ids,
    extract_table_ids_from_tables_content, inline_table_id, ContentIdKind,
};
use super::metadata::{extract_html_text, for_each_metadata_item};
use super::render::{pretty_format_html, render_node};

pub async fn run_media_download(
    client: &Client,
    base_url: &str,
    data_dir: &str,
    discovery_file: &str,
    question_id: Option<&str>,
    download_figures: bool,
    download_tables: bool,
) -> Result<()> {
    let discovery_path = Path::new(discovery_file);
    let discovered_ids = load_discovery_results(discovery_path)?;
    if discovered_ids.is_empty() {
        warn!(
            "No questions found in discovery file: {}",
            discovery_path.display()
        );
    }

    let figure_metadata_by_id = if download_figures {
        load_figure_metadata(client, base_url).await?
    } else {
        HashMap::new()
    };

    let entries = collect_question_entries(data_dir)?;
    let mut entry_map: HashMap<String, QuestionEntry> = HashMap::new();
    for entry in entries {
        entry_map.insert(entry.question_id.clone(), entry);
    }

    let mut targets: Vec<String> = if let Some(qid) = question_id {
        if !discovered_ids.contains(qid) {
            bail!("Question ID not present in discovery file: {}", qid);
        }
        vec![qid.to_string()]
    } else {
        discovered_ids.into_iter().collect()
    };

    targets.sort();
    info!("Processing {} questions for media downloads", targets.len());

    for (idx, qid) in targets.iter().enumerate() {
        if (idx % 25) == 0 && idx > 0 {
            info!("Progress: {}/{}", idx, targets.len());
        }

        let Some(entry) = entry_map.get(qid) else {
            warn!("Question {} not found in data directory; skipping", qid);
            continue;
        };

        if let Err(err) = process_question_entry(
            client,
            base_url,
            entry,
            &figure_metadata_by_id,
            download_figures,
            download_tables,
        )
        .await
        {
            warn!("Media download failed for {}: {}", qid, err);
        }
    }

    Ok(())
}

async fn process_question_entry(
    client: &Client,
    base_url: &str,
    entry: &QuestionEntry,
    figure_metadata_by_id: &HashMap<String, FigureMetadata>,
    download_figures: bool,
    download_tables: bool,
) -> Result<()> {
    if !download_figures && !download_tables {
        return Ok(());
    }

    let question = fetch_question_json(client, base_url, &entry.question_id).await?;
    let update = collect_media_updates(
        client,
        base_url,
        &entry.question_dir,
        &question,
        figure_metadata_by_id,
        download_figures,
        download_tables,
    )
    .await?;

    if update.tables.is_empty()
        && update.images.is_empty()
        && update.videos.is_empty()
        && update.svgs.is_empty()
    {
        return Ok(());
    }

    update_question_json(&entry.json_path, &update)
}

async fn collect_media_updates(
    client: &Client,
    base_url: &str,
    question_dir: &Path,
    question: &Value,
    figure_metadata_by_id: &HashMap<String, FigureMetadata>,
    download_figures: bool,
    download_tables: bool,
) -> Result<MediaUpdate> {
    let mut update = MediaUpdate::default();
    let mut seen_tables = HashSet::new();
    let mut seen_images = HashSet::new();
    let mut seen_figure_metadata = HashSet::new();
    let mut seen_table_metadata = HashSet::new();

    let content_ids = extract_content_ids(question);
    for content_id in content_ids {
        match classify_content_id(&content_id) {
            Some(ContentIdKind::Figure) if download_figures => {
                let path = download_figure(client, base_url, question_dir, &content_id).await?;
                push_unique(&mut update.images, &mut seen_images, path.clone());
                if seen_figure_metadata.insert(content_id.clone()) {
                    let mut metadata = figure_metadata_by_id
                        .get(&content_id)
                        .cloned()
                        .unwrap_or_else(|| fallback_figure_metadata(&content_id));
                    metadata.file = path;
                    update.metadata.figures.push(metadata);
                }
            }
            Some(ContentIdKind::Table) if download_tables => {
                if let Some(download) =
                    download_table(client, base_url, question_dir, &content_id).await?
                {
                    let path = download.path.clone();
                    push_unique(&mut update.tables, &mut seen_tables, Some(path.clone()));
                    if seen_table_metadata.insert(download.table.id.clone()) {
                        let metadata = build_table_metadata(&download.table, Some(path));
                        update.metadata.tables.push(metadata);
                    }
                }
            }
            _ => {}
        }
    }

    if download_tables {
        for table_id in extract_table_ids_from_tables_content(question) {
            if let Some(download) =
                download_table(client, base_url, question_dir, &table_id).await?
            {
                let path = download.path.clone();
                push_unique(&mut update.tables, &mut seen_tables, Some(path.clone()));
                if seen_table_metadata.insert(download.table.id.clone()) {
                    let metadata = build_table_metadata(&download.table, Some(path));
                    update.metadata.tables.push(metadata);
                }
            }
        }

        let inline_tables = extract_inline_tables(question);
        for (index, html) in inline_tables.iter().enumerate() {
            let filename = format!("inline_table_{}.html", index + 1);
            let dest_dir = question_dir.join("tables");
            std::fs::create_dir_all(&dest_dir)?;
            let dest_path = dest_dir.join(&filename);
            if !dest_path.exists() {
                let formatted = pretty_format_html(&html.html);
                std::fs::write(&dest_path, formatted)?;
            }
            let relative = Path::new("tables")
                .join(&filename)
                .to_string_lossy()
                .to_string();
            if seen_tables.insert(relative.clone()) {
                update.tables.push(relative.clone());
            }
            let inline_id = inline_table_id(index);
            if seen_table_metadata.insert(inline_id.clone()) {
                update.metadata.tables.push(TableMetadata {
                    table_id: inline_id,
                    file: Some(relative),
                    title: None,
                    short_title: None,
                    footnotes: Vec::new(),
                    headers: html.headers.clone(),
                });
            }
        }
    }

    Ok(update)
}

fn push_unique(target: &mut Vec<String>, seen: &mut HashSet<String>, value: Option<String>) {
    if let Some(value) = value {
        if seen.insert(value.clone()) {
            target.push(value);
        }
    }
}

fn extract_inline_tables(question: &Value) -> Vec<InlineTable> {
    collect_inline_table_nodes(question)
        .into_iter()
        .map(|table| InlineTable {
            html: render_node(table),
            headers: extract_table_headers(table),
        })
        .collect()
}

struct InlineTable {
    html: String,
    headers: Vec<String>,
}

async fn load_figure_metadata(
    client: &Client,
    base_url: &str,
) -> Result<HashMap<String, FigureMetadata>> {
    let metadata = super::fetch_content_metadata(client, base_url).await?;
    let mut figures_by_id = HashMap::new();

    for_each_metadata_item(&metadata, "figures", |fallback_id, figure| {
        insert_figure_metadata(&mut figures_by_id, fallback_id, figure);
    });

    Ok(figures_by_id)
}

fn insert_figure_metadata(
    figures_by_id: &mut HashMap<String, FigureMetadata>,
    fallback_id: Option<&str>,
    figure: &Value,
) {
    let figure_id = figure
        .get("id")
        .and_then(|v| v.as_str())
        .or(fallback_id)
        .unwrap_or("unknown");

    let extension = figure
        .get("imageInfo")
        .and_then(|info| info.get("extension"))
        .and_then(|ext| ext.as_str())
        .map(|ext| ext.to_ascii_lowercase());

    let title = extract_html_text(figure.get("title"));
    let short_title = extract_html_text(figure.get("shortTitle"));
    let number = figure
        .get("number")
        .and_then(|val| val.as_str())
        .map(|val| val.to_string());
    let footnotes = extract_footnotes(figure.get("footnotes"));

    let width = figure
        .get("imageInfo")
        .and_then(|info| info.get("width"))
        .and_then(|val| val.as_u64())
        .map(|val| val as u32);

    let height = figure
        .get("imageInfo")
        .and_then(|info| info.get("height"))
        .and_then(|val| val.as_u64())
        .map(|val| val as u32);

    figures_by_id.insert(
        figure_id.to_string(),
        FigureMetadata {
            figure_id: figure_id.to_string(),
            file: None,
            title,
            short_title,
            number,
            footnotes,
            extension,
            width,
            height,
        },
    );
}

fn fallback_figure_metadata(figure_id: &str) -> FigureMetadata {
    FigureMetadata {
        figure_id: figure_id.to_string(),
        file: None,
        title: None,
        short_title: None,
        number: None,
        footnotes: Vec::new(),
        extension: None,
        width: None,
        height: None,
    }
}

fn build_table_metadata(table: &TableResponse, file: Option<String>) -> TableMetadata {
    TableMetadata {
        table_id: table.id.clone(),
        file,
        title: extract_html_text(table.title.as_ref()),
        short_title: extract_html_text(table.short_title.as_ref()),
        footnotes: extract_footnotes(table.footnotes.as_ref()),
        headers: extract_table_headers(&table.json_content),
    }
}

fn extract_table_headers(value: &Value) -> Vec<String> {
    let mut headers = Vec::new();
    collect_table_headers(value, &mut headers);
    headers
}

fn collect_table_headers(value: &Value, headers: &mut Vec<String>) {
    match value {
        Value::Object(map) => {
            if let Some(Value::String(tag)) = map.get("tagName") {
                if tag.eq_ignore_ascii_case("th") {
                    let text = extract_text(value);
                    if !text.is_empty() {
                        headers.push(text);
                    }
                    return;
                }
            }

            for child in map.values() {
                collect_table_headers(child, headers);
            }
        }
        Value::Array(items) => {
            for item in items {
                collect_table_headers(item, headers);
            }
        }
        _ => {}
    }
}

fn extract_text(value: &Value) -> String {
    match value {
        Value::String(text) => text.clone(),
        Value::Object(map) => map.get("children").map(extract_text).unwrap_or_default(),
        Value::Array(items) => items.iter().map(extract_text).collect::<Vec<_>>().join(""),
        _ => String::new(),
    }
}

fn extract_footnotes(value: Option<&Value>) -> Vec<String> {
    match value {
        Some(Value::Array(items)) => items
            .iter()
            .filter_map(|item| {
                let rendered = render_value_as_html(item);
                if rendered.is_empty() {
                    None
                } else {
                    Some(rendered)
                }
            })
            .collect(),
        Some(other) => {
            let rendered = render_value_as_html(other);
            if rendered.is_empty() {
                Vec::new()
            } else {
                vec![rendered]
            }
        }
        None => Vec::new(),
    }
}

fn render_value_as_html(value: &Value) -> String {
    match value {
        Value::String(text) => text.clone(),
        Value::Array(_) | Value::Object(_) => render_node(value),
        _ => String::new(),
    }
}
