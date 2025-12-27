use anyhow::Result;
use mksap_extractor::{
    authenticate_extractor, build_categories_from_config, count_discovered_ids, inspect_api,
    show_discovery_stats, total_discovered_ids, validate_extraction, Category, Command,
    MKSAPExtractor,
};
use std::env;
use tracing::{error, info};

const DOTENV_PATH: &str = "../.env";
const BASE_URL: &str = "https://mksap.acponline.org";
const OUTPUT_DIR: &str = "../mksap_data";

#[derive(Debug)]
struct StandardizeOptions {
    dry_run: bool,
    system_filter: Option<String>,
}

#[derive(Debug)]
struct RunOptions {
    refresh_existing: bool,
}

#[tokio::main]
async fn main() -> Result<()> {
    load_env();
    init_tracing();

    info!("MKSAP Question Bank Extractor (Rust)");
    info!("=====================================");

    let args: Vec<String> = env::args().collect();
    let command = Command::parse(&args);

    let session_cookie = env::var("MKSAP_SESSION").unwrap_or_default();

    if handle_standalone_command(command, &args, &session_cookie).await? {
        return Ok(());
    }

    // Build categories from config (DRY: no hardcoded duplication)
    let categories = build_categories_from_config();

    let mut extractor = MKSAPExtractor::new(BASE_URL, OUTPUT_DIR)?;

    // Configure the HTTP client with the session cookie for API authentication
    extractor = extractor.with_session_cookie(&session_cookie);

    if command.requires_auth() {
        // Authenticate using consolidated helper function (flattens nesting from 5+ to 2-3 levels)
        authenticate_extractor(&mut extractor).await?;
    }

    // Phase 1: Inspect API response to understand JSON schema
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
        _ => {}
    }

    Ok(())
}

fn load_env() {
    // Load .env file from project root (before any env::var calls)
    dotenv::from_path(DOTENV_PATH).ok();
}

fn init_tracing() {
    // Initialize logging
    tracing_subscriber::fmt()
        .with_max_level(tracing::Level::INFO)
        .init();
}

fn parse_standardize_options(args: &[String]) -> StandardizeOptions {
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

fn parse_run_options(args: &[String]) -> RunOptions {
    let refresh_existing = args.iter().any(|arg| {
        arg == "--refresh-existing" || arg == "--overwrite-existing" || arg == "--overwrite"
    });

    RunOptions { refresh_existing }
}

async fn handle_standalone_command(
    command: Command,
    args: &[String],
    session_cookie: &str,
) -> Result<bool> {
    match command {
        Command::Validate => {
            validate_extraction(OUTPUT_DIR).await?;
            Ok(true)
        }
        Command::Standardize => {
            info!("=== STANDARDIZING JSON FILES ===");
            let options = parse_standardize_options(args);
            mksap_extractor::run_standardization(
                OUTPUT_DIR,
                options.dry_run,
                options.system_filter.as_deref(),
            )
            .await?;
            Ok(true)
        }
        Command::CleanupRetired => {
            info!("=== CLEANING UP RETIRED QUESTIONS ===");
            let mut extractor = MKSAPExtractor::new(BASE_URL, OUTPUT_DIR)?;
            extractor = extractor.with_session_cookie(session_cookie);
            let moved = extractor.cleanup_retired_questions().await?;
            info!(
                "\n✓ Cleanup complete: {} retired questions moved to mksap_data_failed/retired/",
                moved
            );
            Ok(true)
        }
        Command::CleanupFlat => {
            info!("=== CLEANING UP FLAT DUPLICATE JSON FILES ===");
            let extractor = MKSAPExtractor::new(BASE_URL, OUTPUT_DIR)?;
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

async fn maybe_inspect_api(extractor: &MKSAPExtractor) -> Result<()> {
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

async fn run_extraction(
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

                // Load checkpoint to calculate extracted vs already-extracted
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
