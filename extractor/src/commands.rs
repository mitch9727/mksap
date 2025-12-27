#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Command {
    Run,
    Validate,
    CleanupRetired,
    CleanupFlat,
    DiscoveryStats,
    RetryMissing,
    ListMissing,
    Standardize,
    MediaDiscover,
    MediaDownload,
    MediaBrowser,
    ExtractAll,
}

impl Command {
    pub fn parse(args: &[String]) -> Self {
        match args.get(1).map(|value| value.as_str()) {
            Some("validate") => Command::Validate,
            Some("cleanup-retired") => Command::CleanupRetired,
            Some("cleanup-flat") => Command::CleanupFlat,
            Some("discovery-stats") => Command::DiscoveryStats,
            Some("retry-missing") => Command::RetryMissing,
            Some("list-missing") => Command::ListMissing,
            Some("standardize") => Command::Standardize,
            Some("media-discover") => Command::MediaDiscover,
            Some("media-download") => Command::MediaDownload,
            Some("media-browser") => Command::MediaBrowser,
            Some("extract-all") => Command::ExtractAll,
            _ => Command::Run,
        }
    }

    pub fn requires_auth(self) -> bool {
        matches!(
            self,
            Command::Run
                | Command::RetryMissing
                | Command::ListMissing
                | Command::MediaDiscover
                | Command::MediaDownload
                | Command::MediaBrowser
                | Command::ExtractAll
        )
    }
}
