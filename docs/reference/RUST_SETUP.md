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
cd /Users/Mitchell/coding/projects/MKSAP
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
3. **Extract session cookie** (automatically handled by extractor)

### Manual Session Configuration

If automatic authentication fails, you can manually provide session cookies:

**In `src/main.rs`**, update:

```rust
const USERNAME: &str = "your-email@example.com";
const PASSWORD: &str = "your-password";
const SESSION_COOKIE: &str = "your-session-cookie-here";
```

> ⚠️ **Security Warning**: Never commit credentials to version control. Use environment variables or external config files.

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
   ./target/release/mksap-extractor --version
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
├── src/
│   ├── main.rs          # Entry point, orchestration
│   ├── config.rs        # System definitions (12 system codes)
│   ├── extractor.rs     # Core extraction logic
│   ├── validator.rs     # Data quality validation
│   ├── models.rs        # Data structures
│   ├── media.rs         # Media file handling
│   ├── browser.rs       # Browser-based auth fallback
│   └── utils.rs         # Utility functions
├── mksap_data/          # Extracted question data
├── docs/                # Documentation
├── Cargo.toml           # Project manifest
├── Cargo.lock           # Dependency lock file
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
cargo build --release 2>&1 | grep -i error
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
Initializing configuration...
Checking authentication...
[Browser window opens for manual login if needed]
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
- See [Troubleshooting Guide](troubleshooting.md)

### "Insufficient disk space"
- Build requires ~2GB temporary space
- Output requires ~50MB per 100 questions
- Ensure at least 1GB free before starting

## Next Steps

1. Complete setup above
2. Read [Usage Guide](usage.md) to run the extractor
3. Check [Validation Guide](validation.md) for data quality
4. See [Architecture](architecture.md) for technical details
