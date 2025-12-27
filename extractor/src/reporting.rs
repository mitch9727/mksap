use anyhow::{Context, Result};
use std::fs;
use std::path::Path;
use tracing::info;

use crate::categories::Category;
use crate::checkpoints::read_checkpoint_lines;
use crate::models::DiscoveryMetadataCollection;
use crate::validator::DataValidator;

pub async fn validate_extraction(output_dir: &str) -> Result<()> {
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

pub async fn show_discovery_stats(output_dir: &str) -> Result<()> {
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

pub fn count_discovered_ids(output_dir: &str, category_code: &str) -> usize {
    let checkpoint_path = format!("{}/.checkpoints/{}_ids.txt", output_dir, category_code);
    match read_checkpoint_lines(Path::new(&checkpoint_path)) {
        Ok(ids) => ids.len(),
        Err(_) => 0,
    }
}

pub fn total_discovered_ids(output_dir: &str, categories: &[Category]) -> usize {
    categories
        .iter()
        .map(|category| count_discovered_ids(output_dir, &category.code))
        .sum()
}
