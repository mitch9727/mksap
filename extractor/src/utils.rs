//! Shared helper utilities for CLI and extraction workflows.

use std::env;
use std::str::FromStr;
use tracing::info;

pub fn parse_env<T: FromStr>(key: &str, default: T) -> T {
    env::var(key)
        .ok()
        .and_then(|value| value.parse().ok())
        .unwrap_or(default)
}

pub fn log_progress(current: usize, total: usize, message: &str) {
    info!("\n[{}/{}] {}", current, total, message);
}
