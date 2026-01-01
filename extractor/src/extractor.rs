use anyhow::{Context, Result};
use reqwest::Client;
use std::fs;
use std::path::Path;
use tracing::warn;

use crate::utils::parse_env;
#[path = "auth.rs"]
pub mod auth;
#[path = "cleanup.rs"]
mod cleanup;
#[path = "discovery.rs"]
mod discovery;
#[path = "io.rs"]
pub mod io;
#[path = "retry.rs"]
mod retry;
#[path = "workflow.rs"]
mod workflow;

const QUESTION_TYPE_CODES: [&str; 6] = ["mcq", "qqq", "vdx", "cor", "mqq", "sq"];
const CHECKPOINT_DIR_NAME: &str = ".checkpoints";
const FAILED_DIR_NAME: &str = "mksap_data_failed";

pub struct MKSAPExtractor {
    pub base_url: String,
    pub output_dir: String,
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
        let headers = match crate::http::session_cookie_headers(session_cookie_value) {
            Ok(headers) => headers,
            Err(err) => {
                warn!(
                    "Invalid session cookie value; skipping cookie header: {}",
                    err
                );
                return self;
            }
        };

        match crate::http::build_client_with_headers(headers) {
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

        let configured = parse_env("MKSAP_CONCURRENCY", default);
        if configured == 0 {
            default
        } else {
            configured
        }
    }
}
