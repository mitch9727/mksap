use anyhow::{Context, Result};
use regex::Regex;
use reqwest::Client as HttpClient;
use serde_json::{json, Value};
use std::collections::{HashMap, HashSet};
use std::time::{Duration, Instant};
use thirtyfour::common::capabilities::desiredcapabilities::CapabilitiesHelper;
use thirtyfour::prelude::*;
use tracing::{info, warn};

use crate::session;

#[derive(Clone, Debug)]
pub struct BrowserOptions {
    pub base_url: String,
    pub webdriver_url: String,
    pub headless: bool,
    pub interactive_login: bool,
    pub username: Option<String>,
    pub password: Option<String>,
    pub login_timeout: Duration,
    pub session_cookie: Option<String>,
}

#[derive(Default, Debug)]
pub struct BrowserMedia {
    pub video_urls: Vec<String>,
    pub svg_urls: Vec<String>,
    pub inline_svgs: Vec<String>,
    pub page_html: String,
    pub dom_urls: Vec<String>,
    pub resource_urls: Vec<String>,
    pub performance_urls: Vec<String>,
}

pub struct BrowserSession {
    driver: WebDriver,
    base_url: String,
    webdriver_url: String,
    log_client: HttpClient,
}

impl BrowserSession {
    pub async fn connect(options: &BrowserOptions) -> Result<Self> {
        let mut caps = DesiredCapabilities::chrome();
        if options.headless {
            caps.add_chrome_arg("--headless=new")?;
        }
        caps.add_chrome_arg("--disable-gpu")?;
        caps.add_chrome_arg("--window-size=1280,900")?;
        caps.add("goog:loggingPrefs", json!({"performance": "ALL"}))?;
        caps.add_chrome_option(
            "perfLoggingPrefs",
            json!({"enableNetwork": true, "enablePage": false}),
        )?;
        let driver = WebDriver::new(&options.webdriver_url, caps)
            .await
            .with_context(|| format!("Failed to connect to {}", options.webdriver_url))?;
        driver
            .set_implicit_wait_timeout(Duration::from_secs(2))
            .await?;

        let session = BrowserSession {
            driver,
            base_url: options.base_url.clone(),
            webdriver_url: options.webdriver_url.clone(),
            log_client: HttpClient::new(),
        };

        if let Some(cookie) = options.session_cookie.as_ref() {
            session.inject_session_cookie(cookie).await.ok();
        }

        Ok(session)
    }

    pub async fn ensure_login(&self, options: &BrowserOptions) -> Result<()> {
        if self.has_session_cookie().await? {
            return Ok(());
        }

        if !options.interactive_login {
            return Ok(());
        }

        info!("Opening browser for MKSAP login...");
        self.driver.goto(&options.base_url).await?;

        if let Some(username) = options.username.as_ref() {
            self.try_fill(
                "input[type='email'], input[name*='email'], input[id*='email']",
                username,
            )
            .await;
        }
        if let Some(password) = options.password.as_ref() {
            self.try_fill(
                "input[type='password'], input[name*='password'], input[id*='password']",
                password,
            )
            .await;
            let _ = self.try_submit_password().await;
        }

        info!("Waiting for login session cookie...");
        if let Some(cookie) = self.wait_for_session_cookie(options.login_timeout).await? {
            session::save_session_cookie(&cookie)?;
            info!("Saved session cookie to ~/.mksap_session");
        } else {
            warn!("Login timeout; session cookie not detected.");
        }

        Ok(())
    }

