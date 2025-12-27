#[path = "asset_api.rs"]
pub mod asset_api;
#[path = "asset_discovery.rs"]
pub mod asset_discovery;
#[path = "asset_download.rs"]
pub mod asset_download;
#[path = "asset_metadata.rs"]
pub mod asset_metadata;
#[path = "asset_stats.rs"]
mod asset_stats;
#[path = "asset_store.rs"]
pub mod asset_store;
#[path = "asset_types.rs"]
mod asset_types;
#[path = "content_ids.rs"]
pub mod content_ids;
#[path = "svg_browser.rs"]
pub mod svg_browser;
#[path = "svg_download.rs"]
pub mod svg_download;
#[path = "table_render.rs"]
pub mod table_render;

use anyhow::{Context, Result};
use reqwest::Client;
use serde_json::Value;
use tracing::{info, warn};

pub fn build_client() -> Result<Client> {
    let session_cookie = crate::session::load_session_cookie()
        .context("Session cookie not set. Set MKSAP_SESSION or login via browser.")?;

    let headers = crate::http::session_cookie_headers(&session_cookie)?;
    info!("Using session cookie from environment");

    if session_cookie.trim().is_empty() {
        warn!("MKSAP_SESSION is empty; API may return 401 Unauthorized.");
    }

    crate::http::build_client_with_headers(headers)
}

pub async fn fetch_content_metadata(client: &Client, base_url: &str) -> Result<Value> {
    let url = crate::endpoints::content_metadata(base_url);
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
