use anyhow::Result;
use reqwest::Client;
use std::fs;
use std::path::Path;

pub struct MediaExtractor;

impl MediaExtractor {
    pub async fn extract_images(
        client: &Client,
        image_urls: Vec<&str>,
        question_id: &str,
        folder: &Path,
    ) -> Result<Vec<String>> {
        let mut files = Vec::new();

        for (i, url) in image_urls.iter().enumerate() {
            let response = client.get(*url).send().await?;
            let content_type = response
                .headers()
                .get("content-type")
                .and_then(|h| h.to_str().ok())
                .unwrap_or("image/png");

            let ext = if content_type.contains("png") {
                "png"
            } else if content_type.contains("jpeg") || content_type.contains("jpg") {
                "jpg"
            } else if content_type.contains("gif") {
                "gif"
            } else if content_type.contains("webp") {
                "webp"
            } else {
                "png"
            };

            let filename = format!("{}_{}.{}", question_id, i + 1, ext);
            let filepath = folder.join(&filename);
            let bytes = response.bytes().await?;
            fs::write(filepath, bytes)?;
            files.push(filename);
        }

        Ok(files)
    }

    pub async fn extract_videos(
        client: &Client,
        video_urls: Vec<&str>,
        question_id: &str,
        folder: &Path,
    ) -> Result<Vec<String>> {
        let mut files = Vec::new();

        for (i, url) in video_urls.iter().enumerate() {
            let response = client.get(*url).send().await?;
            let content_type = response
                .headers()
                .get("content-type")
                .and_then(|h| h.to_str().ok())
                .unwrap_or("video/mp4");

            let ext = if content_type.contains("mp4") {
                "mp4"
            } else if content_type.contains("webm") {
                "webm"
            } else if content_type.contains("ogg") {
                "ogg"
            } else {
                "mp4"
            };

            let filename = format!("{}_{}.{}", question_id, i + 1, ext);
            let filepath = folder.join(&filename);
            let bytes = response.bytes().await?;
            fs::write(filepath, bytes)?;
            files.push(filename);
        }

        Ok(files)
    }

}
