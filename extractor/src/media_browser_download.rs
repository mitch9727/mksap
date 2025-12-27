use anyhow::{bail, Context, Result};
use regex::Regex;
use reqwest::Client;
use serde_json::Value;
use std::collections::{HashMap, HashSet, VecDeque};
use std::path::Path;
use std::time::Duration;
use tracing::{info, warn};

use super::browser::{dedupe_urls, extract_svg_urls, BrowserOptions, BrowserSession};
use super::discovery::{DiscoveryResults, QuestionMedia};
use super::file_store::{collect_question_entries, update_question_json, MediaUpdate, SvgMetadata};
use super::metadata::{extract_html_text, for_each_metadata_item, resolve_metadata_id};
use super::session;

pub async fn run_browser_download(
    client: &Client,
    base_url: &str,
    data_dir: &str,
    discovery_file: &str,
    question_id: Option<&str>,
    download_svgs: bool,
    webdriver_url: &str,
    headless: bool,
    interactive_login: bool,
    username: Option<String>,
    password: Option<String>,
    login_timeout_secs: u64,
) -> Result<()> {
    if !download_svgs {
        warn!("Browser download requested without SVGs enabled.");
        return Ok(());
    }

    let discovery_path = Path::new(discovery_file);
    let results = DiscoveryResults::load_from_file(discovery_path).with_context(|| {
        format!(
            "Failed to read discovery results from {}",
            discovery_path.display()
        )
    })?;

    let mut media_by_id: HashMap<String, QuestionMedia> = HashMap::new();
    for (question_id, media) in results.questions {
        if download_svgs && !media.svgs.is_empty() {
            media_by_id.insert(question_id, media);
        }
    }

    if media_by_id.is_empty() {
        warn!(
            "No questions with requested media types found in {}",
            discovery_path.display()
        );
        return Ok(());
    }

    let entries = collect_question_entries(data_dir)?;
    let mut entry_map = HashMap::new();
    for entry in entries {
        entry_map.insert(entry.question_id.clone(), entry);
    }

    let mut targets: Vec<String> = if let Some(qid) = question_id {
        if !media_by_id.contains_key(qid) {
            bail!("Question ID not present in discovery file: {}", qid);
        }
        vec![qid.to_string()]
    } else {
        media_by_id.keys().cloned().collect()
    };

    targets.sort();
    info!(
        "Processing {} questions for browser media downloads",
        targets.len()
    );

    let svg_metadata_by_id = if download_svgs {
        load_svg_metadata(client, base_url).await?
    } else {
        HashMap::new()
    };

    let session_cookie = session::load_session_cookie();
    if session_cookie.is_none() && !interactive_login {
        warn!("No session cookie found; set MKSAP_SESSION or enable --interactive-login.");
    }

    let options = BrowserOptions {
        base_url: base_url.to_string(),
        webdriver_url: webdriver_url.to_string(),
        headless,
        interactive_login,
        username,
        password,
        login_timeout: Duration::from_secs(login_timeout_secs),
        session_cookie,
    };

    let browser = BrowserSession::connect(&options).await?;
    browser.ensure_login(&options).await?;

    for (idx, qid) in targets.iter().enumerate() {
        if idx > 0 && (idx % 10) == 0 {
            info!("Progress: {}/{}", idx, targets.len());
        }

        let Some(entry) = entry_map.get(qid) else {
            warn!("Question {} not found in data directory; skipping", qid);
            continue;
        };

        let Some(expected_media) = media_by_id.get(qid) else {
            continue;
        };

        let browser_media = browser
            .extract_media(qid, download_svgs)
            .await
            .with_context(|| format!("Failed to extract media from {}", qid))?;

        let caption_map = extract_caption_map(&browser_media.page_html);

        let mut update = MediaUpdate::default();
        let mut seen_svg_files = HashSet::new();
        let mut seen_svg_metadata = HashSet::new();

        if download_svgs {
            let urls = dedupe_urls(browser_media.svg_urls);
            let expected_svg_ids: Vec<String> = expected_media
                .svgs
                .iter()
                .map(|svg| svg.svg_id.clone())
                .collect();

            let (assignments, leftovers) =
                assign_ids_to_urls(&expected_svg_ids, &urls, &caption_map);
            let mut remaining_ids: VecDeque<String> = leftovers.into();

            for assignment in assignments {
                let path = download_svg(client, &entry.question_dir, &assignment.url).await?;

                push_unique(&mut update.svgs, &mut seen_svg_files, path.clone());

                if !assignment.id.is_empty() && seen_svg_metadata.insert(assignment.id.clone()) {
                    let mut metadata = svg_metadata_by_id
                        .get(&assignment.id)
                        .cloned()
                        .unwrap_or_else(|| fallback_svg_metadata(&assignment.id));
                    metadata.file = path;
                    if metadata.caption.is_none() {
                        metadata.caption = assignment.caption.clone();
                    }
                    if metadata.title.is_none() {
                        metadata.title = assignment.caption;
                    }
                    update.metadata.svgs.push(metadata);
                }
            }

            for (index, svg_markup) in browser_media.inline_svgs.iter().enumerate() {
                let path = save_inline_svg(&entry.question_dir, index, svg_markup)?;

                push_unique(&mut update.svgs, &mut seen_svg_files, path.clone());

                let svg_id = remaining_ids
                    .pop_front()
                    .unwrap_or_else(|| format!("inline_svg_{}", index + 1));

                if seen_svg_metadata.insert(svg_id.clone()) {
                    let mut metadata = svg_metadata_by_id
                        .get(&svg_id)
                        .cloned()
                        .unwrap_or_else(|| fallback_svg_metadata(&svg_id));
                    metadata.file = path;
                    if metadata.title.is_none() {
                        metadata.title = extract_inline_svg_title(svg_markup);
                    }
                    update.metadata.svgs.push(metadata);
                }
            }

            for leftover_id in remaining_ids {
                if seen_svg_metadata.insert(leftover_id.clone()) {
                    update
                        .metadata
                        .svgs
                        .push(fallback_svg_metadata(&leftover_id));
                }
            }
        }

        if update.svgs.is_empty() && update.metadata.is_empty() {
            continue;
        }

        if let Err(err) = update_question_json(&entry.json_path, &update) {
            warn!("Failed to update {}: {}", qid, err);
        }
    }

    Ok(())
}

