# Rust MKSAP Extractor - Setup Guide

## Prerequisites

### System Requirements
- **OS**: macOS, Linux, or Windows
- **Rust**: 1.70 or newer
- **Disk Space**: ~1GB for dependencies + extracted data

### Rust Installation

If you don't have Rust installed:

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source $HOME/.cargo/env
rustc --version  # Verify installation
```

## Project Setup

### Navigate to Project

```bash
cd /Users/Mitchell/coding/projects/MKSAP/extractor
```

### Build the Project

#### Debug Build (faster, larger binary)
```bash
cargo build
./target/debug/mksap-extractor
```

#### Release Build (optimized, smaller binary)
```bash
cargo build --release
./target/release/mksap-extractor
```

The release build produces a ~15MB binary suitable for production use.

## Configuration

### MKSAP API Authentication

The extractor requires valid MKSAP session credentials:

1. **Visit MKSAP**: https://mksap.acponline.org
2. **Log in** with your ACP credentials
3. **Extract session cookie** and set `MKSAP_SESSION`, or provide `MKSAP_USERNAME`/`MKSAP_PASSWORD`

### Manual Session Configuration

If authentication fails, provide credentials via environment variables:

```bash
MKSAP_SESSION=... ./target/release/mksap-extractor
```

```bash
MKSAP_USERNAME=... MKSAP_PASSWORD=... ./target/release/mksap-extractor
```

> ⚠️ **Security Warning**: Never commit credentials to version control. Prefer environment variables or a local `.env` file.

## Building from Source

### Step-by-Step

1. **Verify Rust toolchain**:
   ```bash
   rustup update
   rustc --version
   cargo --version
   ```

2. **Check dependencies**:
   ```bash
   cargo check
   ```

3. **Build release binary**:
   ```bash
   cargo build --release
   ```

4. **Verify binary**:
   ```bash
   ls -lh target/release/mksap-extractor
   ./target/release/mksap-extractor
   ```

### Dependencies

Key dependencies (from `Cargo.toml`):

- `tokio` - Async runtime with full features
- `reqwest` - HTTP client with JSON support
- `scraper` - HTML parsing
- `serde_json` - JSON serialization
- `tracing` - Structured logging
- `chrono` - Date/time handling
- `anyhow` - Error handling

All dependencies are automatically downloaded during build.

## Directory Structure

```
/Users/Mitchell/coding/projects/MKSAP/
├── extractor/      # Unified extractor crate
│   ├── Cargo.toml
│   └── src/
│       ├── main.rs          # Entry point and CLI dispatch
│       ├── app.rs           # Command routing and orchestration
│       ├── commands.rs      # Command parsing
│       ├── config.rs        # System definitions (16 system codes)
│       ├── categories.rs    # Category build helpers
│       ├── extractor.rs     # Core extractor type
│       ├── workflow.rs      # Discovery + extraction pipeline
│       ├── discovery.rs     # ID discovery + checkpoints
│       ├── io.rs            # File IO + checkpoints
│       ├── retry.rs         # Retry helpers
│       ├── cleanup.rs       # Cleanup helpers
│       ├── reporting.rs     # Validation/discovery reports
│       ├── validator.rs     # Data validation
│       ├── auth.rs          # API login helpers
│       ├── auth_flow.rs     # Authentication flow
│       ├── browser.rs       # Browser-based auth fallback
│       ├── diagnostics.rs   # API inspection helper
│       ├── media/           # Media discovery/download modules
│       └── models.rs        # Data structures
├── mksap_data/          # Extracted question data
├── mksap_data_failed/   # Failed extraction artifacts
├── docs/                # Documentation
├── README.md            # Project readme
└── .gitignore           # Git ignore patterns
```

## Verification

### Check Installation

```bash
# Verify Rust
rustc --version

# Verify cargo
cargo --version

# Test build
cargo check

# Verify compilation
cargo build --release 2>&1 | rg -i "error"
```

### Create Test Data Directory

```bash
cd /Users/Mitchell/coding/projects/MKSAP
mkdir -p mksap_data
chmod 755 mksap_data
```

### First Run

The first run will require manual login or valid session credentials:

```bash
./target/release/mksap-extractor
```

Expected output:
```
🚀 MKSAP Extractor Starting...
Step 0: Checking if already authenticated...
Step 1: Attempting automatic login with provided credentials...
Attempting browser-based login as fallback...
[Browser window opens if needed]
Beginning extraction...
```

## Troubleshooting Setup

### "cargo not found"
- Install Rust using: `curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh`
- Add cargo to PATH: `source $HOME/.cargo/env`

### "Compilation errors"
- Update Rust: `rustup update`
- Clean build: `cargo clean && cargo build --release`
- Check dependencies: `cargo check`

### "Authentication fails"
- Verify MKSAP credentials are valid
- Check session cookie hasn't expired
- Try manual login in browser first
- See [Troubleshooting Guide](TROUBLESHOOTING.md)

### "Insufficient disk space"
- Build requires ~2GB temporary space
- Output requires ~50MB per 100 questions
- Ensure at least 1GB free before starting

## Next Steps

1. Complete setup above
2. Read [Usage Guide](RUST_USAGE.md) to run the extractor
3. Check [Validation Guide](VALIDATION.md) for data quality
4. See [Architecture](RUST_ARCHITECTURE.md) for technical details
