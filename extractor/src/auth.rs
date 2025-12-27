use anyhow::Result;
use serde_json::json;
use tracing::{info, warn};

use super::MKSAPExtractor;

impl MKSAPExtractor {
    pub async fn login(&mut self, username: &str, password: &str) -> Result<()> {
        info!("Attempting to authenticate with MKSAP as {}...", username);

        // Try multiple possible login endpoints
        let endpoints = vec![
            format!("{}/api/auth/login", self.base_url),
            format!("{}/api/login", self.base_url),
            format!("{}/auth/login", self.base_url),
            format!("{}/login", self.base_url),
        ];

        let credentials = json!({
            "email": username,
            "password": password,
        });

        for endpoint in endpoints {
            info!("Trying authentication endpoint: {}", endpoint);

            match self.client.post(&endpoint).json(&credentials).send().await {
                Ok(response) => {
                    let status = response.status();

                    if status.is_success() {
                        self.authenticated = true;
                        info!("Successfully authenticated with MKSAP!");
                        return Ok(());
                    } else if status.as_u16() == 404 {
                        // Try next endpoint
                        continue;
                    } else {
                        let error_text = response.text().await.unwrap_or_default();
                        warn!(
                            "Authentication endpoint {} returned {}: {}",
                            endpoint, status, error_text
                        );
                    }
                }
                Err(e) => {
                    warn!("Request to {} failed: {}", endpoint, e);
                    continue;
                }
            }
        }

        warn!("Could not find a valid authentication endpoint. Proceeding without authentication.");
        // Continue anyway - some content might be accessible
        Ok(())
    }

    pub async fn is_already_authenticated(&self) -> Result<bool> {
        let url = crate::endpoints::answered_questions(&self.base_url);

        match self.client.get(&url).send().await {
            Ok(response) => {
                let is_auth = response.status() == 200;
                if is_auth {
                    info!("✓ Already authenticated (received 200 from question bank page)");
                } else {
                    info!(
                        "Not yet authenticated (received {} from question bank page)",
                        response.status()
                    );
                }
                Ok(is_auth)
            }
            Err(e) => {
                info!("Could not check authentication status: {}", e);
                Ok(false)
            }
        }
    }

    pub async fn browser_login(&mut self, username: &str, password: &str) -> Result<()> {
        use crate::login_browser::BrowserLogin;
        info!("Falling back to interactive browser login...");

        // Create a detection closure that checks authentication
        let base_url = self.base_url.clone();
        let client = self.client.clone();

        let detection_fn = || async {
            let url = crate::endpoints::answered_questions(&base_url);
            match client.get(&url).send().await {
                Ok(response) => Ok(response.status() == 200),
                Err(_) => Ok(false),
            }
        };

        BrowserLogin::interactive_login(&self.base_url, username, password, Some(detection_fn))
            .await?;
        self.authenticated = true;
        Ok(())
    }
}

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