struct AssignedUrl {
    id: String,
    url: String,
    caption: Option<String>,
}

fn assign_ids_to_urls(
    ids: &[String],
    urls: &[String],
    caption_map: &HashMap<String, String>,
) -> (Vec<AssignedUrl>, Vec<String>) {
    let mut remaining: Vec<String> = ids.to_vec();
    let mut assignments = Vec::new();

    for url in urls {
        let mut matched_index = None;
        for (idx, id) in remaining.iter().enumerate() {
            if url.contains(id) {
                matched_index = Some(idx);
                break;
            }
        }

        let id = if let Some(idx) = matched_index {
            remaining.remove(idx)
        } else {
            String::new()
        };

        let caption = caption_map.get(url).cloned();
        assignments.push(AssignedUrl {
            id,
            url: url.clone(),
            caption,
        });
    }

    let mut remaining_iter = remaining.into_iter();
    for assignment in assignments.iter_mut() {
        if assignment.id.is_empty() {
            if let Some(next_id) = remaining_iter.next() {
                assignment.id = next_id;
            } else {
                assignment.id = derive_media_id_from_url(&assignment.url);
            }
        }
    }

    let leftovers = remaining_iter.collect();
    (assignments, leftovers)
}

fn derive_media_id_from_url(url: &str) -> String {
    let trimmed = url.split('?').next().unwrap_or(url);
    let filename = trimmed.rsplit('/').next().unwrap_or("media");
    filename.split('.').next().unwrap_or("media").to_string()
}

fn push_unique(target: &mut Vec<String>, seen: &mut HashSet<String>, value: Option<String>) {
    if let Some(value) = value {
        if seen.insert(value.clone()) {
            target.push(value);
        }
    }
}

fn fallback_svg_metadata(svg_id: &str) -> SvgMetadata {
    SvgMetadata {
        svg_id: svg_id.to_string(),
        file: None,
        title: None,
        caption: None,
    }
}

