use anyhow::Result;
use std::env;
use std::fs;
use std::path::Path;
use tracing::{error, info};

use crate::assets::{asset_discovery, asset_download, svg_download};

use crate::{
    authenticate_extractor, build_categories_from_config, count_discovered_ids,
    show_discovery_stats, total_discovered_ids, validate_extraction, Category, Command,
    MKSAPExtractor,
};

pub const DOTENV_PATH: &str = "../.env";
pub const BASE_URL: &str = "https://mksap.acponline.org";
pub const OUTPUT_DIR: &str = "../mksap_data";

#[derive(Debug)]
pub struct StandardizeOptions {
    pub dry_run: bool,
    pub system_filter: Option<String>,
}

#[derive(Debug)]
pub struct RunOptions {
    pub refresh_existing: bool,
}

pub async fn run(args: Vec<String>) -> Result<()> {
    load_env();
    init_tracing();

    info!("MKSAP Question Bank Extractor (Rust)");
    info!("=====================================");

    let command = Command::parse(&args);
    let session_cookie = crate::session::load_session_cookie();
    let base_url = resolve_media_base_url(&args);

    if handle_standalone_command(command, &args, session_cookie.as_deref(), &base_url).await? {
        return Ok(());
    }

    let categories = build_categories_from_config();
    let mut extractor = MKSAPExtractor::new(&base_url, OUTPUT_DIR)?;
    if let Some(cookie) = session_cookie.as_deref() {
        extractor = extractor.with_session_cookie(cookie);
    }

    if command.requires_auth() {
        authenticate_extractor(&mut extractor).await?;
    }

    maybe_inspect_api(&extractor).await?;

    match command {
        Command::RetryMissing => {
            let recovered = extractor.retry_missing_json().await?;
            info!("Missing JSON recovery complete ({} recovered)", recovered);
        }
        Command::ListMissing => {
            let remaining = extractor.list_remaining_ids(&categories).await?;
            info!("Remaining IDs list complete ({} IDs)", remaining);
        }
        Command::Run => {
            let options = parse_run_options(&args);
            run_extraction(
                &extractor,
                &categories,
                OUTPUT_DIR,
                options.refresh_existing,
            )
            .await?;
        }
        Command::MediaDiscover => {
            run_media_discovery(&args).await?;
        }
        Command::MediaDownload => {
            run_media_download(&args).await?;
        }
        Command::SvgBrowser => {
            run_svg_browser(&args).await?;
        }
        Command::ExtractAll => {
            let options = parse_run_options(&args);
            run_extraction(
                &extractor,
                &categories,
                OUTPUT_DIR,
                options.refresh_existing,
            )
            .await?;
            run_media_discovery(&args).await?;
            run_media_download(&args).await?;
            if has_flag(&args, "--with-browser") {
                run_svg_browser(&args).await?;
            }
        }
        _ => {}
    }

    Ok(())
}

pub fn load_env() {
    dotenv::from_path(DOTENV_PATH).ok();
}

pub fn init_tracing() {
    tracing_subscriber::fmt()
        .with_max_level(tracing::Level::INFO)
        .init();
}

pub fn parse_standardize_options(args: &[String]) -> StandardizeOptions {
    let dry_run = args.iter().any(|arg| arg == "--dry-run");
    let system_filter = args
        .iter()
        .position(|arg| arg == "--system")
        .and_then(|idx| args.get(idx + 1))
        .cloned();

    StandardizeOptions {
        dry_run,
        system_filter,
    }
}

pub fn parse_run_options(args: &[String]) -> RunOptions {
    let refresh_existing = args.iter().any(|arg| {
        arg == "--refresh-existing" || arg == "--overwrite-existing" || arg == "--overwrite"
    });

    RunOptions { refresh_existing }
}

pub async fn handle_standalone_command(
    command: Command,
    args: &[String],
    session_cookie: Option<&str>,
    base_url: &str,
) -> Result<bool> {
    match command {
        Command::Validate => {
            validate_extraction(OUTPUT_DIR).await?;
            Ok(true)
        }
        Command::Standardize => {
            info!("=== STANDARDIZING JSON FILES ===");
            let options = parse_standardize_options(args);
            crate::run_standardization(
                OUTPUT_DIR,
                options.dry_run,
                options.system_filter.as_deref(),
            )
            .await?;
            Ok(true)
        }
        Command::CleanupRetired => {
            info!("=== CLEANING UP RETIRED QUESTIONS ===");
            let mut extractor = MKSAPExtractor::new(base_url, OUTPUT_DIR)?;
            if let Some(cookie) = session_cookie {
                extractor = extractor.with_session_cookie(cookie);
            }
            let moved = extractor.cleanup_retired_questions().await?;
            info!(
                "\n✓ Cleanup complete: {} retired questions moved to mksap_data_failed/retired/",
                moved
            );
            Ok(true)
        }
        Command::CleanupFlat => {
            info!("=== CLEANING UP FLAT DUPLICATE JSON FILES ===");
            let extractor = MKSAPExtractor::new(base_url, OUTPUT_DIR)?;
            let deleted = extractor.cleanup_flat_duplicates()?;
            info!("\n✓ Cleanup complete: {} flat duplicates deleted", deleted);
            Ok(true)
        }
        Command::DiscoveryStats => {
            show_discovery_stats(OUTPUT_DIR).await?;
            Ok(true)
        }
        _ => Ok(false),
    }
}

