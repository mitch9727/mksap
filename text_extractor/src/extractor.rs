use anyhow::{Context, Result};
use reqwest::{
    header::{HeaderMap, HeaderValue, COOKIE},
    Client,
};
use std::env;
use std::fs;
use std::path::Path;
use tracing::warn;

#[path = "auth.rs"]
mod auth;
#[path = "cleanup.rs"]
mod cleanup;
#[path = "discovery.rs"]
mod discovery;
#[path = "io.rs"]
mod io;
#[path = "retry.rs"]
mod retry;
#[path = "workflow.rs"]
mod workflow;

const QUESTION_TYPE_CODES: [&str; 6] = ["mcq", "qqq", "vdx", "cor", "mqq", "sq"];
const CHECKPOINT_DIR_NAME: &str = ".checkpoints";
const FAILED_DIR_NAME: &str = "mksap_data_failed";

pub struct MKSAPExtractor {
    base_url: String,
    output_dir: String,
    pub client: Client,
    authenticated: bool,
}

impl MKSAPExtractor {
    pub fn new(base_url: &str, output_dir: &str) -> Result<Self> {
        fs::create_dir_all(output_dir).context("Failed to create output directory")?;

        Ok(Self {
            base_url: base_url.to_string(),
            output_dir: output_dir.to_string(),
            client: Client::new(),
            authenticated: false,
        })
    }

    pub fn with_session_cookie(mut self, session_cookie_value: &str) -> Self {
        // Create a new client with the session cookie in the default headers
        let mut headers = HeaderMap::new();
        let cookie_value = format!("_mksap19_session={}", session_cookie_value);
        let cookie_header = match HeaderValue::from_str(&cookie_value) {
            Ok(value) => value,
            Err(err) => {
                warn!(
                    "Invalid session cookie value; skipping cookie header: {}",
                    err
                );
                return self;
            }
        };

        headers.insert(COOKIE, cookie_header);

        match Client::builder().default_headers(headers).build() {
            Ok(client) => self.client = client,
            Err(err) => {
                warn!("Failed to build client with session cookie: {}", err);
            }
        }

        self
    }

    pub fn is_authenticated(&self) -> bool {
        self.authenticated
    }

    pub fn set_authenticated(&mut self, authenticated: bool) {
        self.authenticated = authenticated;
    }

    fn failed_root(&self) -> std::path::PathBuf {
        Path::new(&self.output_dir).with_file_name(FAILED_DIR_NAME)
    }

    fn concurrency_limit() -> usize {
        let default = std::thread::available_parallelism()
            .map(|count| count.get())
            .unwrap_or(4);

        env::var("MKSAP_CONCURRENCY")
            .ok()
            .and_then(|value| value.parse::<usize>().ok())
            .filter(|value| *value > 0)
            .unwrap_or(default)
    }
}
