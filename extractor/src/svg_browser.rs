use anyhow::{Context, Result};
use regex::Regex;
use serde_json::Value;
use std::time::{Duration, Instant};
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
    pub svg_urls: Vec<String>,
    pub inline_svgs: Vec<String>,
    pub page_html: String,
}

pub struct BrowserSession {
    driver: WebDriver,
    base_url: String,
}

impl BrowserSession {
    pub async fn connect(options: &BrowserOptions) -> Result<Self> {
        let mut caps = DesiredCapabilities::chrome();
        if options.headless {
            caps.add_chrome_arg("--headless=new")?;
        }
        caps.add_chrome_arg("--disable-gpu")?;
        caps.add_chrome_arg("--window-size=1280,900")?;
        let driver = WebDriver::new(&options.webdriver_url, caps)
            .await
            .with_context(|| format!("Failed to connect to {}", options.webdriver_url))?;
        driver
            .set_implicit_wait_timeout(Duration::from_secs(2))
            .await?;

        let session = BrowserSession {
            driver,
            base_url: options.base_url.clone(),
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

    pub async fn extract_media(&self, question_id: &str, want_svgs: bool) -> Result<BrowserMedia> {
        let mut media = BrowserMedia::default();
        let question_url = format!(
            "{}/app/question-bank/questions/{}",
            self.base_url, question_id
        );

        self.driver.goto(&question_url).await?;
        tokio::time::sleep(Duration::from_secs(5)).await;

        let html = self.driver.source().await?;
        media.page_html = html.clone();
        if want_svgs {
            let dom_urls = self.collect_dom_urls().await.unwrap_or_default();
            let resource_urls = self.collect_resource_urls().await.unwrap_or_default();
            let mut urls = extract_svg_urls(&html);
            urls.extend(filter_urls(&dom_urls, is_svg_url));
            urls.extend(filter_urls(&resource_urls, is_svg_url));
            media.svg_urls = dedupe_urls(urls);
            media.inline_svgs = extract_inline_svgs(&html);
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
                "data-url",
                "data-asset",
                "data-file",
                "href",
            ];
            document.querySelectorAll("iframe, img, object, embed, a, link").forEach(el => {
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

    async fn try_fill(&self, selector: &str, value: &str) {
        if let Ok(element) = self.driver.find(By::Css(selector)).await {
            let _ = element.clear().await;
            let _ = element.send_keys(value).await;
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

pub(crate) fn extract_svg_urls(html: &str) -> Vec<String> {
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

pub(crate) fn dedupe_urls(urls: Vec<String>) -> Vec<String> {
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

fn is_svg_url(url: &str) -> bool {
    let lower = url.to_ascii_lowercase();
    lower.contains(".svg")
}
