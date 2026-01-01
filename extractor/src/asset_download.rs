use anyhow::Result;
use reqwest::Client;
use serde_json::Value;
use std::collections::{HashMap, HashSet};
use std::path::Path;
use tracing::{info, warn};

use super::asset_api::{download_figure, fetch_question_json, fetch_table, TableResponse};
use super::asset_metadata::{extract_html_text, for_each_figure_snapshot};
use super::asset_store::{
    collect_question_entry_map, load_discovery_results, select_targets, update_question_json,
    FigureMetadata, MediaUpdate, QuestionEntry, TableMetadata,
};
use super::content_ids::{
    classify_content_id, collect_inline_table_nodes, extract_content_ids,
    extract_table_ids_from_tables_content, inline_table_id, ContentIdKind,
};
use super::table_render::{pretty_format_html, render_node, render_table_html};

pub async fn run_media_download(
    client: &Client,
    base_url: &str,
    data_dir: &str,
    discovery_file: &str,
    question_id: Option<&str>,
    download_figures: bool,
    download_tables: bool,
) -> Result<()> {
    let discovered_ids = if question_id.is_none() {
        let discovery_path = Path::new(discovery_file);
        let discovered_ids = load_discovery_results(discovery_path)?;
        if discovered_ids.is_empty() {
            warn!(
                "No questions found in discovery file: {}",
                discovery_path.display()
            );
        }
        discovered_ids
    } else {
        HashSet::new()
    };

    let figure_metadata_by_id = if download_figures {
        load_figure_metadata(client, base_url).await?
    } else {
        HashMap::new()
    };

    let entry_map = collect_question_entry_map(data_dir)?;
    let targets = if let Some(question_id) = question_id {
        vec![question_id.to_string()]
    } else {
        select_targets(None, &discovered_ids, "discovery file")?
    };
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
    let mut table_html_index = HashMap::new();

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
                if let Some(table) = fetch_table(client, base_url, &content_id).await? {
                    let html = render_table_html(&table.json_content);
                    let filename = format!("{}.html", table.id);
                    let path =
                        store_table_html(question_dir, &filename, &html, &mut table_html_index)?;
                    push_unique(&mut update.tables, &mut seen_tables, Some(path.clone()));
                    if seen_table_metadata.insert(table.id.clone()) {
                        let metadata = build_table_metadata(&table, Some(path));
                        update.metadata.tables.push(metadata);
                    }
                }
            }
            _ => {}
        }
    }

    if download_tables {
        for table_id in extract_table_ids_from_tables_content(question) {
            if let Some(table) = fetch_table(client, base_url, &table_id).await? {
                let html = render_table_html(&table.json_content);
                let filename = format!("{}.html", table.id);
                let path = store_table_html(question_dir, &filename, &html, &mut table_html_index)?;
                push_unique(&mut update.tables, &mut seen_tables, Some(path.clone()));
                if seen_table_metadata.insert(table.id.clone()) {
                    let metadata = build_table_metadata(&table, Some(path));
                    update.metadata.tables.push(metadata);
                }
            }
        }

        let inline_tables = extract_inline_tables(question);
        for (index, html) in inline_tables.iter().enumerate() {
            let filename = format!("inline_table_{}.html", index + 1);
            let formatted = pretty_format_html(&html.html);
            let relative =
                store_table_html(question_dir, &filename, &formatted, &mut table_html_index)?;
            if seen_tables.insert(relative.clone()) {
                update.tables.push(relative.clone());
            }
            let inline_id = inline_table_id(index);
            if seen_table_metadata.insert(inline_id.clone()) {
                update.metadata.tables.push(TableMetadata {
                    table_id: inline_id,
                    file: Some(relative.clone()),
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

fn store_table_html(
    question_dir: &Path,
    filename: &str,
    html: &str,
    table_html_index: &mut HashMap<String, String>,
) -> Result<String> {
    if let Some(existing) = table_html_index.get(html) {
        return Ok(existing.clone());
    }

    let dest_dir = question_dir.join("tables");
    std::fs::create_dir_all(&dest_dir)?;
    let dest_path = dest_dir.join(filename);
    if !dest_path.exists() {
        std::fs::write(&dest_path, html)?;
    }

    let relative = Path::new("tables")
        .join(filename)
        .to_string_lossy()
        .to_string();
    table_html_index.insert(html.to_string(), relative.clone());
    Ok(relative)
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

    for_each_figure_snapshot(&metadata, |figure, snapshot| {
        let extension = snapshot.image_info.extension;
        let footnotes = extract_footnotes(figure.get("footnotes"));

        let width = snapshot.image_info.width;
        let height = snapshot.image_info.height;

        figures_by_id.insert(
            snapshot.figure_id.clone(),
            FigureMetadata {
                figure_id: snapshot.figure_id,
                file: None,
                title: snapshot.title,
                short_title: snapshot.short_title,
                number: snapshot.number,
                footnotes,
                extension,
                width,
                height,
            },
        );
    });

    Ok(figures_by_id)
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