async fn load_svg_metadata(
    client: &Client,
    base_url: &str,
) -> Result<HashMap<String, SvgMetadata>> {
    let metadata = super::fetch_content_metadata(client, base_url).await?;
    let mut svgs_by_id = HashMap::new();

    for_each_metadata_item(&metadata, "svgs", |fallback_id, svg| {
        insert_svg_metadata(&mut svgs_by_id, fallback_id, svg);
    });

    Ok(svgs_by_id)
}

fn insert_svg_metadata(
    svgs_by_id: &mut HashMap<String, SvgMetadata>,
    fallback_id: Option<&str>,
    svg: &Value,
) {
    let svg_id = resolve_metadata_id(svg, fallback_id);

    let title = extract_html_text(svg.get("title"));
    let caption = extract_html_text(svg.get("caption"));

    svgs_by_id.insert(
        svg_id.to_string(),
        SvgMetadata {
            svg_id: svg_id.to_string(),
            file: None,
            title,
            caption,
        },
    );
}

fn extract_inline_svg_title(svg: &str) -> Option<String> {
    let title_re = Regex::new(r"(?s)<title[^>]*>(.*?)</title>").unwrap();
    if let Some(capture) = title_re.captures(svg) {
        let title = capture.get(1).map(|m| m.as_str().trim()).unwrap_or("");
        if !title.is_empty() {
            return Some(title.to_string());
        }
    }

    let desc_re = Regex::new(r"(?s)<desc[^>]*>(.*?)</desc>").unwrap();
    if let Some(capture) = desc_re.captures(svg) {
        let desc = capture.get(1).map(|m| m.as_str().trim()).unwrap_or("");
        if !desc.is_empty() {
            return Some(desc.to_string());
        }
    }

    None
}

fn extract_caption_map(html: &str) -> HashMap<String, String> {
    let mut captions = HashMap::new();
    let figure_re = Regex::new(r"(?s)<figure\b.*?</figure>").unwrap();

    for cap in figure_re.captures_iter(html) {
        let block = cap.get(0).map(|m| m.as_str()).unwrap_or("");
        let caption = match extract_figcaption(block) {
            Some(text) => text,
            None => continue,
        };

        for url in extract_svg_urls(block) {
            captions.entry(url).or_insert_with(|| caption.clone());
        }
    }

    captions
}

fn extract_figcaption(block: &str) -> Option<String> {
    let caption_re = Regex::new(r"(?s)<figcaption[^>]*>(.*?)</figcaption>").unwrap();
    let caption = caption_re
        .captures(block)
        .and_then(|cap| cap.get(1))
        .map(|m| m.as_str().trim().to_string())?;

    if caption.is_empty() {
        None
    } else {
        Some(caption)
    }
}

async fn download_svg(client: &Client, question_dir: &Path, url: &str) -> Result<Option<String>> {
    let filename = filename_from_url(url);
    let dest_dir = question_dir.join("svgs");
    std::fs::create_dir_all(&dest_dir)?;
    let dest_path = dest_dir.join(&filename);

    if !dest_path.exists() {
        let bytes = client
            .get(url)
            .send()
            .await?
            .error_for_status()?
            .bytes()
            .await?;
        std::fs::write(&dest_path, bytes)?;
    }

    Ok(Some(relative_path("svgs", &filename)))
}

fn save_inline_svg(question_dir: &Path, index: usize, svg: &str) -> Result<Option<String>> {
    let filename = format!("inline_svg_{}.svg", index + 1);
    let dest_dir = question_dir.join("svgs");
    std::fs::create_dir_all(&dest_dir)?;
    let dest_path = dest_dir.join(&filename);
    if !dest_path.exists() {
        std::fs::write(&dest_path, svg)?;
    }
    Ok(Some(relative_path("svgs", &filename)))
}

fn filename_from_url(url: &str) -> String {
    let trimmed = url.split('?').next().unwrap_or(url);
    let name = trimmed
        .rsplit('/')
        .next()
        .filter(|part| !part.is_empty())
        .unwrap_or("media.bin");
    name.to_string()
}

fn relative_path(dir: &str, filename: &str) -> String {
    Path::new(dir).join(filename).to_string_lossy().to_string()
}