pub async fn maybe_inspect_api(extractor: &MKSAPExtractor) -> Result<()> {
    if env::var_os("MKSAP_INSPECT_API").is_some() {
        info!("=== PHASE 1: INSPECTING API RESPONSE ===");
        match inspect_api(extractor).await {
            Ok(_) => {
                info!("API inspection complete.");
            }
            Err(e) => {
                error!("Failed to inspect API: {}", e);
                return Err(e);
            }
        }
    } else {
        info!("Skipping API inspection (set MKSAP_INSPECT_API=1 to enable).");
    }

    Ok(())
}

pub async fn inspect_api(extractor: &MKSAPExtractor) -> Result<()> {
    let url = crate::endpoints::question_json(BASE_URL, "cvmcq25001");

    println!("\n=== FETCHING API RESPONSE ===");
    println!("URL: {}", url);
    println!("\nNote: If you see 'Not authorized', the browser cookies may not be available to this Rust process.");
    println!(
        "The browser login adds cookies to Chrome's local storage, but the Rust HTTP client needs"
    );
    println!("those cookies passed explicitly via HTTP headers or a CookieStore.\n");

    let response = extractor.client.get(url).send().await?;
    let json_text = response.text().await?;

    println!("=== RAW JSON RESPONSE ===");
    println!("{}", json_text);

    let value: serde_json::Value = serde_json::from_str(&json_text)?;
    println!("\n=== PRETTY JSON ===");
    println!("{}", serde_json::to_string_pretty(&value)?);

    if let Some(error) = value.get("error") {
        let error_msg = format!(
            "\n⚠️  API returned an error: {}\n\nIMPORTANT: The API requires authentication cookies!\n\
             The browser authenticated using your local Chrome session, but those cookies\n\
             aren't automatically available to the Rust HTTP client.\n\n\
             To proceed with testing, you have two options:\n\
             1. Manually extract MKSAP_SESSION cookie from Chrome and configure the client\n\
             2. Ensure the Rust extractor has valid session cookies configured",
            error
        );
        println!("{}", error_msg);
    }

    Ok(())
}

pub async fn run_extraction(
    extractor: &MKSAPExtractor,
    categories: &[Category],
    output_dir: &str,
    refresh_existing: bool,
) -> Result<()> {
    info!("\n=== PHASE 2: FULL CATEGORY EXTRACTION ===");
    info!(
        "Starting extraction for all {} categories...\n",
        categories.len()
    );
    if refresh_existing {
        info!("Refresh mode enabled: re-downloading existing question JSON.");
    }

    let mut total_extracted = 0;
    let start_time = std::time::Instant::now();

    for (idx, category) in categories.iter().enumerate() {
        info!(
            "\n[{}/{}] Processing: {}",
            idx + 1,
            categories.len(),
            category.name
        );

        match extractor.extract_category(category, refresh_existing).await {
            Ok(count) => {
                total_extracted += count;

                let total_discovered = count_discovered_ids(output_dir, &category.code);
                let total_discovered = if total_discovered == 0 {
                    count as usize
                } else {
                    total_discovered
                };
                let already_extracted = total_discovered.saturating_sub(count as usize);

                info!(
                    "✓ {}: Extracted {} new, {} already extracted",
                    category.code, count, already_extracted
                );
            }
            Err(e) => {
                error!("✗ Extraction failed: {}", e);
            }
        }
    }

    let total_questions = total_discovered_ids(output_dir, categories);

    let elapsed = start_time.elapsed();
    info!("\n=== EXTRACTION COMPLETE ===");
    info!("Total questions available: {}", total_questions);
    info!("  New extracted: {}", total_extracted);
    info!(
        "  Already extracted: {}",
        total_questions.saturating_sub(total_extracted as usize)
    );
    info!("Time elapsed: {:.2} minutes", elapsed.as_secs_f64() / 60.0);
    info!("Output directory: {}", output_dir);

    Ok(())
}

