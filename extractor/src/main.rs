use anyhow::Result;
use std::env;

use mksap_extractor::run;

#[tokio::main]
async fn main() -> Result<()> {
    let args: Vec<String> = env::args().collect();
    run(args).await
}
