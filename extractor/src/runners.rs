//! Command execution orchestration for extraction and media workflows.

use anyhow::Result;
use std::fs;
use std::path::Path;
use tracing::{debug, error, info};

use crate::assets::{asset_discovery, asset_download, svg_download};
use crate::cli::MediaOptions;
use crate::reporting::{count_discovered_ids, total_discovered_ids};
use crate::utils::log_progress;
use crate::{Category, MKSAPExtractor};

pub async fn run_extraction(
    extractor: &MKSAPExtractor,
    categories: &[Category],
    output_dir: &str,
    refresh_existing: bool,
) -> Result<()> {
    debug!("\n=== PHASE 2: FULL CATEGORY EXTRACTION ===");
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
        log_progress(
            idx + 1,
            categories.len(),
            &format!("Processing: {}", category.name),
        );

        match extractor.extract_category(category, refresh_existing).await {
            Ok(count) => {
                total_extracted += count;

                let total_discovered = count_discovered_ids(output_dir, &category.code);
                let total_discovered = if total_discovered == 0 {
                    count
                } else {
                    total_discovered
                };
                let already_extracted = total_discovered.saturating_sub(count);

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
        total_questions.saturating_sub(total_extracted)
    );
    info!("Time elapsed: {:.2} minutes", elapsed.as_secs_f64() / 60.0);
    info!("Output directory: {}", output_dir);

    Ok(())
}

pub async fn run_media_discovery(options: &MediaOptions) -> Result<()> {
    info!("Starting media discovery via API");
    info!("Base URL: {}", options.base_url);
    info!("Concurrent requests: {}", options.concurrent_requests);
    info!("Output file: {}", options.discovery_file);

    let client = crate::assets::build_client()?;
    let results = asset_discovery::discover_media_questions(
        &client,
        &options.base_url,
        options.concurrent_requests,
    )
    .await?;

    let output_path = Path::new(&options.discovery_file);
    if let Some(parent) = output_path.parent() {
        if !parent.as_os_str().is_empty() {
            fs::create_dir_all(parent)?;
        }
    }

    results.save_to_file(output_path)?;
    info!("Saved discovery results to {}", options.discovery_file);

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

pub async fn run_media_download(options: &MediaOptions) -> Result<()> {
    if !options.all && options.question_id.is_none() {
        info!("No question filter provided; downloading for all discovered questions.");
    }

    let client = crate::assets::build_client()?;
    asset_download::run_media_download(
        &client,
        &options.base_url,
        &options.data_dir,
        &options.discovery_file,
        options.question_id.as_deref(),
        !options.skip_figures,
        !options.skip_tables,
    )
    .await?;

    info!("Media download completed.");
    Ok(())
}

pub async fn run_svg_browser(options: &MediaOptions) -> Result<()> {
    info!("Video files require manual download; browser step handles SVGs only.");

    if !options.all && options.question_id.is_none() {
        info!("No question filter provided; downloading for all SVG questions.");
    }

    let client = crate::assets::build_client()?;
    svg_download::run_svg_download(
        &client,
        &options.base_url,
        &options.data_dir,
        &options.discovery_file,
        options.question_id.as_deref(),
        !options.skip_svgs,
        &options.webdriver_url,
        options.headless,
        options.interactive_login,
        options.username.clone(),
        options.password.clone(),
        options.login_timeout_secs,
    )
    .await?;

    info!("SVG browser download completed.");
    Ok(())
}
