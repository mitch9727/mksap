//! CLI argument parsing and option structs.

use std::path::Path;

use crate::app::{BASE_URL, OUTPUT_DIR};

#[derive(Debug)]
pub struct StandardizeOptions {
    pub dry_run: bool,
    pub system_filter: Option<String>,
}

#[derive(Debug)]
pub struct RunOptions {
    pub refresh_existing: bool,
}

#[derive(Debug)]
pub struct MediaOptions {
    /// Base API URL (default: https://mksap.acponline.org).
    pub base_url: String,
    /// Output directory for extracted data.
    pub data_dir: String,
    /// Discovery metadata file path.
    pub discovery_file: String,
    /// Optional question ID filter.
    pub question_id: Option<String>,
    /// Download all discovered items when true.
    pub all: bool,
    /// Skip figure downloads.
    pub skip_figures: bool,
    /// Skip table downloads.
    pub skip_tables: bool,
    /// Skip SVG downloads.
    pub skip_svgs: bool,
    /// Concurrent request count for discovery.
    pub concurrent_requests: usize,
    /// WebDriver URL for SVG browser downloads.
    pub webdriver_url: String,
    /// Run browser in headless mode.
    pub headless: bool,
    /// Use interactive login in browser automation.
    pub interactive_login: bool,
    /// Username for browser login.
    pub username: Option<String>,
    /// Password for browser login.
    pub password: Option<String>,
    /// Timeout in seconds for browser login.
    pub login_timeout_secs: u64,
}

impl MediaOptions {
    pub fn from_args(args: &[String]) -> Self {
        Self {
            base_url: resolve_media_base_url(args),
            data_dir: resolve_media_data_dir(args),
            discovery_file: resolve_media_discovery_file(args),
            question_id: parse_arg_value(args, "--question-id"),
            all: has_flag(args, "--all"),
            skip_figures: has_flag(args, "--skip-figures"),
            skip_tables: has_flag(args, "--skip-tables"),
            skip_svgs: has_flag(args, "--skip-svgs"),
            concurrent_requests: resolve_media_concurrency(args),
            webdriver_url: parse_arg_value(args, "--webdriver-url")
                .unwrap_or_else(|| "http://localhost:9515".to_string()),
            headless: parse_bool_arg(args, "--headless", true),
            interactive_login: parse_bool_arg(args, "--interactive-login", false),
            username: parse_arg_value(args, "--username"),
            password: parse_arg_value(args, "--password"),
            login_timeout_secs: parse_arg_value(args, "--login-timeout-secs")
                .and_then(|value| value.parse::<u64>().ok())
                .unwrap_or(120),
        }
    }
}

pub fn parse_standardize_options(args: &[String]) -> StandardizeOptions {
    let dry_run = has_flag(args, "--dry-run");
    let system_filter = parse_arg_value(args, "--system");

    StandardizeOptions {
        dry_run,
        system_filter,
    }
}

pub fn parse_run_options(args: &[String]) -> RunOptions {
    let refresh_existing = args.iter().any(|arg| {
        arg == "--refresh-existing" || arg == "--overwrite-existing" || arg == "--overwrite"
    });

    RunOptions { refresh_existing }
}

pub(crate) fn parse_arg_value(args: &[String], key: &str) -> Option<String> {
    let prefix = format!("{}=", key);
    args.iter()
        .find_map(|arg| arg.strip_prefix(&prefix).map(|value| value.to_string()))
        .or_else(|| {
            args.windows(2).find_map(|pair| {
                (pair[0] == key && !pair[1].starts_with('-')).then(|| pair[1].to_string())
            })
        })
}

pub(crate) fn has_flag(args: &[String], flag: &str) -> bool {
    args.iter().any(|arg| arg == flag)
}

pub(crate) fn parse_bool_arg(args: &[String], flag: &str, default: bool) -> bool {
    if let Some(value) = parse_arg_value(args, flag) {
        match value.to_ascii_lowercase().as_str() {
            "true" | "1" | "yes" => return true,
            "false" | "0" | "no" => return false,
            _ => return default,
        }
    }

    if has_flag(args, flag) {
        return true;
    }

    default
}

fn resolve_media_base_url(args: &[String]) -> String {
    parse_arg_value(args, "--base-url").unwrap_or_else(|| BASE_URL.to_string())
}

fn resolve_media_data_dir(args: &[String]) -> String {
    parse_arg_value(args, "--data-dir").unwrap_or_else(|| OUTPUT_DIR.to_string())
}

fn resolve_media_discovery_file(args: &[String]) -> String {
    parse_arg_value(args, "--discovery-file").unwrap_or_else(|| {
        Path::new(OUTPUT_DIR)
            .join("media_discovery.json")
            .to_string_lossy()
            .to_string()
    })
}

fn resolve_media_concurrency(args: &[String]) -> usize {
    parse_arg_value(args, "--concurrent-requests")
        .and_then(|value| value.parse::<usize>().ok())
        .filter(|value| *value > 0)
        .unwrap_or(10)
}
