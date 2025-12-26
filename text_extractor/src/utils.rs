//! Text parsing and metadata extraction utilities using regex patterns.
//!
//! # Purpose
//!
//! Provides regex-based extraction of structured metadata from MKSAP question text,
//! including learning objectives, care types, patient demographics, answer options,
//! and key learning points.
//!
//! # Design Notes
//!
//! - Uses [`regex::Regex`] for pattern matching
//! - Regex patterns are compiled on each call (not cached) - acceptable for extraction phase
//! - All methods are non-fallible and return sensible defaults (empty strings/vecs) if patterns don't match
//! - Assumes specific MKSAP text formatting conventions

use regex::Regex;

/// Utility struct for extracting structured metadata from MKSAP question text.
///
/// This stateless helper is typically used during question data transformation
/// to extract specific fields from parsed question bodies.
pub struct TextParser;

impl TextParser {
    /// Create a new TextParser instance.
    ///
    /// Since TextParser is stateless, this is a trivial factory method.
    /// Prefer using `TextParser::default()` or direct instantiation.
    ///
    /// # Examples
    ///
    /// ```ignore
    /// let parser = TextParser::new();
    /// let objective = parser.extract_objective(question_text);
    /// ```
    pub fn new() -> Self {
        Self
    }

    /// Extract the educational objective from question text.
    ///
    /// Searches for the "Educational Objective:" section and captures the text
    /// until the next section heading or end of text.
    ///
    /// # Arguments
    ///
    /// * `text` - The question text (usually plain text conversion of nested JSON)
    ///
    /// # Returns
    ///
    /// The educational objective text, trimmed. Returns empty string if not found.
    ///
    /// # Examples
    ///
    /// ```ignore
    /// let text = "Educational Objective: Learn to diagnose heart disease\\nCare type: ...";
    /// assert_eq!(parser.extract_objective(text), "Learn to diagnose heart disease");
    /// ```
    pub fn extract_objective(&self, text: &str) -> String {
        let re = Regex::new(r"Educational Objective:\\s*(.+?)(?:\\n|Cardiovascular|Care type)")
            .unwrap();
        re.captures(text)
            .and_then(|c| c.get(1))
            .map(|m| m.as_str().trim().to_string())
            .unwrap_or_default()
    }

    /// Extract the unique question identifier from question text.
    ///
    /// Searches for a "Question ID" field and captures the alphanumeric ID
    /// (e.g., "cvmcq24001").
    ///
    /// # Arguments
    ///
    /// * `text` - The question text
    ///
    /// # Returns
    ///
    /// The question ID string. Returns "unknown" if not found.
    ///
    /// # Examples
    ///
    /// ```ignore
    /// let text = "Question ID cvmcq24001\\n...";
    /// assert_eq!(parser.extract_question_id(text), "cvmcq24001");
    /// ```
    pub fn extract_question_id(&self, text: &str) -> String {
        let re = Regex::new(r"Question ID\\s+([a-z0-9]+)").unwrap();
        re.captures(text)
            .and_then(|c| c.get(1))
            .map(|m| m.as_str().to_string())
            .unwrap_or_else(|| "unknown".to_string())
    }

    /// Extract care type classifications from question text.
    ///
    /// Searches for "Care type:" labels and captures the text following each one.
    /// Multiple care types can appear in a single question.
    ///
    /// # Arguments
    ///
    /// * `text` - The question text
    ///
    /// # Returns
    ///
    /// Vector of care type strings (e.g., `["Screening", "Health promotion"]`).
    /// Returns empty vector if none found.
    ///
    /// # Examples
    ///
    /// ```ignore
    /// let text = "Care type: Screening\\nCare type: Health promotion";
    /// assert_eq!(parser.extract_care_types(text), vec!["Screening", "Health promotion"]);
    /// ```
    pub fn extract_care_types(&self, text: &str) -> Vec<String> {
        let re = Regex::new(r"Care type:\\s*([^\\n]+)").unwrap();
        re.captures_iter(text)
            .map(|c| c[1].trim().to_string())
            .collect()
    }