    pub async fn extract_media(
        &self,
        question_id: &str,
        want_videos: bool,
        want_svgs: bool,
    ) -> Result<BrowserMedia> {
        let mut media = BrowserMedia::default();
        let question_url = format!(
            "{}/app/question-bank/questions/{}",
            self.base_url, question_id
        );

        let _ = self.drain_performance_logs().await;
        self.driver.goto(&question_url).await?;
        tokio::time::sleep(Duration::from_secs(5)).await;

        let html = self.driver.source().await?;
        media.page_html = html.clone();
        let dom_urls = self.collect_dom_urls().await.unwrap_or_default();
        let resource_urls = self.collect_resource_urls().await.unwrap_or_default();
        let mut performance_capture = self
            .collect_performance_video_urls(Duration::from_secs(4))
            .await
            .unwrap_or_default();
        let mut performance_urls = performance_capture.urls.clone();
        let mut performance_entries = performance_capture.entry_count;
        let mut performance_methods = performance_capture.methods.clone();
        let mut performance_candidates = performance_capture.candidates.clone();
        media.dom_urls = dom_urls.clone();
        media.resource_urls = resource_urls.clone();
        media.performance_urls = performance_urls.clone();
        if want_videos {
            let mut urls = extract_video_urls(&html);
            urls.extend(filter_urls(&dom_urls, |url| is_video_url(url)));
            urls.extend(filter_urls(&resource_urls, |url| is_video_url(url)));
            urls.extend(performance_urls.clone());
            media.video_urls = dedupe_urls(urls);
        }
        if want_svgs {
            let mut urls = extract_svg_urls(&html);
            urls.extend(filter_urls(&dom_urls, |url| is_svg_url(url)));
            urls.extend(filter_urls(&resource_urls, |url| is_svg_url(url)));
            media.svg_urls = dedupe_urls(urls);
            media.inline_svgs = extract_inline_svgs(&html);
        }

        if want_videos && media.video_urls.is_empty() {
            if self.try_trigger_video().await.unwrap_or(false) {
                tokio::time::sleep(Duration::from_secs(5)).await;
                let refreshed_html = self.driver.source().await?;
                let dom_urls = self.collect_dom_urls().await.unwrap_or_default();
                let resource_urls = self.collect_resource_urls().await.unwrap_or_default();
                let new_capture = self
                    .collect_performance_video_urls(Duration::from_secs(8))
                    .await
                    .unwrap_or_default();
                performance_urls.extend(new_capture.urls);
                performance_entries += new_capture.entry_count;
                performance_methods.extend(new_capture.methods);
                performance_candidates.extend(new_capture.candidates);
                if performance_capture.large_urls.is_empty() && !new_capture.large_urls.is_empty() {
                    performance_capture.large_urls = new_capture.large_urls;
                }
                performance_capture.request_url_count += new_capture.request_url_count;
                performance_capture.request_size_count += new_capture.request_size_count;
                if performance_capture.top_sizes.is_empty() {
                    performance_capture.top_sizes = new_capture.top_sizes;
                }
                performance_urls = dedupe_urls(performance_urls);
                media.dom_urls = dom_urls.clone();
                media.resource_urls = resource_urls.clone();
                media.performance_urls = performance_urls.clone();
                let mut urls = extract_video_urls(&refreshed_html);
                urls.extend(filter_urls(&dom_urls, |url| is_video_url(url)));
                urls.extend(filter_urls(&resource_urls, |url| is_video_url(url)));
                urls.extend(performance_urls);
                media.video_urls = dedupe_urls(urls);
            }
        }

        if want_videos && media.video_urls.is_empty() && !performance_capture.large_urls.is_empty()
        {
            warn!(
                "{}: using large response URLs as video fallback: {}",
                question_id,
                summarize_urls(&performance_capture.large_urls)
            );
            performance_urls = performance_capture.large_urls.clone();
            media.performance_urls = performance_urls.clone();
            let mut urls = media.video_urls.clone();
            urls.extend(performance_urls.clone());
            media.video_urls = dedupe_urls(urls);
        }

        if want_videos && media.video_urls.is_empty() {
            if performance_capture.request_url_count > 0 {
                warn!(
                    "{}: performance requests: urls={}, sizes={}",
                    question_id,
                    performance_capture.request_url_count,
                    performance_capture.request_size_count
                );
            }
            if !performance_capture.saw_session_cookie {
                warn!(
                    "{}: no _mksap19_session cookie observed in request headers",
                    question_id
                );
            }
            if !performance_capture.top_sizes.is_empty() {
                warn!(
                    "{}: largest responses: {}",
                    question_id,
                    summarize_sizes(&performance_capture.top_sizes)
                );
            }
            if performance_entries == 0 {
                warn!(
                    "{}: performance log was empty; check WebDriver logging prefs",
                    question_id
                );
            } else if !performance_methods.is_empty() {
                warn!(
                    "{}: performance methods observed: {}",
                    question_id,
                    summarize_methods(&performance_methods)
                );
            }
            if !performance_candidates.is_empty() {
                warn!(
                    "{}: performance candidate URLs: {}",
                    question_id,
                    summarize_urls(&performance_candidates)
                );
            }
        }

        Ok(media)
    }

