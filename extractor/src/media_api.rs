use anyhow::{bail, Context, Result};
use reqwest::Client;
use serde::Deserialize;
use serde_json::Value;
use std::path::Path;
use tracing::warn;

use super::render::render_table_html;

#[derive(Debug, Deserialize)]
struct FigureResponse {
    pub id: String,
    #[serde(rename = "imageInfo")]
    pub image_info: ImageInfo,
}

#[derive(Debug, Deserialize)]
struct ImageInfo {
    pub extension: String,
    pub hash: String,
}

#[derive(Debug, Deserialize)]
pub struct TableResponse {
    pub id: String,
    pub title: Option<Value>,
    #[serde(rename = "shortTitle")]
    pub short_title: Option<Value>,
    pub footnotes: Option<Value>,
    #[serde(rename = "jsonContent")]
    pub json_content: Value,
}

#[derive(Debug)]
pub struct TableDownload {
    pub path: String,
    pub table: TableResponse,
}

pub async fn fetch_question_json(
    client: &Client,
    base_url: &str,
    question_id: &str,
) -> Result<Value> {
    let url = format!("{}/api/questions/{}.json", base_url, question_id);
    let response = client
        .get(&url)
        .send()
        .await
        .context("Failed to reach API; check network connectivity and retry")?;
    if response.status() == reqwest::StatusCode::NOT_FOUND {
        bail!("Question ID not found: {}", question_id);
    }
    let response = response.error_for_status()?;
    response
        .json::<Value>()
        .await
        .context("Failed to decode question JSON")
}

pub async fn download_figure(
    client: &Client,
    base_url: &str,
    question_dir: &Path,
    figure_id: &str,
) -> Result<Option<String>> {
    let url = format!("{}/api/figures/{}.json", base_url, figure_id);
    let response = match client.get(&url).send().await {
        Ok(resp) => resp,
        Err(err) => {
            warn!(
                "Failed to reach API for figure {}: {}. Retry later.",
                figure_id, err
            );
            return Ok(None);
        }
    };
    if response.status() == reqwest::StatusCode::NOT_FOUND {
        warn!("Figure not found: {}", figure_id);
        return Ok(None);
    }
    let response = match response.error_for_status() {
        Ok(resp) => resp,
        Err(err) => {
            warn!("Failed to fetch figure {}: {}", figure_id, err);
            return Ok(None);
        }
    };
    let figure = response
        .json::<FigureResponse>()
        .await
        .context("Failed to decode figure JSON")?;

    let filename = format!(
        "{}.{}.{}",
        figure.id, figure.image_info.hash, figure.image_info.extension
    );
    let download_url = format!(
        "https://d2chybfyz5ban.cloudfront.net/hashed_figures/{}",
        filename
    );

    let dest_dir = question_dir.join("figures");
    std::fs::create_dir_all(&dest_dir)?;
    let dest_path = dest_dir.join(&filename);
    if !dest_path.exists() {
        let bytes = client
            .get(&download_url)
            .send()
            .await?
            .error_for_status()?
            .bytes()
            .await?;
        std::fs::write(&dest_path, bytes)?;
    }

    let relative = Path::new("figures").join(&filename);
    Ok(Some(relative.to_string_lossy().to_string()))
}

pub async fn download_table(
    client: &Client,
    base_url: &str,
    question_dir: &Path,
    table_id: &str,
) -> Result<Option<TableDownload>> {
    let url = format!("{}/api/tables/{}.json", base_url, table_id);
    let response = match client.get(&url).send().await {
        Ok(resp) => resp,
        Err(err) => {
            warn!(
                "Failed to reach API for table {}: {}. Retry later.",
                table_id, err
            );
            return Ok(None);
        }
    };
    if response.status() == reqwest::StatusCode::NOT_FOUND {
        warn!("Table not found: {}", table_id);
        return Ok(None);
    }
    let response = match response.error_for_status() {
        Ok(resp) => resp,
        Err(err) => {
            warn!("Failed to fetch table {}: {}", table_id, err);
            return Ok(None);
        }
    };
    let table = response
        .json::<TableResponse>()
        .await
        .context("Failed to decode table JSON")?;

    let html = render_table_html(&table.json_content);
    let filename = format!("{}.html", table.id);
    let dest_dir = question_dir.join("tables");
    std::fs::create_dir_all(&dest_dir)?;
    let dest_path = dest_dir.join(&filename);
    if !dest_path.exists() {
        std::fs::write(&dest_path, html)?;
    }

    let relative = Path::new("tables")
        .join(&filename)
        .to_string_lossy()
        .to_string();

    Ok(Some(TableDownload {
        path: relative,
        table,
    }))
}
