use clap::{Parser, Subcommand};

#[derive(Parser, Debug)]
#[command(about = "Discover and download MKSAP media assets", author, version)]
pub struct Args {
    #[command(subcommand)]
    pub command: Option<Command>,

    /// Base API URL
    #[arg(long, default_value = "https://mksap.acponline.org", global = true)]
    pub base_url: String,

    /// Root directory containing extracted question JSON folders
    #[arg(long, default_value = "../mksap_data", global = true)]
    pub data_dir: String,

    /// Path to discovery results file
    #[arg(long, default_value = "media_discovery.json", global = true)]
    pub discovery_file: String,

    /// Number of concurrent API requests (discovery only)
    #[arg(long, default_value = "10", global = true)]
    pub concurrent_requests: usize,

    // Legacy arguments (when no subcommand specified, runs download mode)
    /// ACP MKSAP question ID (e.g., cvmcq24012)
    #[arg(conflicts_with = "command")]
    pub question_id: Option<String>,

    /// Process every discovered question
    #[arg(long, conflicts_with = "command")]
    pub all: bool,

    /// Skip figure downloads
    #[arg(long, conflicts_with = "command")]
    pub skip_figures: bool,

    /// Skip table downloads
    #[arg(long, conflicts_with = "command")]
    pub skip_tables: bool,
}

#[derive(Subcommand, Debug)]
pub enum Command {
    /// Discover all questions with media references (no downloads)
    Discover,

    /// Download figures and tables for discovered questions
    Download {
        /// ACP MKSAP question ID (e.g., cvmcq24012)
        #[arg(long)]
        question_id: Option<String>,

        /// Process every discovered question
        #[arg(long)]
        all: bool,

        /// Skip figure downloads
        #[arg(long)]
        skip_figures: bool,

        /// Skip table downloads
        #[arg(long)]
        skip_tables: bool,
    },

    /// Backfill inline table metadata from saved HTML files
    BackfillInlineTables,

    /// Download videos and svgs by loading the MKSAP UI in a browser
    Browser {
        /// ACP MKSAP question ID (e.g., cvmcq24012)
        #[arg(long)]
        question_id: Option<String>,

        /// Process every discovered question with video/svg content IDs
        #[arg(long)]
        all: bool,

        /// Skip video downloads
        #[arg(long)]
        skip_videos: bool,

        /// Skip svg downloads
        #[arg(long)]
        skip_svgs: bool,

        /// WebDriver URL (chromedriver or selenium server)
        #[arg(long, default_value = "http://localhost:9515")]
        webdriver_url: String,

        /// Run browser in headless mode
        #[arg(long, default_value_t = true)]
        headless: bool,

        /// Attempt interactive login when no session cookie is present
        #[arg(long)]
        interactive_login: bool,

        /// Username for interactive login (optional)
        #[arg(long)]
        username: Option<String>,

        /// Password for interactive login (optional)
        #[arg(long)]
        password: Option<String>,

        /// Login timeout in seconds
        #[arg(long, default_value_t = 120)]
        login_timeout_secs: u64,
    },
}
