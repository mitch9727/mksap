//! Command routing and standalone command handling.

use anyhow::Result;
use tracing::info;

use crate::app::maybe_inspect_api;
use crate::cli::{has_flag, parse_run_options, parse_standardize_options, MediaOptions};
use crate::runners::{run_extraction, run_media_discovery, run_media_download, run_svg_browser};
use crate::session::load_session_cookie;
use crate::{
    authenticate_extractor, build_categories_from_config, show_discovery_stats,
    validate_extraction, Command, MKSAPExtractor, OUTPUT_DIR,
};

pub async fn handle_command(command: Command, args: &[String]) -> Result<()> {
    let session_cookie = load_session_cookie();
    let media_options = MediaOptions::from_args(args);
    let base_url = media_options.base_url.clone();

    if handle_standalone_command(command, args, session_cookie.as_deref(), &base_url).await? {
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
            let options = parse_run_options(args);
            run_extraction(
                &extractor,
                &categories,
                OUTPUT_DIR,
                options.refresh_existing,
            )
            .await?;
        }
        Command::MediaDiscover => {
            run_media_discovery(&media_options).await?;
        }
        Command::MediaDownload => {
            run_media_download(&media_options).await?;
        }
        Command::SvgBrowser => {
            run_svg_browser(&media_options).await?;
        }
        Command::ExtractAll => {
            let options = parse_run_options(args);
            run_extraction(
                &extractor,
                &categories,
                OUTPUT_DIR,
                options.refresh_existing,
            )
            .await?;
            run_media_discovery(&media_options).await?;
            run_media_download(&media_options).await?;
            if has_flag(args, "--with-browser") {
                run_svg_browser(&media_options).await?;
            }
        }
        _ => {}
    }

    Ok(())
}

pub async fn handle_standalone_command(
    command: Command,
    args: &[String],
    session_cookie: Option<&str>,
    base_url: &str,
) -> Result<bool> {
    match command {
        Command::Validate => {
            handle_validate().await?;
            Ok(true)
        }
        Command::Standardize => {
            handle_standardize(args).await?;
            Ok(true)
        }
        Command::CleanupRetired => {
            handle_cleanup_retired(session_cookie, base_url).await?;
            Ok(true)
        }
        Command::CleanupFlat => {
            handle_cleanup_flat(base_url).await?;
            Ok(true)
        }
        Command::DiscoveryStats => {
            handle_discovery_stats().await?;
            Ok(true)
        }
        _ => Ok(false),
    }
}

async fn handle_validate() -> Result<()> {
    validate_extraction(OUTPUT_DIR).await?;
    Ok(())
}

async fn handle_standardize(args: &[String]) -> Result<()> {
    info!("=== STANDARDIZING JSON FILES ===");
    let options = parse_standardize_options(args);
    crate::run_standardization(
        OUTPUT_DIR,
        options.dry_run,
        options.system_filter.as_deref(),
    )
    .await?;
    Ok(())
}

async fn handle_cleanup_retired(session_cookie: Option<&str>, base_url: &str) -> Result<()> {
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
    Ok(())
}

async fn handle_cleanup_flat(base_url: &str) -> Result<()> {
    info!("=== CLEANING UP FLAT DUPLICATE JSON FILES ===");
    let extractor = MKSAPExtractor::new(base_url, OUTPUT_DIR)?;
    let deleted = extractor.cleanup_flat_duplicates()?;
    info!("\n✓ Cleanup complete: {} flat duplicates deleted", deleted);
    Ok(())
}

async fn handle_discovery_stats() -> Result<()> {
    show_discovery_stats(OUTPUT_DIR).await?;
    Ok(())
}
