use clap::Parser;
use serde::Deserialize;
use serde_json::Value;
use std::path::PathBuf;

#[derive(Parser, Debug)]
#[command(about = "Extract MKSAP question media and update local JSON", author, version)]
pub struct Args {
    /// ACP MKSAP question ID (e.g., cvmcq24012)
    pub question_id: Option<String>,

    /// Base API URL
    #[arg(long, default_value = "https://mksap.acponline.org")]
    pub base_url: String,

    /// Root directory containing extracted question JSON folders
    #[arg(long, default_value = "../mksap_data")]
    pub data_dir: String,

    /// Process every question under data_dir
    #[arg(long)]
    pub all: bool,

    /// Reformat existing table HTML files under data_dir
    #[arg(long)]
    pub format_existing: bool,

    /// Skip video extraction
    #[arg(long)]
    pub skip_videos: bool,

    /// Skip SVG extraction
    #[arg(long)]
    pub skip_svgs: bool,

    /// Use a headed browser for automation
    #[arg(long)]
    pub headed: bool,

    /// Open a browser for interactive login if no session cookie is available
    #[arg(long)]
    pub interactive_login: bool,

    /// Username for automated login (best effort)
    #[arg(long)]
    pub username: Option<String>,

    /// Password for automated login (best effort)
    #[arg(long)]
    pub password: Option<String>,

    /// WebDriver URL for browser automation
    #[arg(long, default_value = "http://localhost:9515")]
    pub webdriver_url: String,

    /// Timeout (seconds) to wait for login cookie detection
    #[arg(long, default_value_t = 600)]
    pub login_timeout_seconds: u64,
}

#[derive(Debug, Deserialize)]
pub struct FigureResponse {
    pub id: String,
    #[serde(rename = "imageInfo")]
    pub image_info: ImageInfo,
}

#[derive(Debug, Deserialize)]
pub struct ImageInfo {
    pub extension: String,
    pub hash: String,
}

#[derive(Debug, Deserialize)]
pub struct TableResponse {
    pub id: String,
    #[serde(rename = "jsonContent")]
    pub json_content: Value,
}

#[derive(Clone, Debug)]
pub struct QuestionEntry {
    pub question_id: String,
    pub question_dir: PathBuf,
    pub json_path: PathBuf,
}

#[derive(Debug, Default)]
pub struct MediaUpdate {
    pub tables: Vec<String>,
    pub images: Vec<String>,
    pub videos: Vec<String>,
    pub svgs: Vec<String>,
}
