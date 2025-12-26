use std::path::Path;

pub mod svgs;
pub mod videos;

pub fn filename_from_url(url: &str) -> String {
    let trimmed = url.split('?').next().unwrap_or(url);
    let name = trimmed
        .rsplit('/')
        .next()
        .filter(|part| !part.is_empty())
        .unwrap_or("media.bin");
    name.to_string()
}

pub fn relative_path(dir: &str, filename: &str) -> String {
    Path::new(dir).join(filename).to_string_lossy().to_string()
}