async fn run_media_discovery(args: &[String]) -> Result<()> {
    info!("Starting media discovery via API");
    let base_url = resolve_media_base_url(args);
    let concurrent = resolve_media_concurrency(args);
    let discovery_file = resolve_media_discovery_file(args);

    info!("Base URL: {}", base_url);
    info!("Concurrent requests: {}", concurrent);
    info!("Output file: {}", discovery_file);

    let client = crate::assets::build_client()?;
    let results = asset_discovery::discover_media_questions(&client, &base_url, concurrent).await?;

    let output_path = Path::new(&discovery_file);
    if let Some(parent) = output_path.parent() {
        if !parent.as_os_str().is_empty() {
            fs::create_dir_all(parent)?;
        }
    }

    results.save_to_file(output_path)?;
    info!("Saved discovery results to {}", discovery_file);

    let report = results.generate_report();
    let report_path = output_path.with_extension("txt");
    fs::write(&report_path, &report)?;
    info!("Saved text report to {}", report_path.display());

    if !results.metadata.statistics.video_question_ids.is_empty() {
        info!(
            "Video files are not downloaded automatically. Use the VIDEO QUESTION IDS in {} for manual downloads.",
            report_path.display()
        );
    }

    println!("\n{}", report);
    Ok(())
}

async fn run_media_download(args: &[String]) -> Result<()> {
    let base_url = resolve_media_base_url(args);
    let data_dir = resolve_media_data_dir(args);
    let discovery_file = resolve_media_discovery_file(args);
    let question_id = parse_arg_value(args, "--question-id");
    let all = has_flag(args, "--all");
    let skip_figures = has_flag(args, "--skip-figures");
    let skip_tables = has_flag(args, "--skip-tables");

    if !all && question_id.is_none() {
        info!("No question filter provided; downloading for all discovered questions.");
    }

    let client = crate::assets::build_client()?;
    asset_download::run_media_download(
        &client,
        &base_url,
        &data_dir,
        &discovery_file,
        question_id.as_deref(),
        !skip_figures,
        !skip_tables,
    )
    .await?;

    info!("Media download completed.");
    Ok(())
}

async fn run_svg_browser(args: &[String]) -> Result<()> {
    let base_url = resolve_media_base_url(args);
    let data_dir = resolve_media_data_dir(args);
    let discovery_file = resolve_media_discovery_file(args);
    let question_id = parse_arg_value(args, "--question-id");
    let all = has_flag(args, "--all");
    let skip_svgs = has_flag(args, "--skip-svgs");
    let webdriver_url = parse_arg_value(args, "--webdriver-url")
        .unwrap_or_else(|| "http://localhost:9515".to_string());
    let headless = parse_bool_arg(args, "--headless", true);
    let interactive_login = parse_bool_arg(args, "--interactive-login", false);
    let username = parse_arg_value(args, "--username");
    let password = parse_arg_value(args, "--password");
    let login_timeout_secs = parse_arg_value(args, "--login-timeout-secs")
        .and_then(|value| value.parse::<u64>().ok())
        .unwrap_or(120);

    info!("Video files require manual download; browser step handles SVGs only.");

    if !all && question_id.is_none() {
        info!("No question filter provided; downloading for all SVG questions.");
    }

    let client = crate::assets::build_client()?;
    svg_download::run_svg_download(
        &client,
        &base_url,
        &data_dir,
        &discovery_file,
        question_id.as_deref(),
        !skip_svgs,
        &webdriver_url,
        headless,
        interactive_login,
        username,
        password,
        login_timeout_secs,
    )
    .await?;

    info!("SVG browser download completed.");
    Ok(())
}

fn resolve_media_base_url(args: &[String]) -> String {
    parse_arg_value(args, "--base-url").unwrap_or_else(|| BASE_URL.to_string())
}

fn resolve_media_data_dir(args: &[String]) -> String {
    parse_arg_value(args, "--data-dir").unwrap_or_else(|| OUTPUT_DIR.to_string())
}

fn resolve_media_discovery_file(args: &[String]) -> String {
    parse_arg_value(args, "--discovery-file").unwrap_or_else(|| {
        Path::new(OUTPUT_DIR)
            .join("media_discovery.json")
            .to_string_lossy()
            .to_string()
    })
}

fn resolve_media_concurrency(args: &[String]) -> usize {
    parse_arg_value(args, "--concurrent-requests")
        .and_then(|value| value.parse::<usize>().ok())
        .filter(|value| *value > 0)
        .unwrap_or(10)
}

fn parse_arg_value(args: &[String], key: &str) -> Option<String> {
    let prefix = format!("{}=", key);
    for (idx, arg) in args.iter().enumerate() {
        if let Some(value) = arg.strip_prefix(&prefix) {
            return Some(value.to_string());
        }
        if arg == key {
            if let Some(value) = args.get(idx + 1) {
                if !value.starts_with('-') {
                    return Some(value.to_string());
                }
            }
        }
    }
    None
}

fn has_flag(args: &[String], flag: &str) -> bool {
    args.iter().any(|arg| arg == flag)
}

fn parse_bool_arg(args: &[String], flag: &str, default: bool) -> bool {
    if let Some(value) = parse_arg_value(args, flag) {
        match value.to_ascii_lowercase().as_str() {
            "true" | "1" | "yes" => return true,
            "false" | "0" | "no" => return false,
            _ => return default,
        }
    }

    if has_flag(args, flag) {
        return true;
    }

    default
}
