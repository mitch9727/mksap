use anyhow::{Context, Result};
use clap::Parser;
use reqwest::{header, Client};
use tracing::info;

mod discovery;

#[derive(Parser, Debug)]
#[command(about = "Discover MKSAP questions with media via API", author, version)]
struct Args {
    /// Base API URL
    #[arg(long, default_value = "https://mksap.acponline.org")]
    base_url: String,

    /// Number of concurrent API requests
    #[arg(long, default_value = "10")]
    concurrent_requests: usize,

    /// Output file path for discovery results
    #[arg(long, default_value = "media_discovery.json")]
    output_file: String,
}

#[tokio::main]
async fn main() -> Result<()> {
    // Load .env file from project root
    dotenv::from_path("../.env").ok();

    tracing_subscriber::fmt()
        .with_max_level(tracing::Level::INFO)
        .init();

    let args = Args::parse();

    info!("Starting media discovery via API");
    info!("Base URL: {}", args.base_url);
    info!("Concurrent requests: {}", args.concurrent_requests);
    info!("Output file: {}", args.output_file);

    // Get session cookie from environment
    let session_cookie = std::env::var("MKSAP_SESSION")
        .context("MKSAP_SESSION not set in .env file")?;

    // Build HTTP client with authentication
    let mut headers = header::HeaderMap::new();
    let cookie_value = format!("_mksap19_session={}", session_cookie);
    headers.insert(
        header::COOKIE,
        header::HeaderValue::from_str(&cookie_value)?,
    );
    info!("Using session cookie from environment");

    let client = Client::builder()
        .default_headers(headers)
        .build()?;

    // Discover questions with media using inverse logic:
    // 1. Get all question IDs from text_extractor's discovery checkpoints
    // 2. Check each question via API to see if it's text-only
    // 3. Questions that aren't text-only = questions with media
    let results = discovery::discover_media_questions(
        &client,
        &args.base_url,
        args.concurrent_requests,
    )
    .await
    .context("Failed to discover media questions")?;

    let output_path = std::path::Path::new(&args.output_file);
    results.save_to_file(output_path)?;
    info!("Saved discovery results to {}", args.output_file);

    let report = results.generate_report();
    let report_path = output_path.with_extension("txt");
    std::fs::write(&report_path, &report)?;
    info!("Saved text report to {}", report_path.display());

    println!("\n{}", report);

    Ok(())
}
