use anyhow::{Context, Result};
use clap::Parser;
use reqwest::{header, Client};
use tracing::{info, warn};

mod api;
mod browser;
mod browser_download;
mod browser_media;
mod cli;
mod discovery;
mod download;
mod file_store;
mod render;
mod session;

use cli::{Args, Command};

#[tokio::main]
async fn main() -> Result<()> {
    // Load .env from current working directory or repo root.
    dotenv::dotenv().ok();
    dotenv::from_path("../.env").ok();

    tracing_subscriber::fmt()
        .with_max_level(tracing::Level::INFO)
        .init();

    let args = Args::parse();

    match &args.command {
        Some(Command::Discover) => {
            run_discovery(&args).await?;
        }
        Some(Command::Download {
            question_id,
            all,
            skip_figures,
            skip_tables,
        }) => {
            run_download(
                &args,
                question_id.as_deref(),
                *all,
                *skip_figures,
                *skip_tables,
            )
            .await?;
        }
        Some(Command::BackfillInlineTables) => {
            let added = file_store::backfill_inline_table_metadata(&args.data_dir)?;
            info!("Backfilled {} inline table metadata entries.", added);
        }
        Some(Command::Browser {
            question_id,
            all,
            skip_videos,
            skip_svgs,
            webdriver_url,
            headless,
            interactive_login,
            username,
            password,
            login_timeout_secs,
        }) => {
            run_browser_download(
                &args,
                question_id.as_deref(),
                *all,
                *skip_videos,
                *skip_svgs,
                webdriver_url,
                *headless,
                *interactive_login,
                username.clone(),
                password.clone(),
                *login_timeout_secs,
            )
            .await?;
        }
        None => {
            if args.all || args.question_id.is_some() {
                run_download(
                    &args,
                    args.question_id.as_deref(),
                    args.all,
                    args.skip_figures,
                    args.skip_tables,
                )
                .await?;
            } else {
                run_discovery(&args).await?;
            }
        }
    }

    Ok(())
}

async fn run_discovery(args: &Args) -> Result<()> {
    info!("Starting media discovery via API");
    info!("Base URL: {}", args.base_url);
    info!("Concurrent requests: {}", args.concurrent_requests);
    info!("Output file: {}", args.discovery_file);

    let client = build_client()?;

    let results =
        discovery::discover_media_questions(&client, &args.base_url, args.concurrent_requests)
            .await
            .context("Failed to discover media questions")?;

    let output_path = std::path::Path::new(&args.discovery_file);
    results.save_to_file(output_path)?;
    info!("Saved discovery results to {}", args.discovery_file);

    let report = results.generate_report();
    let report_path = output_path.with_extension("txt");
    std::fs::write(&report_path, &report)?;
    info!("Saved text report to {}", report_path.display());

    println!("\n{}", report);
    Ok(())
}

async fn run_download(
    args: &Args,
    question_id: Option<&str>,
    all: bool,
    skip_figures: bool,
    skip_tables: bool,
) -> Result<()> {
    if !all && question_id.is_none() {
        info!("No question filter provided; downloading for all discovered questions.");
    }

    let client = build_client()?;

    download::run_media_download(
        &client,
        &args.base_url,
        &args.data_dir,
        &args.discovery_file,
        question_id,
        !skip_figures,
        !skip_tables,
    )
    .await?;

    info!("Media download completed.");
    Ok(())
}

async fn run_browser_download(
    args: &Args,
    question_id: Option<&str>,
    all: bool,
    skip_videos: bool,
    skip_svgs: bool,
    webdriver_url: &str,
    headless: bool,
    interactive_login: bool,
    username: Option<String>,
    password: Option<String>,
    login_timeout_secs: u64,
) -> Result<()> {
    if !all && question_id.is_none() {
        info!("No question filter provided; downloading for all video/svg questions.");
    }

    let client = build_client()?;

    browser_download::run_browser_download(
        &client,
        &args.base_url,
        &args.data_dir,
        &args.discovery_file,
        question_id,
        !skip_videos,
        !skip_svgs,
        webdriver_url,
        headless,
        interactive_login,
        username,
        password,
        login_timeout_secs,
    )
    .await?;

    info!("Browser media download completed.");
    Ok(())
}

fn build_client() -> Result<Client> {
    let session_cookie = session::load_session_cookie()
        .context("Session cookie not set. Set MKSAP_SESSION or login via browser.")?;

    let mut headers = header::HeaderMap::new();
    let cookie_value = format!("_mksap19_session={}", session_cookie);
    headers.insert(
        header::COOKIE,
        header::HeaderValue::from_str(&cookie_value)?,
    );
    info!("Using session cookie from environment");

    if session_cookie.trim().is_empty() {
        warn!("MKSAP_SESSION is empty; API may return 401 Unauthorized.");
    }

    let client = Client::builder().default_headers(headers).build()?;
    Ok(client)
}
