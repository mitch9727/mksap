use anyhow::Result;
use reqwest::Client;
use std::path::Path;

use super::{filename_from_url, relative_path};

pub async fn download_svg(
    client: &Client,
    question_dir: &Path,
    url: &str,
) -> Result<Option<String>> {
    let filename = filename_from_url(url);
    let dest_dir = question_dir.join("svgs");
    std::fs::create_dir_all(&dest_dir)?;
    let dest_path = dest_dir.join(&filename);

    if !dest_path.exists() {
        let bytes = client.get(url).send().await?.error_for_status()?.bytes().await?;
        std::fs::write(&dest_path, bytes)?;
    }

    Ok(Some(relative_path("svgs", &filename)))
}

pub fn save_inline_svg(
    question_dir: &Path,
    index: usize,
    svg: &str,
) -> Result<Option<String>> {
    let filename = format!("inline_svg_{}.svg", index + 1);
    let dest_dir = question_dir.join("svgs");
    std::fs::create_dir_all(&dest_dir)?;
    let dest_path = dest_dir.join(&filename);
    if !dest_path.exists() {
        std::fs::write(&dest_path, svg)?;
    }
    Ok(Some(relative_path("svgs", &filename)))
}