    async fn has_session_cookie(&self) -> Result<bool> {
        let cookies = self.driver.get_all_cookies().await?;
        Ok(cookies
            .iter()
            .any(|cookie| cookie.name() == "_mksap19_session"))
    }

    async fn wait_for_session_cookie(&self, timeout: Duration) -> Result<Option<String>> {
        let start = Instant::now();
        loop {
            let cookies = self.driver.get_all_cookies().await?;
            if let Some(cookie) = cookies
                .iter()
                .find(|cookie| cookie.name() == "_mksap19_session")
            {
                return Ok(Some(cookie.value().to_string()));
            }
            if start.elapsed() >= timeout {
                return Ok(None);
            }
            tokio::time::sleep(Duration::from_secs(2)).await;
        }
    }

    async fn inject_session_cookie(&self, cookie_value: &str) -> Result<()> {
        self.driver.goto(&self.base_url).await?;
        let cookie = Cookie::build("_mksap19_session", cookie_value.to_string())
            .domain("mksap.acponline.org")
            .path("/")
            .secure(true)
            .http_only(true)
            .finish();
        self.driver.add_cookie(cookie).await?;
        match self.driver.get_named_cookie("_mksap19_session").await {
            Ok(stored) => {
                if stored.value() != cookie_value {
                    warn!(
                        "Session cookie value mismatch; expected {} chars, stored {} chars",
                        cookie_value.len(),
                        stored.value().len()
                    );
                }
            }
            Err(err) => {
                warn!("Failed to read back session cookie: {}", err);
            }
        }
        Ok(())
    }

    async fn collect_dom_urls(&self) -> Result<Vec<String>> {
        let script = r#"
            const urls = [];
            const push = (value) => {
                if (!value || typeof value !== "string") {
                    return;
                }
                urls.push(value);
            };
            const attrs = [
                "src",
                "data-src",
                "data-video",
                "data-video-src",
                "data-url",
                "data-asset",
                "data-file",
                "href",
            ];
            document.querySelectorAll("video, video source, source, iframe, img, object, embed, a, link").forEach(el => {
                push(el.currentSrc);
                attrs.forEach(attr => push(el.getAttribute(attr)));
            });
            return Array.from(new Set(urls));
        "#;
        let result = self.driver.execute(script, Vec::<Value>::new()).await?;
        let urls: Vec<String> = result.convert()?;
        Ok(urls)
    }

    async fn collect_resource_urls(&self) -> Result<Vec<String>> {
        let script = r#"
            if (!window.performance || !window.performance.getEntriesByType) {
                return [];
            }
            return window.performance.getEntriesByType("resource").map(entry => entry.name);
        "#;
        let result = self.driver.execute(script, Vec::<Value>::new()).await?;
        let urls: Vec<String> = result.convert()?;
        Ok(urls)
    }

    async fn drain_performance_logs(&self) -> Result<()> {
        let _ = self.fetch_performance_logs().await?;
        Ok(())
    }

    async fn collect_performance_video_urls(
        &self,
        timeout: Duration,
    ) -> Result<PerformanceCapture> {
        let start = Instant::now();
        let mut capture = PerformanceCapture::default();
        let mut request_urls: HashMap<String, String> = HashMap::new();
        let mut request_types: HashMap<String, String> = HashMap::new();
        let mut request_sizes: HashMap<String, u64> = HashMap::new();
        loop {
            let entries = self.fetch_performance_logs().await?;
            capture.entry_count += entries.len();
            let batch = extract_performance_batch(&entries);
            capture.urls.extend(batch.urls);
            capture.methods.extend(batch.methods);
            capture.candidates.extend(batch.candidates);
            if batch.saw_session_cookie {
                capture.saw_session_cookie = true;
            }
            request_urls.extend(batch.request_urls);
            request_types.extend(batch.request_types);
            request_sizes.extend(batch.request_sizes);
            if !capture.urls.is_empty() || start.elapsed() >= timeout {
                break;
            }
            tokio::time::sleep(Duration::from_millis(500)).await;
        }
        capture.urls = dedupe_urls(capture.urls);
        capture.candidates = dedupe_urls(capture.candidates);
        let (large_urls, top_sizes) =
            select_large_urls(&request_urls, &request_sizes, &request_types);
        capture.large_urls = large_urls;
        capture.top_sizes = top_sizes;
        capture.request_url_count = request_urls.len();
        capture.request_size_count = request_sizes.len();
        Ok(capture)
    }

