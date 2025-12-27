mod app;
mod auth_flow;
mod browser;
mod categories;
mod commands;
mod config;
mod diagnostics;
mod extractor;
mod models;
mod reporting;
mod standardize;
mod validator;

pub use app::{
    handle_standalone_command, init_tracing, load_env, maybe_inspect_api, parse_run_options,
    parse_standardize_options, run, run_extraction, RunOptions, StandardizeOptions, BASE_URL,
    DOTENV_PATH, OUTPUT_DIR,
};
pub use auth_flow::authenticate_extractor;
pub use categories::{build_categories_from_config, Category};
pub use commands::Command;
pub use diagnostics::inspect_api;
pub use extractor::MKSAPExtractor;
pub use reporting::{
    count_discovered_ids, show_discovery_stats, total_discovered_ids, validate_extraction,
};
pub use standardize::run_standardization;
