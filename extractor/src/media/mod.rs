pub mod api;
pub mod browser;
pub mod browser_download;
pub mod discovery;
pub mod download;
pub mod file_store;
pub mod media_ids;
pub mod metadata;
pub mod render;
pub mod session;

use anyhow::{Context, Result};
use reqwest::{header, Client};
use serde_json::Value;
use tracing::{info, warn};

pub fn build_client() -> Result<Client> {
    let session_cookie = session::load_session_cookie()
        .context("Session cookie not set. Set MKSAP_SESSION or login via browser.")?;

    let mut headers = header::HeaderMap::new();
    let cookie_value = format!("_mksap19_session={}", session_cookie);
    headers.insert(
        header::COOKIE,
        header::HeaderValue::from_str(&cookie_value)?,
    );
    info!("Using session cookie from environment");

    if session_cookie.trim().is_empty() {
        warn!("MKSAP_SESSION is empty; API may return 401 Unauthorized.");
    }

    let client = Client::builder().default_headers(headers).build()?;
    Ok(client)
}

pub async fn fetch_content_metadata(client: &Client, base_url: &str) -> Result<Value> {
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

    response.json().await.context("Failed to parse metadata")
}
