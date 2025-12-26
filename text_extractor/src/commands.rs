#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Command {
    Run,
    Validate,
    CleanupRetired,
    CleanupFlat,
    DiscoveryStats,
    RetryMissing,
    ListMissing,
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
            _ => Command::Run,
        }
    }

    pub fn requires_auth(self) -> bool {
        matches!(
            self,
            Command::Run | Command::RetryMissing | Command::ListMissing
        )
    }
}
