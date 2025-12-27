pub(crate) fn question_json(base_url: &str, question_id: &str) -> String {
    format!("{}/api/questions/{}.json", base_url, question_id)
}

pub(crate) fn figure_json(base_url: &str, figure_id: &str) -> String {
    format!("{}/api/figures/{}.json", base_url, figure_id)
}

pub(crate) fn table_json(base_url: &str, table_id: &str) -> String {
    format!("{}/api/tables/{}.json", base_url, table_id)
}

pub(crate) fn content_metadata(base_url: &str) -> String {
    format!("{}/api/content_metadata.json", base_url)
}

pub(crate) fn answered_questions(base_url: &str) -> String {
    format!(
        "{}/app/question-bank/content-areas/cv/answered-questions",
        base_url
    )
}
