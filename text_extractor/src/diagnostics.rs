use anyhow::Result;

use crate::extractor::MKSAPExtractor;

pub async fn inspect_api(extractor: &MKSAPExtractor) -> Result<()> {
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
