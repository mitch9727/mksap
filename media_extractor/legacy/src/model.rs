use clap::{Parser, Subcommand};
use serde::Deserialize;
use serde_json::Value;
use std::path::PathBuf;

#[derive(Parser, Debug)]
#[command(about = "Extract MKSAP question media and update local JSON", author, version)]
pub struct Args {
    #[command(subcommand)]
    pub command: Option<Command>,

    /// Base API URL
    #[arg(long, default_value = "https://mksap.acponline.org", global = true)]
    pub base_url: String,

    /// Root directory containing extracted question JSON folders
    #[arg(long, default_value = "../mksap_data", global = true)]
    pub data_dir: String,

    /// Username for automated login (best effort)
    #[arg(long, global = true)]
    pub username: Option<String>,

    /// Password for automated login (best effort)
    #[arg(long, global = true)]
    pub password: Option<String>,

    /// WebDriver URL for browser automation
    #[arg(long, default_value = "http://localhost:9515", global = true)]
    pub webdriver_url: String,

    /// Timeout (seconds) to wait for login cookie detection
    #[arg(long, default_value_t = 600, global = true)]
    pub login_timeout_seconds: u64,

    // Legacy arguments (when no subcommand specified, runs extract mode)
    /// ACP MKSAP question ID (e.g., cvmcq24012)
    #[arg(conflicts_with = "command")]
    pub question_id: Option<String>,

    /// Process every question under data_dir
    #[arg(long, conflicts_with = "command")]
    pub all: bool,

    /// Reformat existing table HTML files under data_dir
    #[arg(long, conflicts_with = "command")]
    pub format_existing: bool,

    /// Skip video extraction
    #[arg(long, conflicts_with = "command")]
    pub skip_videos: bool,

    /// Skip SVG extraction
    #[arg(long, conflicts_with = "command")]
    pub skip_svgs: bool,

    /// Use a headed browser for automation
    #[arg(long, conflicts_with = "command")]
    pub headed: bool,

    /// Open a browser for interactive login if no session cookie is available
    #[arg(long, conflicts_with = "command")]
    pub interactive_login: bool,
}

#[derive(Subcommand, Debug)]
pub enum Command {
    /// Discover all questions with media (fast, no downloads)
    Discover {
        /// Number of concurrent API requests
        #[arg(long, default_value = "10")]
        concurrent_requests: usize,

        /// Output file path for discovery results
        #[arg(long, default_value = "media_discovery.json")]
        output_file: String,
    },

    /// Extract media files for questions
    Extract {
        /// ACP MKSAP question ID (e.g., cvmcq24012)
        #[arg(long)]
        question_id: Option<String>,

        /// Process every question under data_dir
        #[arg(long)]
        all: bool,

        /// Path to discovery results file (filters to questions with media)
        #[arg(long)]
        discovery_file: Option<String>,

        /// Reformat existing table HTML files under data_dir
        #[arg(long)]
        format_existing: bool,

        /// Skip video extraction
        #[arg(long)]
        skip_videos: bool,

        /// Skip SVG extraction
        #[arg(long)]
        skip_svgs: bool,

        /// Use a headed browser for automation
        #[arg(long)]
        headed: bool,

        /// Open a browser for interactive login if no session cookie is available
        #[arg(long)]
        interactive_login: bool,
    },
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
