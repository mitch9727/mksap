use serde::{Deserialize, Serialize};
use std::collections::HashMap;

use super::asset_types::QuestionMedia;

// ============================================================================
// Statistics Tracking
// ============================================================================

#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct DiscoveryStatistics {
    pub total_questions_scanned: usize,
    pub total_questions_with_media: usize,
    pub total_questions_without_media: usize,
    pub percentage_with_media: f64,

    // Per media type
    pub questions_with_figures: usize,
    pub questions_with_tables: usize,
    pub questions_with_videos: usize,
    pub questions_with_svgs: usize,

    // Total counts
    pub total_figure_references: usize,
    pub total_table_references: usize,
    pub total_video_references: usize,
    pub total_svg_references: usize,

    // Figure breakdown
    pub svg_figures: usize,
    pub jpg_figures: usize,
    pub png_figures: usize,

    // Combinations
    pub questions_with_multiple_types: usize,
    pub questions_with_all_four_types: usize,

    // By specialty
    pub by_subspecialty: HashMap<String, usize>,

    // By product type (kept for backward compatibility, currently unused)
    pub by_product_type: HashMap<String, usize>,

    // Video question tracking by subspecialty
    #[serde(skip_serializing, default)]
    pub video_questions_by_subspecialty: HashMap<String, Vec<String>>,
    #[serde(skip_serializing_if = "Vec::is_empty", default)]
    pub video_question_ids: Vec<String>,

    // Error tracking
    pub failed_requests: usize,
    pub skipped_questions: usize,
}

impl DiscoveryStatistics {
    /// Update statistics with a newly discovered question
    pub fn update_with_question(&mut self, question_id: &str, question: &QuestionMedia) {
        let has_figures = !question.figures.is_empty();
        let has_tables = !question.tables.is_empty();
        let has_videos = !question.videos.is_empty();
        let has_svgs = !question.svgs.is_empty();

        if has_figures {
            self.questions_with_figures += 1;
            self.total_figure_references += question.figures.len();

            for fig in &question.figures {
                match fig.extension.as_str() {
                    "svg" => self.svg_figures += 1,
                    "jpg" | "jpeg" => self.jpg_figures += 1,
                    "png" => self.png_figures += 1,
                    _ => {}
                }
            }
        }

        if has_tables {
            self.questions_with_tables += 1;
            self.total_table_references += question.tables.len();
        }

        if has_videos {
            self.questions_with_videos += 1;
            self.total_video_references += question.videos.len();
            self.video_question_ids.push(question_id.to_string());

            // Track video questions by subspecialty
            if let Some(subspecialty) = &question.subspecialty {
                self.video_questions_by_subspecialty
                    .entry(subspecialty.clone())
                    .or_default()
                    .push(question_id.to_string());
            }
        }

        if has_svgs {
            self.questions_with_svgs += 1;
            self.total_svg_references += question.svgs.len();
        }

        let media_type_count = question.media_type_count();
        if media_type_count > 1 {
            self.questions_with_multiple_types += 1;
        }
        if media_type_count == 4 {
            self.questions_with_all_four_types += 1;
        }

        // Track by subspecialty
        if let Some(subspecialty) = &question.subspecialty {
            *self
                .by_subspecialty
                .entry(subspecialty.clone())
                .or_insert(0) += 1;
        }
    }

    /// Finalize statistics after all questions processed
    pub fn finalize(&mut self, total_scanned: usize, total_with_media: usize) {
        self.total_questions_scanned = total_scanned;
        self.total_questions_with_media = total_with_media;
        self.total_questions_without_media =
            total_scanned - total_with_media - self.skipped_questions;
        self.percentage_with_media = if total_scanned > 0 {
            (total_with_media as f64 / total_scanned as f64) * 100.0
        } else {
            0.0
        };
        if !self.video_question_ids.is_empty() {
            self.video_question_ids.sort();
            self.video_question_ids.dedup();
        }
    }

