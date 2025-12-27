use anyhow::{Context, Result};
use std::fs;
use std::path::PathBuf;

pub fn load_session_cookie() -> Option<String> {
    if let Ok(session_cookie) = std::env::var("MKSAP_SESSION") {
        let trimmed = session_cookie.trim().to_string();
        if !trimmed.is_empty() {
            return Some(trimmed);
        }
    }

    let path = session_cookie_path().ok()?;
    let text = fs::read_to_string(path).ok()?;
    let trimmed = text.trim().to_string();
    if trimmed.is_empty() {
        None
    } else {
        Some(trimmed)
    }
}

pub fn save_session_cookie(cookie: &str) -> Result<()> {
    let path = session_cookie_path().context("Unable to resolve session cookie path")?;
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent)
            .with_context(|| format!("Failed to create {}", parent.display()))?;
    }
    fs::write(&path, cookie.trim())
        .with_context(|| format!("Failed to write {}", path.display()))?;
    Ok(())
}

fn session_cookie_path() -> Result<PathBuf> {
    let home = std::env::var("HOME").context("HOME not set")?;
    Ok(PathBuf::from(home).join(".mksap_session"))
}
