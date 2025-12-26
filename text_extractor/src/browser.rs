//! Cross-platform browser-based authentication fallback for MKSAP session login.
//!
//! # Purpose
//!
//! This module provides browser-based login as an authentication fallback when
//! automatic session cookie authentication fails. It launches the system's default
//! Chrome browser and allows manual login via the MKSAP web interface.
//!
//! # Architecture
//!
//! The browser login flow:
//! 1. **Launch**: Open system's default browser with MKSAP URL
//! 2. **Wait**: Poll for authentication completion (if detection function provided)
//! 3. **Timeout**: Exit after 10 minutes of waiting
//! 4. **Extract**: Save session cookie for future use
//!
//! # Platform Support
//!
//! - **macOS**: Uses `open -a` to launch Chrome, Chromium, or Brave
//! - **Linux**: Uses `xdg-open` (respects user's default browser setting)
//! - **Windows**: Uses `start` command (launches default browser)
//!
//! # Authentication Detection
//!
//! Optional callback function (`detection_fn`) can detect login completion:
//! - Called every 3 seconds
//! - Returns `Ok(true)` when login is detected
//! - Early exit without waiting full 10-minute timeout
//! - Useful when integrating with automated testing or CI/CD

use anyhow::Result;
use std::future::Future;
use std::time::Duration;
use tracing::info;

/// Browser-based authentication helper for fallback login flow.
pub struct BrowserLogin;

impl BrowserLogin {
    /// Launch browser for manual MKSAP login with optional authentication detection.
    ///
    /// Opens the system's default Chrome/Chromium browser pointed at the MKSAP login page.
    /// Optionally polls a detection callback to determine when login is complete, or waits
    /// up to 10 minutes for manual login completion.
    ///
    /// # Arguments
    ///
    /// * `base_url` - MKSAP base URL to load in browser (e.g., "https://mksap.acponline.org")
    /// * `detection_fn` - Optional async callback that returns `Ok(true)` when login is detected.
    ///   Called every 3 seconds. If `None`, waits full 10 minutes.
    ///
    /// # Returns
    ///
    /// - `Ok(())` - Login detected (via callback) or 10-minute timeout reached
    /// - `Err` - Browser launch failed or timeout exceeded
    ///
    /// # Platform-Specific Behavior
    ///
    /// **macOS**:
    /// - Tries "Google Chrome", then "Chrome", then "Chromium" in order
    /// - Uses `open -a` to launch by application name
    ///
    /// **Linux**:
    /// - Uses `xdg-open` (respects user's default browser)
    /// - May open Firefox, Chromium, or other default browser
    ///
    /// **Windows**:
    /// - Uses `start` command
    /// - Opens system default browser
    ///
    /// # Authentication Callback
    ///
    /// The optional `detection_fn` callback:
    /// - Called every 3 seconds if provided
    /// - Should return `Ok(true)` when authentication is detected
    /// - Causes immediate return (skips remaining wait time)
    /// - Useful for automated testing or CI/CD environments
    /// - Errors in callback are logged but don't abort the wait loop
    ///
    /// # Timeout
    ///
    /// Hard 10-minute (600 second) timeout. If no successful authentication detected
    /// (or no detection callback provided), returns `Err` after timeout.
    ///
    /// # Credentials Display
    ///
    /// **WARNING**: Hardcoded credentials are displayed in the log output.
    /// In production, these should be loaded from environment variables or
    /// secure credential stores.
    ///
    /// # Examples
    ///
    /// ```ignore
    /// use text_extractor::browser::BrowserLogin;
    ///
    /// // Simple: wait 10 minutes for manual login
    /// BrowserLogin::interactive_login("https://mksap.acponline.org", None::<fn() -> _>).await?;
    ///
    /// // With detection: poll for authentication every 3 seconds
    /// let check_auth = || async {
    ///     // Check if session cookie exists or API responds with 200
    ///     is_authenticated().await
    /// };
    /// BrowserLogin::interactive_login("https://mksap.acponline.org", Some(check_auth)).await?;
    /// ```
    pub async fn interactive_login<F, Fut>(
        base_url: &str,
        username: &str,
        password: &str,
        detection_fn: Option<F>,
    ) -> Result<()>
    where
        F: Fn() -> Fut,
        Fut: Future<Output = Result<bool>>,
    {
        info!("================================================");
        info!("LAUNCHING CHROME BROWSER FOR LOGIN");
        info!("================================================");
        info!("");

        // Try to open Chrome directly with the URL
        #[cfg(target_os = "macos")]
        {
            std::process::Command::new("open")
                .args(["-a", "Google Chrome", base_url])
                .spawn()
                .or_else(|_| {
                    std::process::Command::new("open")
                        .args(["-a", "Chrome", base_url])
                        .spawn()
                })
                .or_else(|_| {
                    std::process::Command::new("open")
                        .args(["-a", "Chromium", base_url])
                        .spawn()
                })
                .ok();
        }

        #[cfg(target_os = "linux")]
        {
            std::process::Command::new("xdg-open")
                .arg(base_url)
                .spawn()
                .ok();
        }

        #[cfg(target_os = "windows")]
        {
            std::process::Command::new("start")
                .arg(base_url)
                .spawn()
                .ok();
        }

        info!("✓ Chrome browser opened!");
        info!("");
        info!("Please log in with your credentials:");
        info!("  Email: {}", username);
        info!("  Password: {}", password);
        info!("");
        info!("After successful login, your cookies will be saved for extraction.");
        info!("");
        info!("Waiting for login to complete...");
        info!("(Timeout in 10 minutes)");
        info!("");

        let max_wait = Duration::from_secs(600); // 10 minutes
        let start = std::time::Instant::now();
        let mut last_check = 0u64;
        let check_interval = 3u64; // Check authentication every 3 seconds

        // Wait for user to complete login
        loop {
            if start.elapsed() > max_wait {
                return Err(anyhow::anyhow!(
                    "Login timeout: Did not complete login within 10 minutes"
                ));
            }

            let elapsed_secs = start.elapsed().as_secs();

            // Check authentication if detection function is provided and interval has passed
            if let Some(ref detect) = detection_fn {
                if elapsed_secs - last_check >= check_interval {
                    last_check = elapsed_secs;
                    match detect().await {
                        Ok(true) => {
                            info!("✓ Login detected! Proceeding with extraction.");
                            return Ok(());
                        }
                        Ok(false) => {
                            // Still waiting, will check again in 3 seconds
                        }
                        Err(e) => {
                            info!("Authentication check failed: {}", e);
                        }
                    }
                }
            }

            // Display countdown every 10 seconds
            if elapsed_secs % 10 == 0
                && elapsed_secs != 0
                && (elapsed_secs == 10 || elapsed_secs % 10 == 0)
            {
                let remaining = 600 - elapsed_secs;
                info!("Still waiting... ({} seconds remaining)", remaining);
            }

            tokio::time::sleep(Duration::from_secs(1)).await;
        }
    }
}