    /// Generate human-readable report
    pub fn generate_report(&self, timestamp: &str) -> String {
        let mut report = String::new();

        report.push_str("MKSAP Media Discovery Report\n");
        report.push_str(&format!("Generated: {}\n", timestamp));
        report.push('\n');

        report.push_str("SUMMARY\n");
        report.push_str(&format!(
            "- Total questions scanned: {}\n",
            self.total_questions_scanned
        ));
        report.push_str(&format!(
            "- Questions with media: {} ({:.1}%)\n",
            self.total_questions_with_media, self.percentage_with_media
        ));
        report.push_str(&format!(
            "- Questions without media: {}\n",
            self.total_questions_without_media
        ));
        report.push_str(&format!(
            "- Skipped (invalidated): {}\n",
            self.skipped_questions
        ));
        report.push_str(&format!("- Failed: {}\n", self.failed_requests));
        report.push('\n');

        report.push_str("MEDIA COUNTS\n");
        report.push_str(&format!(
            "- Figures: {} (across {} questions)\n",
            self.total_figure_references, self.questions_with_figures
        ));
        report.push_str(&format!(
            "- Tables: {} (across {} questions)\n",
            self.total_table_references, self.questions_with_tables
        ));
        report.push_str(&format!(
            "- Videos: {} (across {} questions)\n",
            self.total_video_references, self.questions_with_videos
        ));
        report.push_str(&format!(
            "- SVGs: {} (across {} questions)\n",
            self.total_svg_references, self.questions_with_svgs
        ));
        report.push('\n');

        report.push_str("FIGURE BREAKDOWN\n");
        report.push_str(&format!("- SVG format: {}\n", self.svg_figures));
        report.push_str(&format!("- JPG format: {}\n", self.jpg_figures));
        report.push_str(&format!("- PNG format: {}\n", self.png_figures));
        report.push('\n');

        report.push_str("MEDIA COMBINATIONS\n");
        report.push_str(&format!(
            "- Questions with multiple media types: {}\n",
            self.questions_with_multiple_types
        ));
        report.push_str(&format!(
            "- Questions with all four types: {}\n",
            self.questions_with_all_four_types
        ));
        report.push('\n');

        if !self.by_subspecialty.is_empty() {
            report.push_str("BY SUBSPECIALTY\n");
            let mut subspecialties: Vec<_> = self.by_subspecialty.iter().collect();
            subspecialties.sort_by_key(|(k, _)| *k);
            for (subspecialty, count) in subspecialties {
                report.push_str(&format!("- {}: {} questions\n", subspecialty, count));
            }
            report.push('\n');
        }

        if !self.by_product_type.is_empty() {
            report.push_str("BY PRODUCT TYPE\n");
            let mut product_types: Vec<_> = self.by_product_type.iter().collect();
            product_types.sort_by_key(|(k, _)| *k);
            for (product_type, count) in product_types {
                report.push_str(&format!("- {}: {} questions\n", product_type, count));
            }
            report.push('\n');
        }

        // Add video questions section
        if !self.video_questions_by_subspecialty.is_empty() {
            report.push_str("QUESTIONS WITH VIDEOS\n");

            // Sort by video count (descending), then alphabetically
            let mut sorted: Vec<_> = self.video_questions_by_subspecialty.iter().collect();
            sorted.sort_by(|a, b| b.1.len().cmp(&a.1.len()).then_with(|| a.0.cmp(b.0)));

            for (subspecialty, question_ids) in sorted {
                let count = question_ids.len();
                let mut ids_sorted = question_ids.clone();
                ids_sorted.sort();

                report.push_str(&format!("  {} ({}):\n", subspecialty, count));
                report.push_str(&format!("    {}\n", ids_sorted.join(", ")));
            }
            report.push('\n');
        }

        if !self.video_question_ids.is_empty() {
            report.push_str("VIDEO QUESTION IDS\n");
            report.push_str(&format!("{}\n", self.video_question_ids.join(", ")));
        }

        report
    }
}
