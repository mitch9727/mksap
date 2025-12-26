use anyhow::Result;
use reqwest::Client;
use serde_json::Value;
use std::collections::HashSet;
use std::path::Path;
use tracing::{info, warn};

use crate::api::{download_figure, download_table, fetch_question_json};
use crate::browser::{BrowserMedia, BrowserSession};
use crate::file_store::update_question_json;
use crate::media::svgs::{download_svg, save_inline_svg};
use crate::media::videos::download_video;
use crate::model::{MediaUpdate, QuestionEntry};
use crate::render::{pretty_format_html, render_node};

pub async fn run_media_extraction(
    client: &Client,
    base_url: &str,
    targets: &[QuestionEntry],
    mut browser: Option<BrowserSession>,
    include_videos: bool,
    include_svgs: bool,
) -> Result<()> {
    let total = targets.len();
    for (idx, entry) in targets.iter().enumerate() {
        if idx % 25 == 0 && idx > 0 {
            info!("Progress: {}/{}", idx, total);
        }
        if let Err(err) = process_question_entry(
            client,
            base_url,
            entry,
            browser.as_mut(),
            include_videos,
            include_svgs,
        )
        .await
        {
            warn!(
                "Media extraction failed for {}: {}",
                entry.question_id, err
            );
        }
    }
    Ok(())
}

async fn process_question_entry(
    client: &Client,
    base_url: &str,
    entry: &QuestionEntry,
    browser: Option<&mut BrowserSession>,
    include_videos: bool,
    include_svgs: bool,
) -> Result<()> {
    let question = fetch_question_json(client, base_url, &entry.question_id).await?;
    let content_ids = extract_content_ids(&question);
    let inline_tables = extract_inline_tables(&question);
    if content_ids.is_empty() && inline_tables.is_empty() {
        return Ok(());
    }

    let update = collect_media_updates(
        client,
        base_url,
        &entry.question_id,
        &entry.question_dir,
        content_ids,
        inline_tables,
        browser,
        include_videos,
        include_svgs,
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
    question_id: &str,
    question_dir: &Path,
    content_ids: Vec<String>,
    inline_tables: Vec<String>,
    browser: Option<&mut BrowserSession>,
    include_videos: bool,
    include_svgs: bool,
) -> Result<MediaUpdate> {
    let mut update = MediaUpdate::default();
    let mut seen_tables = HashSet::new();
    let mut seen_images = HashSet::new();
    let mut seen_videos = HashSet::new();
    let mut seen_svgs = HashSet::new();

    let mut wants_videos = Vec::new();
    let mut wants_svgs = Vec::new();

    for content_id in content_ids {
        if is_figure_id(&content_id) {
            push_unique(
                &mut update.images,
                &mut seen_images,
                download_figure(client, base_url, question_dir, &content_id).await?,
            );
            continue;
        }
        if is_table_id(&content_id) {
            push_unique(
                &mut update.tables,
                &mut seen_tables,
                download_table(client, base_url, question_dir, &content_id).await?,
            );
            continue;
        }
        if include_videos && is_video_id(&content_id) {
            wants_videos.push(content_id.clone());
            continue;
        }
        if include_svgs && is_svg_id(&content_id) {
            wants_svgs.push(content_id.clone());
            continue;
        }
    }

    if (!wants_videos.is_empty() || !wants_svgs.is_empty()) && browser.is_none() {
        for vid in wants_videos {
            if seen_videos.insert(vid.clone()) {
                warn!("Found video {} (browser disabled)", vid);
                update.videos.push(vid);
            }
        }
        for svg in wants_svgs {
            if seen_svgs.insert(svg.clone()) {
                warn!("Found svg {} (browser disabled)", svg);
                update.svgs.push(svg);
            }
        }
    }

    if let Some(browser) = browser {
        let want_video_media = include_videos && !wants_videos.is_empty();
        let want_svg_media = include_svgs && !wants_svgs.is_empty();
        if want_video_media || want_svg_media {
            let browser_media =
                browser.extract_media(question_id, want_video_media, want_svg_media).await?;
            apply_browser_media(
                client,
                question_dir,
                browser_media,
                &mut update,
                &mut seen_videos,
                &mut seen_svgs,
            )
            .await?;
        }
    }

    for (index, html) in inline_tables.iter().enumerate() {
        let filename = format!("inline_table_{}.html", index + 1);
        let dest_dir = question_dir.join("tables");
        std::fs::create_dir_all(&dest_dir)?;
        let dest_path = dest_dir.join(&filename);
        let formatted = pretty_format_html(html);
        std::fs::write(&dest_path, formatted)?;
        let relative = Path::new("tables").join(&filename).to_string_lossy().to_string();
        if seen_tables.insert(relative.clone()) {
            update.tables.push(relative);
        }
    }

    Ok(update)
}

async fn apply_browser_media(
    client: &Client,
    question_dir: &Path,
    browser_media: BrowserMedia,
    update: &mut MediaUpdate,
    seen_videos: &mut HashSet<String>,
    seen_svgs: &mut HashSet<String>,
) -> Result<()> {
    for url in browser_media.video_urls {
        if let Some(path) = download_video(client, question_dir, &url).await? {
            if seen_videos.insert(path.clone()) {
                update.videos.push(path);
            }
        }
    }

    for url in browser_media.svg_urls {
        if let Some(path) = download_svg(client, question_dir, &url).await? {
            if seen_svgs.insert(path.clone()) {
                update.svgs.push(path);
            }
        }
    }

    for (index, svg) in browser_media.inline_svgs.iter().enumerate() {
        if let Some(path) = save_inline_svg(question_dir, index, svg)? {
            if seen_svgs.insert(path.clone()) {
                update.svgs.push(path);
            }
        }
    }

    Ok(())
}

fn push_unique(target: &mut Vec<String>, seen: &mut HashSet<String>, value: Option<String>) {
    if let Some(value) = value {
        if seen.insert(value.clone()) {
            target.push(value);
        }
    }
}

fn extract_content_ids(question: &Value) -> Vec<String> {
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

fn extract_inline_tables(question: &Value) -> Vec<String> {
    let mut tables = Vec::new();
    walk_for_inline_tables(question, &mut tables);
    tables
}

fn walk_for_inline_tables(value: &Value, tables: &mut Vec<String>) {
    match value {
        Value::Object(map) => {
            if let Some(Value::String(tag)) = map.get("tagName") {
                if tag.eq_ignore_ascii_case("table") {
                    tables.push(render_node(value));
                    return;
                }
            }
            for v in map.values() {
                walk_for_inline_tables(v, tables);
            }
        }
        Value::Array(items) => {
            for item in items {
                walk_for_inline_tables(item, tables);
            }
        }
        _ => {}
    }
}

fn is_figure_id(content_id: &str) -> bool {
    let lower = content_id.to_ascii_lowercase();
    lower.starts_with("fig") || lower.get(2..).map_or(false, |tail| tail.starts_with("fig"))
}

fn is_table_id(content_id: &str) -> bool {
    let lower = content_id.to_ascii_lowercase();
    lower.starts_with("tab") || lower.get(2..).map_or(false, |tail| tail.starts_with("tab"))
}

fn is_video_id(content_id: &str) -> bool {
    let lower = content_id.to_ascii_lowercase();
    lower.starts_with("vid") || lower.get(2..).map_or(false, |tail| tail.starts_with("vid"))
}

fn is_svg_id(content_id: &str) -> bool {
    let lower = content_id.to_ascii_lowercase();
    lower.starts_with("svg") || lower.get(2..).map_or(false, |tail| tail.starts_with("svg"))
}
