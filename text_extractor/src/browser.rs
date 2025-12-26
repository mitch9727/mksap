use anyhow::Result;
use tracing::info;
use std::time::Duration;
use std::future::Future;

pub struct BrowserLogin;

impl BrowserLogin {
    /// Launch Chrome for manual login with optional authentication detection
    ///
    /// If detection_fn returns true, login is considered complete and the function exits early.
    /// Otherwise, waits up to 10 minutes for manual login completion.
    pub async fn interactive_login<F, Fut>(base_url: &str, detection_fn: Option<F>) -> Result<()>
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
                .or_else(|_| std::process::Command::new("open")
                    .args(["-a", "Chrome", base_url])
                    .spawn())
                .or_else(|_| std::process::Command::new("open")
                    .args(["-a", "Chromium", base_url])
                    .spawn())
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
        info!("  Email: mitmarques@aol.com");
        info!("  Password: gipkyz-sonki2-Wekjyv");
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
                return Err(anyhow::anyhow!("Login timeout: Did not complete login within 10 minutes"));
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
            if elapsed_secs % 10 == 0 && elapsed_secs != 0 && (elapsed_secs == 10 || elapsed_secs % 10 == 0) {
                let remaining = 600 - elapsed_secs;
                info!("Still waiting... ({} seconds remaining)", remaining);
            }

            tokio::time::sleep(Duration::from_secs(1)).await;
        }
    }
}