    async fn fetch_performance_logs(&self) -> Result<Vec<Value>> {
        let session_id = self.driver.handle.session_id.clone();
        let url = format!(
            "{}/session/{}/log",
            self.webdriver_url.trim_end_matches('/'),
            session_id
        );
        let response = self
            .log_client
            .post(url)
            .json(&json!({"type": "performance"}))
            .send()
            .await?;
        let response = response.error_for_status()?;
        let payload: Value = response.json().await?;
        let entries = payload
            .get("value")
            .and_then(|value| value.as_array())
            .cloned()
            .unwrap_or_default();
        Ok(entries)
    }

    async fn try_trigger_video(&self) -> Result<bool> {
        let script = r#"
            const selectors = [
                'button[aria-label*="play" i]',
                'button[title*="play" i]',
                '[data-testid*="play" i]',
                'button[class*="play" i]',
                '[role="button"][aria-label*="play" i]',
                '[role="button"][title*="play" i]',
            ];
            for (const selector of selectors) {
                const el = document.querySelector(selector);
                if (el) {
                    el.scrollIntoView({block: "center"});
                    el.click();
                    return true;
                }
            }
            const textMatches = Array.from(document.querySelectorAll("button, a, [role='button']"))
                .filter(el => /video/i.test(el.textContent || ""));
            if (textMatches.length > 0) {
                textMatches[0].scrollIntoView({block: "center"});
                textMatches[0].click();
                return true;
            }
            const video = document.querySelector("video");
            if (video) {
                try {
                    video.muted = true;
                    video.scrollIntoView({block: "center"});
                    const playPromise = video.play();
                    if (playPromise && playPromise.catch) {
                        playPromise.catch(() => {});
                    }
                    return true;
                } catch (e) {}
            }
            return false;
        "#;
        let result = self.driver.execute(script, Vec::<Value>::new()).await?;
        let clicked: bool = result.convert()?;
        Ok(clicked)
    }

    async fn try_fill(&self, selector: &str, value: &str) {
        match self.driver.find(By::Css(selector)).await {
            Ok(element) => {
                let _ = element.clear().await;
                let _ = element.send_keys(value).await;
            }
            Err(_) => {}
        }
    }

    async fn try_submit_password(&self) -> Result<()> {
        if let Ok(element) = self
            .driver
            .find(By::Css("input[type='password'], input[name*='password']"))
            .await
        {
            let _ = element.send_keys("\n").await;
        }
        Ok(())
    }
}

