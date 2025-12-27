pub mod api;
pub mod browser;
pub mod browser_download;
pub mod browser_media;
pub mod discovery;
pub mod download;
pub mod file_store;
pub mod media_ids;
pub mod render;
pub mod session;

use anyhow::{Context, Result};
use reqwest::{header, Client};
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
