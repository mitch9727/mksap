use anyhow::{Context, Result};
use std::fs;
use tracing::{error, info};

mod auth_flow;
mod browser;
mod categories;
mod commands;
mod config;
mod diagnostics;
mod extractor;
mod models;
mod reporting;
mod validator;

use auth_flow::authenticate_extractor;
use categories::build_categories_from_config;
use commands::Command;
use diagnostics::inspect_api;
use extractor::MKSAPExtractor;
use reporting::{
    count_discovered_ids, show_discovery_stats, total_discovered_ids, validate_extraction,
};

#[tokio::main]
async fn main() -> Result<()> {
    // Load .env file if present (before any env::var calls)
    dotenv::dotenv().ok();

    // Initialize logging
    tracing_subscriber::fmt()
        .with_max_level(tracing::Level::INFO)
        .init();

    info!("MKSAP Question Bank Extractor (Rust)");
    info!("=====================================");

    let args: Vec<String> = std::env::args().collect();
    let command = Command::parse(&args);

    let base_url = "https://mksap.acponline.org";
    let output_dir = "../mksap_data";
    let session_cookie = std::env::var("MKSAP_SESSION").unwrap_or_else(|_| String::new());

    match command {
        Command::Validate => return validate_extraction(output_dir).await,
        Command::CleanupRetired => {
            info!("=== CLEANING UP RETIRED QUESTIONS ===");
            let mut extractor = MKSAPExtractor::new(base_url, output_dir)?;
            extractor = extractor.with_session_cookie(&session_cookie);
            let moved = extractor.cleanup_retired_questions().await?;
            info!(
                "\n✓ Cleanup complete: {} retired questions moved to mksap_data_failed/retired/",
                moved
            );
            return Ok(());
        }
        Command::CleanupFlat => {
            info!("=== CLEANING UP FLAT DUPLICATE JSON FILES ===");
            let extractor = MKSAPExtractor::new(base_url, output_dir)?;
            let deleted = extractor.cleanup_flat_duplicates()?;
            info!("\n✓ Cleanup complete: {} flat duplicates deleted", deleted);
            return Ok(());
        }
        Command::DiscoveryStats => return show_discovery_stats(output_dir).await,
        _ => {}
    }

    // Create output directory
    fs::create_dir_all(output_dir).context("Failed to create output directory")?;

    // Build categories from config (DRY: no hardcoded duplication)
    let categories = build_categories_from_config();

    let mut extractor = MKSAPExtractor::new(base_url, output_dir)?;

    // Configure the HTTP client with the session cookie for API authentication
    extractor = extractor.with_session_cookie(&session_cookie);

    if command.requires_auth() {
        // Authenticate using consolidated helper function (flattens nesting from 5+ to 2-3 levels)
        authenticate_extractor(&mut extractor).await?;
    }

    // Phase 1: Inspect API response to understand JSON schema
    if std::env::var("MKSAP_INSPECT_API").is_ok() {
        info!("=== PHASE 1: INSPECTING API RESPONSE ===");
        match inspect_api(&extractor).await {
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

    info!("\n=== PHASE 2: FULL CATEGORY EXTRACTION ===");
    info!(
        "Starting extraction for all {} categories...\n",
        categories.len()
    );

    let mut total_extracted = 0;
    let start_time = std::time::Instant::now();

    if let Command::RetryMissing = command {
        let recovered = extractor.retry_missing_json().await?;
        info!("Missing JSON recovery complete ({} recovered)", recovered);
        return Ok(());
    }
    if let Command::ListMissing = command {
        let remaining = extractor.list_remaining_ids(&categories).await?;
        info!("Remaining IDs list complete ({} IDs)", remaining);
        return Ok(());
    }

    for (idx, category) in categories.iter().enumerate() {
        info!(
            "\n[{}/{}] Processing: {}",
            idx + 1,
            categories.len(),
            category.name
        );

        match extractor.extract_category(category).await {
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

    let total_questions = total_discovered_ids(output_dir, &categories);

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
