use anyhow::{Context, Result};
use reqwest::header::{HeaderMap, HeaderValue, COOKIE};
use reqwest::{Client, RequestBuilder, Response};
use std::time::Duration;
use tokio::time::timeout;

pub(crate) fn session_cookie_headers(session_cookie: &str) -> Result<HeaderMap> {
    let mut headers = HeaderMap::new();
    let cookie_value = format!("_mksap19_session={}", session_cookie);
    headers.insert(COOKIE, HeaderValue::from_str(&cookie_value)?);
    Ok(headers)
}

pub(crate) fn build_client_with_headers(headers: HeaderMap) -> Result<Client> {
    Ok(Client::builder().default_headers(headers).build()?)
}

pub(crate) async fn send_with_timeout(
    request: RequestBuilder,
    timeout_duration: Duration,
) -> Result<Response> {
    timeout(timeout_duration, request.send())
        .await
        .context("Request timeout")?
        .context("Network error")
}
