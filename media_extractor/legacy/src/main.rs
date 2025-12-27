use anyhow::Result;
use clap::Parser;
use reqwest::Client;
use tracing::{info, warn};

mod api;
mod browser;
mod discovery;
mod file_store;
mod media;
mod model;
mod render;
mod session;
mod update;

use model::{Args, Command};
use session::load_session_cookie;

#[tokio::main]
async fn main() -> Result<()> {
    tracing_subscriber::fmt()
        .with_max_level(tracing::Level::INFO)
        .init();

    let args = Args::parse();

    match &args.command {
        Some(Command::Discover {
            concurrent_requests,
            output_file,
        }) => {
            run_discovery(&args, *concurrent_requests, output_file).await?;
        }
        Some(Command::Extract {
            question_id,
            all,
            discovery_file,
            format_existing,
            skip_videos,
            skip_svgs,
            headed,
            interactive_login,
        }) => {
            run_extraction(
                &args,
                question_id.as_deref(),
                *all,
                discovery_file.as_deref(),
                *format_existing,
                *skip_videos,
                *skip_svgs,
                *headed,
                *interactive_login,
            )
            .await?;
        }
        None => {
            // Legacy mode: run extraction with top-level args
            run_extraction(
                &args,
                args.question_id.as_deref(),
                args.all,
                None,
                args.format_existing,
                args.skip_videos,
                args.skip_svgs,
                args.headed,
                args.interactive_login,
            )
            .await?;
        }
    }

    Ok(())
}

async fn run_discovery(
    args: &Args,
    concurrent_requests: usize,
    output_file: &str,
) -> Result<()> {
    info!("Starting media discovery...");
    info!("Concurrent requests: {}", concurrent_requests);
    info!("Output file: {}", output_file);

    let client = build_client(None)?; // Discovery doesn't need authentication
    let mut discovery =
        discovery::MediaDiscovery::new(concurrent_requests, args.base_url.clone(), client).await?;

    discovery.initialize().await?;
    let results = discovery.scan_all_questions().await?;

    // Save JSON
    let output_path = std::path::Path::new(output_file);
    results.save_to_file(output_path)?;
    info!("Saved discovery results to {}", output_file);

    // Generate and save text report
    let report = results.generate_report();
    let report_path = output_path.with_extension("txt");
    std::fs::write(&report_path, &report)?;
    info!("Saved text report to {}", report_path.display());

    // Print summary
    println!("\n{}", report);

    Ok(())
}

async fn run_extraction(
    args: &Args,
    question_id: Option<&str>,
    all: bool,
    discovery_file: Option<&str>,
    format_existing: bool,
    skip_videos: bool,
    skip_svgs: bool,
    headed: bool,
    interactive_login: bool,
) -> Result<()> {
    let mut session_cookie = load_session_cookie();

    let entries = file_store::collect_question_entries(&args.data_dir)?;
    let targets = if let Some(discovery_path) = discovery_file {
        info!("Loading discovery results from {}", discovery_path);
        let discovery_filter =
            file_store::load_discovery_results(std::path::Path::new(discovery_path))?;
        let all_targets = file_store::select_targets(&entries, question_id, all)?;
        let filtered: Vec<_> = all_targets
            .into_iter()
            .filter(|entry| discovery_filter.contains(&entry.question_id))
            .collect();
        info!(
            "Filtered to {} questions based on discovery results",
            filtered.len()
        );
        filtered
    } else {
        file_store::select_targets(&entries, question_id, all)?
    };

    let include_videos = !skip_videos;
    let include_svgs = !skip_svgs;

    let password = resolve_password(args)?;

    if (include_videos || include_svgs) && session_cookie.is_none() && interactive_login {
        let login_options = browser::BrowserOptions {
            base_url: args.base_url.clone(),
            webdriver_url: args.webdriver_url.clone(),
            headless: false,
            interactive_login: true,
            username: args.username.clone(),
            password: password.clone(),
            login_timeout: std::time::Duration::from_secs(args.login_timeout_seconds),
            session_cookie: None,
        };
        let login_session = browser::BrowserSession::connect(&login_options).await?;
        login_session.ensure_login(&login_options).await?;
        session_cookie = load_session_cookie();
    }

    let client = build_client(session_cookie.as_deref())?;

    let browser = if include_videos || include_svgs {
        let options = browser::BrowserOptions {
            base_url: args.base_url.clone(),
            webdriver_url: args.webdriver_url.clone(),
            headless: !headed,
            interactive_login,
            username: args.username.clone(),
            password: password.clone(),
            login_timeout: std::time::Duration::from_secs(args.login_timeout_seconds),
            session_cookie: session_cookie.clone(),
        };
        let session = browser::BrowserSession::connect(&options).await?;
        session.ensure_login(&options).await?;
        Some(session)
    } else {
        None
    };

    info!("Processing {} questions for media extraction", targets.len());
    update::run_media_extraction(
        &client,
        &args.base_url,
        &targets,
        browser,
        include_videos,
        include_svgs,
    )
    .await?;
    if format_existing {
        let formatted = file_store::format_existing_tables(&args.data_dir)?;
        info!("Reformatted {} table HTML files", formatted);
    }
    info!("Media extraction completed.");
    Ok(())
}

fn build_client(session_cookie: Option<&str>) -> Result<Client> {
    let mut headers = reqwest::header::HeaderMap::new();
    if let Some(session_cookie) = session_cookie {
        let cookie_value = format!("_mksap19_session={}", session_cookie);
        headers.insert(reqwest::header::COOKIE, cookie_value.parse()?);
    } else {
        warn!("MKSAP_SESSION not set and no cached session found; API may return 401 Unauthorized.");
    }

    Ok(Client::builder().default_headers(headers).build()?)
}

fn resolve_password(args: &Args) -> Result<Option<String>> {
    if let Some(password) = args.password.clone() {
        return Ok(Some(password));
    }
    if args.username.is_some() {
        let password = rpassword::prompt_password("MKSAP password (input hidden): ")?;
        if password.trim().is_empty() {
            return Ok(None);
        }
        return Ok(Some(password));
    }
    Ok(None)
}
