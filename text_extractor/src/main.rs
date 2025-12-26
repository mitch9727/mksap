use anyhow::{Context, Result};
use serde::{Deserialize, Serialize};
use std::fs;
use std::path::Path;
use tracing::{error, info, warn};
use tracing_subscriber;

mod browser;
mod config;
mod extractor;
mod models;
mod validator;

use extractor::MKSAPExtractor;
use models::DiscoveryMetadataCollection;
use validator::DataValidator;

#[derive(Debug, Clone, Serialize, Deserialize)]
struct Category {
    code: String,
    name: String,
    path: String,
    question_prefix: String,
}

async fn validate_extraction(output_dir: &str) -> Result<()> {
    info!("\n=== VALIDATING EXTRACTED DATA ===");
    info!("Scanning mksap_data directory for extracted questions...\n");

    let result = DataValidator::validate_extraction(output_dir)?;

    println!("\n{}", DataValidator::generate_report(&result));
    println!("\n{}", DataValidator::compare_with_specification(&result));

    // Save detailed report
    let report_path = format!("{}/validation_report.txt", output_dir);
    let mut report = DataValidator::generate_report(&result);
    report.push_str("\n\n");
    report.push_str(&DataValidator::compare_with_specification(&result));

    fs::write(&report_path, report).context("Failed to write validation report")?;

    info!("Validation report saved to {}", report_path);

    Ok(())
}

async fn show_discovery_stats(output_dir: &str) -> Result<()> {
    let metadata_path = Path::new(output_dir)
        .join(".checkpoints")
        .join("discovery_metadata.json");

    if !metadata_path.exists() {
        println!("\n❌ No discovery metadata found.");
        println!("Run extraction first to generate discovery data.\n");
        return Ok(());
    }

    let contents = fs::read_to_string(&metadata_path)?;
    let metadata: DiscoveryMetadataCollection = serde_json::from_str(&contents)?;

    println!("\n=== MKSAP Discovery Statistics ===\n");
    println!("Last Updated: {}\n", metadata.last_updated);

    let total_discovered: usize = metadata.systems.iter().map(|s| s.discovered_count).sum();
    let total_candidates: usize = metadata.systems.iter().map(|s| s.candidates_tested).sum();
    let overall_hit_rate = if total_candidates > 0 {
        (total_discovered as f64 / total_candidates as f64) * 100.0
    } else {
        0.0
    };

    println!("Overall:");
    println!("  Total Discovered: {} questions", total_discovered);
    println!("  Total Candidates Tested: {}", total_candidates);
    println!("  Overall Hit Rate: {:.2}%\n", overall_hit_rate);

    println!("Per-System Breakdown:");
    println!(
        "{:<6} {:>10} {:>15} {:>10} {}",
        "System", "Discovered", "Candidates", "Hit Rate", "Types Found"
    );
    println!("{}", "-".repeat(70));

    for sys in &metadata.systems {
        println!(
            "{:<6} {:>10} {:>15} {:>9.2}% {}",
            sys.system_code,
            sys.discovered_count,
            sys.candidates_tested,
            sys.hit_rate * 100.0,
            sys.question_types_found.join(",")
        );
    }

    println!();
    Ok(())
}

/// Perform authentication with fallback strategy.
///
/// Tries in order:
/// 1. Check if already authenticated (HTTP check)
/// 2. Automatic login with credentials
/// 3. Browser-based login (interactive)
///
/// Logs all results and warns on failures, but doesn't error out.
async fn authenticate_extractor(extractor: &mut MKSAPExtractor) -> Result<()> {
    let username = std::env::var("MKSAP_USERNAME").unwrap_or_else(|_| {
        warn!("MKSAP_USERNAME not set in environment");
        String::new()
    });
    let password = std::env::var("MKSAP_PASSWORD").unwrap_or_else(|_| {
        warn!("MKSAP_PASSWORD not set in environment");
        String::new()
    });

    // Step 1: Check if already authenticated
    info!("Step 0: Checking if already authenticated...");
    match extractor.is_already_authenticated().await {
        Ok(true) => {
            info!("✓ Already authenticated, proceeding with extraction");
            extractor.set_authenticated(true);
            return Ok(());
        }
        Ok(false) => {
            info!("Not yet authenticated, attempting login...");
        }
        Err(e) => {
            warn!("Could not check authentication status: {}", e);
            info!("Attempting standard login flow...");
        }
    }

    // Step 2: Try automatic login
    info!("Step 1: Attempting automatic login with provided credentials...");
    match extractor.login(&username, &password).await {
        Ok(_) if extractor.is_authenticated() => {
            info!("✓ Authentication successful, proceeding with extraction");
            return Ok(());
        }
        Ok(_) => {
            // Check if authentication now works via HTTP
            if let Ok(true) = extractor.is_already_authenticated().await {
                info!("✓ Authentication successful via HTTP check");
                extractor.set_authenticated(true);
                return Ok(());
            }
        }
        Err(e) => {
            warn!("Step 2: Automatic authentication error: {}", e);
        }
    }

    // Step 3: Fall back to browser login
    info!("Attempting browser-based login as fallback...");
    match extractor.browser_login(&username, &password).await {
        Ok(_) => {
            info!("✓ Browser login successful!");
            Ok(())
        }
        Err(e) => {
            warn!("Browser login not available: {}", e);
            info!("Proceeding without authentication (some content may not be accessible)");
            Ok(())
        }
    }
}