    /// Extract patient type classifications from question text.
    ///
    /// Searches for "Patient:" labels and captures demographic information.
    /// Multiple patient types can appear in a single question.
    ///
    /// # Arguments
    ///
    /// * `text` - The question text
    ///
    /// # Returns
    ///
    /// Vector of patient type strings (e.g., `["Adult", "Male"]`).
    /// Returns empty vector if none found.
    ///
    /// # Examples
    ///
    /// ```ignore
    /// let text = "Patient: Adult female\\nPatient: 65 years old";
    /// assert_eq!(parser.extract_patient_types(text), vec!["Adult female", "65 years old"]);
    /// ```
    pub fn extract_patient_types(&self, text: &str) -> Vec<String> {
        let re = Regex::new(r"Patient:\\s*([^\\n]+)").unwrap();
        re.captures_iter(text)
            .map(|c| c[1].trim().to_string())
            .collect()
    }

    /// Extract multiple-choice answer options with peer performance percentages.
    ///
    /// Searches for "Option A", "Option B", "Option C", "Option D" and extracts:
    /// - The option letter
    /// - The first line of option text
    /// - The peer answer percentage (if available)
    ///
    /// # Arguments
    ///
    /// * `text` - The question text
    ///
    /// # Returns
    ///
    /// Vector of tuples: (letter, text, percentage). Example:
    /// ```text
    /// ("A", "Aspirin", 23),
    /// ("B", "Ibuprofen", 15),
    /// ("C", "Acetaminophen", 55),
    /// ("D", "Naproxen", 7)
    /// ```
    /// Returns empty vector if no options found.
    ///
    /// # Examples
    ///
    /// ```ignore
    /// let text = "Option A. Aspirin 23%\\nOption B. Ibuprofen 15%";
    /// assert_eq!(parser.extract_options(text)[0], ("A".to_string(), "Aspirin".to_string(), 23));
    /// ```
    pub fn extract_options(&self, text: &str) -> Vec<(String, String, u32)> {
        let mut options = Vec::new();

        for letter in &["A", "B", "C", "D"] {
            let pattern = format!(r"Option {}\\.\\s+(.+?)(?=Option [B-D]|You answered|Incorrect|Correct)", letter);
            let re = Regex::new(&pattern).unwrap();

            if let Some(cap) = re.captures(text) {
                let option_text = cap[1].trim().split("\n").next().unwrap_or("").to_string();

                let perc_pattern = format!(r"Option {}[^\n]*?(\d+)%", letter);
                let perc_re = Regex::new(&perc_pattern).unwrap();
                let percentage = perc_re
                    .captures(text)
                    .and_then(|c| c.get(1).map(|m| m.as_str().parse::<u32>().unwrap_or(0)))
                    .unwrap_or(0);

                options.push((letter.to_string(), option_text, percentage));
            }
        }

        options
    }

    /// Extract key learning points from the critique or summary section.
    ///
    /// Searches for the "Key Points" section and extracts bullet-pointed statements.
    /// Filters out very short points (< 10 characters) to avoid noise.
    ///
    /// # Arguments
    ///
    /// * `text` - The question text
    ///
    /// # Returns
    ///
    /// Vector of key point strings (e.g., `["Learn to recognize heart murmurs", "Consider patient age..."]`).
    /// Returns empty vector if no key points section found.
    ///
    /// # Examples
    ///
    /// ```ignore
    /// let text = "Key Points\n• Learn to recognize heart murmurs\n• Consider patient age";
    /// let points = parser.extract_key_points(text);
    /// assert!(points.contains(&"Learn to recognize heart murmurs".to_string()));
    /// ```
    pub fn extract_key_points(&self, text: &str) -> Vec<String> {
        let re = Regex::new(r"Key Points([\\s\\S]*?)(?=Reference|Learning Plan|$)")
            .unwrap();

        if let Some(cap) = re.captures(text) {
            let points_text = cap.get(1).map(|m| m.as_str()).unwrap_or("");
            let point_re = Regex::new(r"[•\\*\\-]\\s+(.+?)(?=[•\\*\\-]|$)").unwrap();

            point_re
                .captures_iter(points_text)
                .map(|c| c[1].trim().to_string())
                .filter(|p| p.len() > 10)
                .collect()
        } else {
            Vec::new()
        }
    }
}

impl Default for TextParser {
    /// Create a default TextParser instance via `Default` trait.
    ///
    /// Equivalent to `TextParser::new()`. Useful for builder patterns or
    /// scenarios where you need a `Default` implementation.
    fn default() -> Self {
        Self::new()
    }
}