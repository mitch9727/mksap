use anyhow::Result;
use tracing::{info, warn};

use crate::extractor::MKSAPExtractor;

/// Perform authentication with fallback strategy.
///
/// Tries in order:
/// 1. Check if already authenticated (HTTP check)
/// 2. Automatic login with credentials
/// 3. Browser-based login (interactive)
///
/// Logs all results and warns on failures, but doesn't error out.
pub async fn authenticate_extractor(extractor: &mut MKSAPExtractor) -> Result<()> {
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