fn extract_video_urls(html: &str) -> Vec<String> {
    let mut urls = Vec::new();
    let re = Regex::new(r#"src="([^"]+\.(?:mp4|m3u8)[^"]*)""#).unwrap();
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

fn extract_inline_svgs(html: &str) -> Vec<String> {
    let mut svgs = Vec::new();
    let re = Regex::new(r#"(?s)(<svg\b.*?</svg>)"#).unwrap();
    for cap in re.captures_iter(html) {
        svgs.push(cap[1].to_string());
    }
    svgs
}

fn dedupe_urls(urls: Vec<String>) -> Vec<String> {
    let mut seen = std::collections::HashSet::new();
    urls.into_iter()
        .filter(|url| seen.insert(url.clone()))
        .collect()
}

fn filter_urls<F>(urls: &[String], predicate: F) -> Vec<String>
where
    F: Fn(&str) -> bool,
{
    urls.iter().filter(|url| predicate(url)).cloned().collect()
}

fn is_video_url(url: &str) -> bool {
    let lower = url.to_ascii_lowercase();
    lower.contains(".mp4") || lower.contains(".m3u8")
}

fn is_svg_url(url: &str) -> bool {
    let lower = url.to_ascii_lowercase();
    lower.contains(".svg")
}

fn extract_performance_batch(entries: &[Value]) -> PerformanceBatch {
    let mut batch = PerformanceBatch::default();
    for entry in entries {
        let message = entry.get("message").and_then(|v| v.as_str());
        let Some(message) = message else {
            continue;
        };
        let parsed: Value = match serde_json::from_str(message) {
            Ok(value) => value,
            Err(_) => continue,
        };
        let method = parsed
            .get("message")
            .and_then(|msg| msg.get("method"))
            .and_then(|m| m.as_str());
        let Some(method) = method else {
            continue;
        };
        batch.methods.insert(method.to_string());

        if method == "Network.responseReceived" {
            let params = parsed.get("message").and_then(|msg| msg.get("params"));
            let response = params.and_then(|params| params.get("response"));
            if let (Some(params), Some(response)) = (params, response) {
                if let Some(request_id) = params.get("requestId").and_then(|id| id.as_str()) {
                    let resource_type = params
                        .get("type")
                        .and_then(|t| t.as_str())
                        .unwrap_or("")
                        .to_string();
                    if !resource_type.is_empty() {
                        batch
                            .request_types
                            .insert(request_id.to_string(), resource_type);
                    }
                }
                let url = response.get("url").and_then(|u| u.as_str());
                let mime = response.get("mimeType").and_then(|m| m.as_str());
                let resource_type = params.get("type").and_then(|t| t.as_str());
                if let Some(url) = url {
                    if let Some(request_id) = params.get("requestId").and_then(|id| id.as_str()) {
                        batch
                            .request_urls
                            .insert(request_id.to_string(), url.to_string());
                    }
                    if is_video_hint_url(url)
                        || matches!(resource_type, Some("Media") | Some("Other"))
                    {
                        push_limited(&mut batch.candidates, url.to_string(), 8);
                    }
                    if matches!(resource_type, Some("Media")) || is_video_candidate(url, mime) {
                        batch.urls.push(url.to_string());
                    }
                }
            }
        } else if method == "Network.requestWillBeSent" {
            if let Some(params) = parsed.get("message").and_then(|msg| msg.get("params")) {
                if let Some(url) = params
                    .get("request")
                    .and_then(|req| req.get("url"))
                    .and_then(|u| u.as_str())
                {
                    if is_video_url(url) {
                        batch.urls.push(url.to_string());
                    }
                    if is_video_hint_url(url) {
                        push_limited(&mut batch.candidates, url.to_string(), 8);
                    }
                }
                if let Some(request_id) = params.get("requestId").and_then(|id| id.as_str()) {
                    if let Some(request) = params.get("request") {
                        if let Some(url) = request.get("url").and_then(|u| u.as_str()) {
                            batch
                                .request_urls
                                .insert(request_id.to_string(), url.to_string());
                        }
                    }
                }
            }
        } else if method == "Network.loadingFinished" {
            if let Some(params) = parsed.get("message").and_then(|msg| msg.get("params")) {
                let request_id = params.get("requestId").and_then(|id| id.as_str());
                let size = params
                    .get("encodedDataLength")
                    .and_then(|v| v.as_f64())
                    .map(|v| v as u64);
                if let (Some(request_id), Some(size)) = (request_id, size) {
                    batch.request_sizes.insert(request_id.to_string(), size);
                }
            }
        } else if method == "Network.requestWillBeSentExtraInfo" {
            if let Some(params) = parsed.get("message").and_then(|msg| msg.get("params")) {
                if let Some(headers) = params.get("headers").and_then(|h| h.as_object()) {
                    let cookie_header = headers
                        .get("cookie")
                        .or_else(|| headers.get("Cookie"))
                        .and_then(|v| v.as_str());
                    if let Some(cookie_header) = cookie_header {
                        if cookie_header.contains("_mksap19_session") {
                            batch.saw_session_cookie = true;
                        }
                    }
                }
            }
        }
    }
    batch
}

#[derive(Default)]
struct PerformanceCapture {
    urls: Vec<String>,
    entry_count: usize,
    methods: HashSet<String>,
    candidates: Vec<String>,
    large_urls: Vec<String>,
    top_sizes: Vec<(u64, String)>,
    request_url_count: usize,
    request_size_count: usize,
    saw_session_cookie: bool,
}

#[derive(Default)]
struct PerformanceBatch {
    urls: Vec<String>,
    methods: HashSet<String>,
    candidates: Vec<String>,
    request_urls: HashMap<String, String>,
    request_types: HashMap<String, String>,
    request_sizes: HashMap<String, u64>,
    saw_session_cookie: bool,
}

fn select_large_urls(
    request_urls: &HashMap<String, String>,
    request_sizes: &HashMap<String, u64>,
    request_types: &HashMap<String, String>,
) -> (Vec<String>, Vec<(u64, String)>) {
    let mut urls = Vec::new();
    for (request_id, resource_type) in request_types {
        if resource_type == "Media" {
            if let Some(url) = request_urls.get(request_id) {
                urls.push(url.clone());
            }
        }
    }
    urls = dedupe_urls(urls);

    let mut sized: Vec<(u64, String)> = request_sizes
        .iter()
        .filter_map(|(request_id, size)| {
            let url = request_urls.get(request_id)?;
            Some((*size, url.clone()))
        })
        .collect();
    sized.sort_by(|a, b| b.0.cmp(&a.0));
    let top_sizes: Vec<(u64, String)> = sized.iter().take(3).cloned().collect();

    for (size, url) in sized {
        if size < 500_000 {
            continue;
        }
        if is_excluded_large_asset(&url) {
            continue;
        }
        if !urls.contains(&url) {
            urls.push(url);
        }
        if urls.len() >= 3 {
            break;
        }
    }

    (urls, top_sizes)
}

fn is_excluded_large_asset(url: &str) -> bool {
    let lower = url.to_ascii_lowercase();
    let excluded_exts = [
        ".js", ".css", ".png", ".jpg", ".jpeg", ".svg", ".gif", ".woff", ".woff2",
    ];
    excluded_exts.iter().any(|ext| lower.contains(ext))
}

fn is_video_candidate(url: &str, mime_type: Option<&str>) -> bool {
    if is_video_url(url) {
        return true;
    }
    if let Some(mime) = mime_type {
        let lower = mime.to_ascii_lowercase();
        if lower.starts_with("video/") {
            return true;
        }
        if lower.contains("mpegurl") {
            return true;
        }
    }
    false
}

fn summarize_methods(methods: &HashSet<String>) -> String {
    let mut items: Vec<&String> = methods.iter().collect();
    items.sort();
    let slice = if items.len() > 8 {
        &items[..8]
    } else {
        &items[..]
    };
    let mut summary = String::new();
    for (idx, item) in slice.iter().enumerate() {
        if idx > 0 {
            summary.push_str(", ");
        }
        summary.push_str(item.as_str());
    }
    if items.len() > slice.len() {
        summary.push_str(", …");
    }
    summary
}

fn summarize_urls(urls: &[String]) -> String {
    let slice = if urls.len() > 5 { &urls[..5] } else { urls };
    let mut summary = String::new();
    for (idx, url) in slice.iter().enumerate() {
        if idx > 0 {
            summary.push_str(", ");
        }
        summary.push_str(url);
    }
    if urls.len() > slice.len() {
        summary.push_str(", …");
    }
    summary
}

fn summarize_sizes(items: &[(u64, String)]) -> String {
    let mut summary = String::new();
    for (idx, (size, url)) in items.iter().enumerate() {
        if idx > 0 {
            summary.push_str(", ");
        }
        summary.push_str(&format!("{}b {}", size, url));
    }
    summary
}

fn is_video_hint_url(url: &str) -> bool {
    let lower = url.to_ascii_lowercase();
    lower.contains("cvvid")
        || lower.contains("video")
        || lower.contains("vid")
        || lower.contains("m3u8")
        || lower.contains("mp4")
        || lower.contains("stream")
}

fn push_limited(target: &mut Vec<String>, value: String, limit: usize) {
    if target.len() < limit {
        target.push(value);
    }
}
