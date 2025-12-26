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
        let url = format!(
            "{}/app/question-bank/content-areas/cv/answered-questions",
            self.base_url
        );

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
        use crate::browser::BrowserLogin;
        info!("Falling back to interactive browser login...");

        // Create a detection closure that checks authentication
        let base_url = self.base_url.clone();
        let client = self.client.clone();

        let detection_fn = || async {
            let url = format!(
                "{}/app/question-bank/content-areas/cv/answered-questions",
                base_url
            );
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
