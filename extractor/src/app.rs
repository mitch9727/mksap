use anyhow::Result;
use std::env;
use tracing::{debug, error, info};

use crate::handlers::handle_command;
use crate::{Command, MKSAPExtractor};

pub const DOTENV_PATH: &str = "../.env";
pub const BASE_URL: &str = "https://mksap.acponline.org";
pub const OUTPUT_DIR: &str = "../mksap_data";

pub async fn run(args: Vec<String>) -> Result<()> {
    load_env();
    init_tracing();

    info!("MKSAP Question Bank Extractor (Rust)");
    info!("=====================================");

    let command = Command::parse(&args);
    handle_command(command, &args).await
}

pub fn load_env() {
    dotenv::from_path(DOTENV_PATH).ok();
}

pub fn init_tracing() {
    tracing_subscriber::fmt()
        .with_max_level(tracing::Level::INFO)
        .init();
}

pub async fn maybe_inspect_api(extractor: &MKSAPExtractor) -> Result<()> {
    if env::var_os("MKSAP_INSPECT_API").is_some() {
        debug!("=== PHASE 1: INSPECTING API RESPONSE ===");
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

pub async fn inspect_api(extractor: &MKSAPExtractor) -> Result<()> {
    let url = crate::endpoints::question_json(BASE_URL, "cvmcq25001");

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
