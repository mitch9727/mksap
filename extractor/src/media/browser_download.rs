use anyhow::{bail, Context, Result};
use regex::Regex;
use reqwest::Client;
use serde_json::Value;
use std::collections::{HashMap, HashSet, VecDeque};
use std::path::Path;
use std::time::Duration;
use tracing::{info, warn};

use super::browser::{BrowserMedia, BrowserOptions, BrowserSession};
use super::browser_media;
use super::discovery::{DiscoveryResults, QuestionMedia};
use super::file_store::{
    collect_question_entries, update_question_json, MediaUpdate, SvgMetadata, VideoMetadata,
};
use super::session;

const VIDEO_CLOUDFRONT_BASE: &str = "https://d2chybfyz5ban.cloudfront.net/hashed_figures";

pub async fn run_browser_download(
    client: &Client,
    base_url: &str,
    data_dir: &str,
    discovery_file: &str,
    question_id: Option<&str>,
    download_videos: bool,
    download_svgs: bool,
    webdriver_url: &str,
    headless: bool,
    interactive_login: bool,
    username: Option<String>,
    password: Option<String>,
    login_timeout_secs: u64,
) -> Result<()> {
    if !download_videos && !download_svgs {
        warn!("Browser download requested without videos or svgs enabled.");
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
    for media in results.questions_with_media {
        if (download_videos && !media.videos.is_empty())
            || (download_svgs && !media.svgs.is_empty())
        {
            media_by_id.insert(media.question_id.clone(), media);
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

    let video_metadata_by_id = if download_videos {
        load_video_metadata(client, base_url).await?
    } else {
        HashMap::new()
    };

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
            .extract_media(qid, download_videos, download_svgs)
            .await
            .with_context(|| format!("Failed to extract media from {}", qid))?;

        let caption_map = extract_caption_map(&browser_media.page_html);

        let mut update = MediaUpdate::default();
        let mut seen_video_files = HashSet::new();
        let mut seen_svg_files = HashSet::new();
        let mut seen_video_metadata = HashSet::new();
        let mut seen_svg_metadata = HashSet::new();

        if download_videos {
            let mut urls = dedupe_ordered(browser_media.video_urls.clone());
            if urls.is_empty() {
                let metadata_urls =
                    build_video_urls_from_metadata(&expected_media.videos, &video_metadata_by_id);
                if !metadata_urls.is_empty() {
                    warn!(
                        "{}: using mp4Hash metadata for {} video URLs",
                        qid,
                        metadata_urls.len()
                    );
                    urls = metadata_urls;
                }
            }
            if urls.is_empty() {
                let fallback_urls = collect_video_fallbacks(&browser_media);
                if !fallback_urls.is_empty() {
                    warn!(
                        "{}: no direct video URLs found; trying {} fallback URLs",
                        qid,
                        fallback_urls.len()
                    );
                    urls = fallback_urls;
                } else {
                    warn!("{}: no video URLs detected in DOM or resource logs", qid);
                }
            }
            let expected_video_ids: Vec<String> = expected_media
                .videos
                .iter()
                .map(|video| video.video_id.clone())
                .collect();

            let (assignments, leftovers) =
                assign_ids_to_urls(&expected_video_ids, &urls, &caption_map);

            for assignment in assignments {
                let path = browser_media::videos::download_video(
                    client,
                    &entry.question_dir,
                    &assignment.url,
                )
                .await?;

                push_unique(&mut update.videos, &mut seen_video_files, path.clone());

                if !assignment.id.is_empty() && seen_video_metadata.insert(assignment.id.clone()) {
                    let mut metadata = video_metadata_by_id
                        .get(&assignment.id)
                        .cloned()
                        .unwrap_or_else(|| fallback_video_metadata(&assignment.id));
                    metadata.file = path;
                    if metadata.caption.is_none() {
                        metadata.caption = assignment.caption.clone();
                    }
                    if metadata.title.is_none() {
                        metadata.title = assignment.caption;
                    }
                    update.metadata.videos.push(metadata);
                }
            }

            for leftover_id in leftovers {
                if seen_video_metadata.insert(leftover_id.clone()) {
                    update
                        .metadata
                        .videos
                        .push(fallback_video_metadata(&leftover_id));
                }
            }
        }

        if download_svgs {
            let urls = dedupe_ordered(browser_media.svg_urls);
            let expected_svg_ids: Vec<String> = expected_media
                .svgs
                .iter()
                .map(|svg| svg.svg_id.clone())
                .collect();

            let (assignments, leftovers) =
                assign_ids_to_urls(&expected_svg_ids, &urls, &caption_map);
            let mut remaining_ids: VecDeque<String> = leftovers.into();

            for assignment in assignments {
                let path =
                    browser_media::svgs::download_svg(client, &entry.question_dir, &assignment.url)
                        .await?;

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
                let path =
                    browser_media::svgs::save_inline_svg(&entry.question_dir, index, svg_markup)?;

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

        if update.videos.is_empty() && update.svgs.is_empty() && update.metadata.is_empty() {
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

fn dedupe_ordered(values: Vec<String>) -> Vec<String> {
    let mut seen = HashSet::new();
    values
        .into_iter()
        .filter(|value| seen.insert(value.clone()))
        .collect()
}

fn push_unique(target: &mut Vec<String>, seen: &mut HashSet<String>, value: Option<String>) {
    if let Some(value) = value {
        if seen.insert(value.clone()) {
            target.push(value);
        }
    }
}

fn build_video_urls_from_metadata(
    videos: &[super::discovery::VideoReference],
    metadata: &HashMap<String, VideoMetadata>,
) -> Vec<String> {
    let mut urls = Vec::new();
    for video in videos {
        if let Some(meta) = metadata.get(&video.video_id) {
            if let Some(hash) = meta.mp4_hash.as_deref() {
                urls.push(format!(
                    "{}/{}.{}.mp4",
                    VIDEO_CLOUDFRONT_BASE, video.video_id, hash
                ));
            }
        }
    }
    dedupe_ordered(urls)
}

fn collect_video_fallbacks(media: &BrowserMedia) -> Vec<String> {
    let mut urls = Vec::new();
    urls.extend(
        media
            .performance_urls
            .iter()
            .filter(|url| is_video_candidate(url))
            .cloned(),
    );
    urls.extend(
        media
            .dom_urls
            .iter()
            .filter(|url| is_video_candidate(url))
            .cloned(),
    );
    urls.extend(
        media
            .resource_urls
            .iter()
            .filter(|url| is_video_candidate(url))
            .cloned(),
    );
    dedupe_ordered(urls)
}

fn is_video_candidate(url: &str) -> bool {
    let lower = url.to_ascii_lowercase();
    if lower.starts_with("blob:") {
        return false;
    }

    let has_video_hint = lower.contains("video") || lower.contains("vid");
    if !has_video_hint {
        return false;
    }

    let excluded_exts = [
        ".js", ".css", ".png", ".jpg", ".jpeg", ".svg", ".gif", ".json",
    ];

    !excluded_exts.iter().any(|ext| lower.contains(ext))
}

fn fallback_video_metadata(video_id: &str) -> VideoMetadata {
    VideoMetadata {
        video_id: video_id.to_string(),
        file: None,
        title: None,
        short_title: None,
        width: None,
        height: None,
        caption: None,
        mp4_hash: None,
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

async fn load_video_metadata(
    client: &Client,
    base_url: &str,
) -> Result<HashMap<String, VideoMetadata>> {
    let url = format!("{}/api/content_metadata.json", base_url);
    let response = client
        .get(&url)
        .send()
        .await
        .context("Failed to fetch content metadata")?;

    if !response.status().is_success() {
        anyhow::bail!(
            "Content metadata request failed: HTTP {}",
            response.status()
        );
    }

    let metadata: Value = response.json().await.context("Failed to parse metadata")?;
    let mut videos_by_id = HashMap::new();

    let videos_value = metadata.get("videos");
    match videos_value {
        Some(Value::Array(videos)) => {
            for video in videos {
                insert_video_metadata(&mut videos_by_id, None, video);
            }
        }
        Some(Value::Object(videos)) => {
            for (key, video) in videos {
                insert_video_metadata(&mut videos_by_id, Some(key.as_str()), video);
            }
        }
        _ => {}
    }

    Ok(videos_by_id)
}

async fn load_svg_metadata(
    client: &Client,
    base_url: &str,
) -> Result<HashMap<String, SvgMetadata>> {
    let url = format!("{}/api/content_metadata.json", base_url);
    let response = client
        .get(&url)
        .send()
        .await
        .context("Failed to fetch content metadata")?;

    if !response.status().is_success() {
        anyhow::bail!(
            "Content metadata request failed: HTTP {}",
            response.status()
        );
    }

    let metadata: Value = response.json().await.context("Failed to parse metadata")?;
    let mut svgs_by_id = HashMap::new();

    let svgs_value = metadata.get("svgs");
    match svgs_value {
        Some(Value::Array(svgs)) => {
            for svg in svgs {
                insert_svg_metadata(&mut svgs_by_id, None, svg);
            }
        }
        Some(Value::Object(svgs)) => {
            for (key, svg) in svgs {
                insert_svg_metadata(&mut svgs_by_id, Some(key.as_str()), svg);
            }
        }
        _ => {}
    }

    Ok(svgs_by_id)
}

fn insert_video_metadata(
    videos_by_id: &mut HashMap<String, VideoMetadata>,
    fallback_id: Option<&str>,
    video: &Value,
) {
    let video_id = video
        .get("id")
        .and_then(|v| v.as_str())
        .or(fallback_id)
        .unwrap_or("unknown");

    let title = extract_html_text(video.get("title"));
    let short_title = extract_html_text(video.get("shortTitle"));
    let caption = extract_html_text(video.get("caption"));
    let (width, height) = extract_dimensions(video);
    let mp4_hash = video
        .get("mp4Hash")
        .and_then(|v| v.as_str())
        .map(|v| v.to_string());

    videos_by_id.insert(
        video_id.to_string(),
        VideoMetadata {
            video_id: video_id.to_string(),
            file: None,
            title,
            short_title,
            width,
            height,
            caption,
            mp4_hash,
        },
    );
}

fn insert_svg_metadata(
    svgs_by_id: &mut HashMap<String, SvgMetadata>,
    fallback_id: Option<&str>,
    svg: &Value,
) {
    let svg_id = svg
        .get("id")
        .and_then(|v| v.as_str())
        .or(fallback_id)
        .unwrap_or("unknown");

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

fn extract_dimensions(value: &Value) -> (Option<u32>, Option<u32>) {
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

fn extract_html_text(value: Option<&Value>) -> Option<String> {
    match value {
        Some(Value::String(text)) => Some(text.clone()),
        Some(Value::Object(obj)) => obj
            .get("__html")
            .and_then(|val| val.as_str())
            .map(|text| text.to_string()),
        _ => None,
    }
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

        for url in extract_video_urls(block) {
            captions.entry(url).or_insert_with(|| caption.clone());
        }
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

fn extract_video_urls(html: &str) -> Vec<String> {
    let mut urls = Vec::new();
    let re = Regex::new(r#"src="([^"]+\.mp4[^"]*)""#).unwrap();
    for cap in re.captures_iter(html) {
        urls.push(cap[1].to_string());
    }
    urls
}

fn extract_svg_urls(html: &str) -> Vec<String> {
    let mut urls = Vec::new();
    let re = Regex::new(r#"src="([^"]+\.svg[^"]*)""#).unwrap();
    for cap in re.captures_iter(html) {
        urls.push(cap[1].to_string());
    }
    urls
}
