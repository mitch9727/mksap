use anyhow::{Context, Result};
use std::collections::HashSet;
use std::fs;
use std::path::Path;

pub fn checkpoint_system_id(path: &Path) -> Option<String> {
    let filename = path.file_name().and_then(|n| n.to_str())?;
    let system_id = filename.strip_suffix("_ids.txt")?;
    if system_id.is_empty() {
        None
    } else {
        Some(system_id.to_string())
    }
}

pub fn read_checkpoint_lines(path: &Path) -> Result<Vec<String>> {
    let content = fs::read_to_string(path).context("Failed to read checkpoint file")?;
    Ok(content
        .lines()
        .map(str::trim)
        .filter(|line| !line.is_empty())
        .map(|line| line.to_string())
        .collect())
}

pub fn read_checkpoint_ids(path: &Path) -> Result<Vec<String>> {
    let mut ids = read_checkpoint_lines(path)?;
    ids.sort();
    ids.dedup();
    Ok(ids)
}

pub fn read_all_checkpoint_ids(checkpoint_dir: &Path) -> Result<HashSet<String>> {
    let mut all_ids = HashSet::new();

    for entry in fs::read_dir(checkpoint_dir).context("Failed to read checkpoint directory")? {
        let entry = entry?;
        let path = entry.path();

        if !path.is_file() || !path.to_string_lossy().ends_with("_ids.txt") {
            continue;
        }

        for id in read_checkpoint_lines(&path)? {
            all_ids.insert(id);
        }
    }

    Ok(all_ids)
}
