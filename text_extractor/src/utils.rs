use regex::Regex;

pub struct TextParser;

impl TextParser {
    pub fn new() -> Self {
        Self
    }

    pub fn extract_objective(&self, text: &str) -> String {
        let re = Regex::new(r"Educational Objective:\\s*(.+?)(?:\\n|Cardiovascular|Care type)")
            .unwrap();
        re.captures(text)
            .and_then(|c| c.get(1))
            .map(|m| m.as_str().trim().to_string())
            .unwrap_or_default()
    }

    pub fn extract_question_id(&self, text: &str) -> String {
        let re = Regex::new(r"Question ID\\s+([a-z0-9]+)").unwrap();
        re.captures(text)
            .and_then(|c| c.get(1))
            .map(|m| m.as_str().to_string())
            .unwrap_or_else(|| "unknown".to_string())
    }

    pub fn extract_care_types(&self, text: &str) -> Vec<String> {
        let re = Regex::new(r"Care type:\\s*([^\\n]+)").unwrap();
        re.captures_iter(text)
            .map(|c| c[1].trim().to_string())
            .collect()
    }

    pub fn extract_patient_types(&self, text: &str) -> Vec<String> {
        let re = Regex::new(r"Patient:\\s*([^\\n]+)").unwrap();
        re.captures_iter(text)
            .map(|c| c[1].trim().to_string())
            .collect()
    }

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
    fn default() -> Self {
        Self::new()
    }
}