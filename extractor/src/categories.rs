use crate::config;

#[derive(Debug, Clone)]
pub struct Category {
    pub code: String,
    pub name: String,
    pub question_prefix: String,
}

pub fn build_categories_from_config() -> Vec<Category> {
    config::init_organ_systems()
        .into_iter()
        .map(|sys| {
            let id = sys.id;
            Category {
                code: id.clone(),
                name: sys.name,
                question_prefix: id,
            }
        })
        .collect()
}