/// Build categories from config-driven organ systems with web UI paths.
///
/// Maps each organ system to its MKSAP web UI path pattern.
fn build_categories_from_config() -> Vec<Category> {
    // Path mappings for AND content areas (web UI groups multiple systems)
    let path_map = std::collections::HashMap::from([
        (
            "cv",
            "/app/question-bank/content-areas/cv/answered-questions",
        ),
        (
            "en",
            "/app/question-bank/content-areas/en/answered-questions",
        ),
        (
            "cs",
            "/app/question-bank/content-areas/fccs/answered-questions",
        ),
        (
            "hm",
            "/app/question-bank/content-areas/hm/answered-questions",
        ),
        (
            "id",
            "/app/question-bank/content-areas/id/answered-questions",
        ),
        (
            "np",
            "/app/question-bank/content-areas/np/answered-questions",
        ),
        (
            "nr",
            "/app/question-bank/content-areas/nr/answered-questions",
        ),
        (
            "on",
            "/app/question-bank/content-areas/on/answered-questions",
        ),
        (
            "rm",
            "/app/question-bank/content-areas/rm/answered-questions",
        ),
        // AND content areas
        (
            "gi",
            "/app/question-bank/content-areas/gihp/answered-questions",
        ),
        (
            "hp",
            "/app/question-bank/content-areas/gihp/answered-questions",
        ),
        (
            "in",
            "/app/question-bank/content-areas/dmin/answered-questions",
        ),
        (
            "dm",
            "/app/question-bank/content-areas/dmin/answered-questions",
        ),
        (
            "pm",
            "/app/question-bank/content-areas/pmcc/answered-questions",
        ),
        (
            "cc",
            "/app/question-bank/content-areas/pmcc/answered-questions",
        ),
    ]);

    config::init_organ_systems()
        .into_iter()
        .map(|sys| Category {
            code: sys.id.clone(),
            name: sys.name,
            path: path_map
                .get(sys.id.as_str())
                .copied()
                .unwrap_or("/app/question-bank")
                .to_string(),
            question_prefix: sys.id,
        })
        .collect()
}

async fn inspect_api(extractor: &MKSAPExtractor) -> Result<()> {
    let url = "https://mksap.acponline.org/api/questions/cvmcq25001.json";

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

    // Check the response to see if it's an error
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
    let base_url = "https://mksap.acponline.org";
    let output_dir = "../mksap_data";
    let session_cookie = std::env::var("MKSAP_SESSION").unwrap_or_else(|_| String::new());

    if args.len() > 1 && args[1] == "validate" {
        return validate_extraction(output_dir).await;
    }
    if args.len() > 1 && args[1] == "cleanup-retired" {
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
    if args.len() > 1 && args[1] == "discovery-stats" {
        return show_discovery_stats(output_dir).await;
    }
    if args.len() > 1 && args[1] == "retry-missing" {
        // Continue through authentication, then re-fetch missing JSON entries.
    }
    if args.len() > 1 && args[1] == "list-missing" {
        // Continue through authentication, then list remaining IDs.
    }

    // Create output directory
    fs::create_dir_all(output_dir).context("Failed to create output directory")?;

    // Build categories from config (DRY: no hardcoded duplication)
    let categories = build_categories_from_config();

    let mut extractor = MKSAPExtractor::new(base_url, output_dir)?;

    // Configure the HTTP client with the session cookie for API authentication
    extractor = extractor.with_session_cookie(&session_cookie);

    // Authenticate using consolidated helper function (flattens nesting from 5+ to 2-3 levels)
    authenticate_extractor(&mut extractor).await?;

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

    if args.len() > 1 && args[1] == "retry-missing" {
        let recovered = extractor.retry_missing_json().await?;
        info!("Missing JSON recovery complete ({} recovered)", recovered);
        return Ok(());
    }
    if args.len() > 1 && args[1] == "list-missing" {
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
                let checkpoint_path = format!("mksap_data/.checkpoints/{}_ids.txt", category.code);
                let total_discovered = match std::fs::read_to_string(&checkpoint_path) {
                    Ok(content) => content.lines().count(),
                    Err(_) => count as usize,
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

    // Calculate total questions across all systems
    let mut total_questions = 0;

    for category in &categories {
        let checkpoint_path = format!("mksap_data/.checkpoints/{}_ids.txt", category.code);
        if let Ok(content) = std::fs::read_to_string(&checkpoint_path) {
            let discovered = content.lines().count();
            total_questions += discovered;
        }
    }

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
