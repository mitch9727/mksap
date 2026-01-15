# Rust MKSAP Extractor - Troubleshooting Guide

## Common Issues and Solutions

### Authentication Issues

#### Login Timeout (5 minute limit)

**Symptom**:
```
ERROR: Login timed out. Please run the extractor again and complete login within 5 minutes.
```

**Causes**:
- Browser window didn't open
- Network connectivity issues
- Login page not loading
- Session cookie not being detected

**Solutions**:

1. **Verify MKSAP is accessible**:
   ```bash
   curl -I https://mksap.acponline.org
   # Should return 200 OK
   ```

2. **Check credentials**:
   - Verify username and password are correct
   - Ensure ACP account is active
   - Try manual login in browser first

3. **Increase timeout**:
   - Increase the browser login timeout in the auth settings (code configuration)

4. **Manual session cookie**:
   - Log in manually at https://mksap.acponline.org
   - Extract session cookie using browser dev tools
   - Set `MKSAP_SESSION` for the extractor process

#### "Invalid Session" Errors

**Symptom**:
```
ERROR: 403 Forbidden - Session invalid or expired
```

**Causes**:
- Session cookie expired (after ~24 hours)
- Cookie lost or corrupted
- MKSAP account permissions changed

**Solutions**:

1. **Re-authenticate**:
   ```bash
   rm -f ~/.mksap_session  # Remove cached session
   ./target/release/mksap-extractor
   # Will prompt for new login
   ```

2. **Verify account access**:
   - Log in manually to MKSAP
   - Check subscription is active
   - Verify question bank access

3. **Check cookie format**:
   - Session cookie should be ~100-200 characters
   - Should start with alphanumeric
   - Should not contain spaces

### API and Network Issues

#### "Connection Refused" or "Cannot Connect"

**Symptom**:
```
ERROR: Failed to connect to mksap.acponline.org
```

**Causes**:
- MKSAP server is down
- Network connectivity issues
- Firewall blocking HTTPS

**Solutions**:

1. **Check network**:
   ```bash
   ping -c 3 mksap.acponline.org
   curl https://mksap.acponline.org -I
   ```

2. **Check firewall**:
   - Ensure port 443 (HTTPS) is accessible
   - Check corporate firewall/VPN settings
   - Try different network if available

3. **Check MKSAP status**:
   - Visit https://mksap.acponline.org in browser
   - Check ACP status page
   - Try extraction again later

#### Rate Limiting (429 Responses)

**Symptom**:
```
HTTP 429: Too Many Requests
[Backing off 60 seconds...]
```

**Causes**:
- Extraction running too fast
- Multiple extraction instances
- Server is rate limiting all requests

**Solutions**:

1. **Increase delay**:
   - Increase the request delay in the extraction settings (code configuration)

2. **Stop other extractions**:
   - Only run one extractor instance
   - Check for background processes

3. **Wait and retry**:
   - Extractor automatically backs off
   - Wait 60 seconds between requests
   - Run extraction during off-peak hours

#### Timeout Errors

**Symptom**:
```
ERROR: Request timed out after 30 seconds
```

**Causes**:
- Network is slow
- Server is responding slowly
- Large question data takes time to download

**Solutions**:

1. **Increase timeout**:
   - Increase the request timeout in the extraction settings (code configuration)

2. **Check network speed**:
   ```bash
   speedtest-cli
   # Should have >5 Mbps for reliable extraction
   ```

3. **Try different network**:
   - Move closer to WiFi router
   - Use wired connection if possible
   - Try from different location

### Data and File Issues

#### "Insufficient Disk Space"

**Symptom**:
```
ERROR: No space left on device
```

**Causes**:
- Disk full
- Output directory on full partition

**Solutions**:

1. **Check available space**:
   ```bash
   df -h
   du -sh /path/to/MKSAP
   ```

2. **Estimate space needed**:
   - Current: 754 questions = ~50MB
   - Full: 1,810 questions = ~120MB
   - Temporary: +2GB for build

3. **Free up space**:
   ```bash
   # Remove old builds
   cd /path/to/MKSAP
   cargo clean  # Frees 2GB

   # Move existing data
   mkdir ~/mksap_backup
   mv mksap_data/* ~/mksap_backup/
   ```

#### "Invalid JSON" in Extracted Files

**Symptom**:
```
ERROR: Failed to parse JSON for cvmcq24001.json
```

**Causes**:
- Incomplete download (network interrupted)
- File corruption
- API returned malformed response

**Solutions**:

1. **Delete problematic question**:
   ```bash
   rm -rf mksap_data/cv/cvmcq24001/
   ```

2. **Re-extract that question**:
   ```bash
   ./target/release/mksap-extractor
   # Will re-download missing questions
   ```

3. **Validate entire dataset**:
   ```bash
   ./target/release/mksap-extractor validate
   # Reports any corruption
   ```

4. **Resume from next system**:
   - Delete entire system directory if many corrupted files
   - Continue extraction

#### "Permission Denied" Errors

**Symptom**:
```
ERROR: Permission denied (os error 13)
```

**Causes**:
- mksap_data directory not writable
- File ownership issues
- Insufficient permissions

**Solutions**:

1. **Fix directory permissions**:
   ```bash
   cd /path/to/MKSAP
   chmod 755 mksap_data/
   chmod -R 755 mksap_data/*
   ```

2. **Check ownership**:
   ```bash
   ls -l mksap_data/
   # Should be owned by your user
   chown -R $USER mksap_data/
   ```

3. **Recreate directory**:
   ```bash
   rm -rf mksap_data/
   mkdir mksap_data
   chmod 755 mksap_data
   ```

### Compilation Issues

#### "Rustc Not Found"

**Symptom**:
```
error: toolchain 'stable' not found
```

**Solutions**:

1. **Install Rust**:
   ```bash
   curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
   source $HOME/.cargo/env
   ```

2. **Update Rust**:
   ```bash
   rustup update
   rustc --version  # Verify
   ```

#### Compilation Errors

**Symptom**:
```
error: failed to resolve: use of undeclared crate `tokio`
```

**Solutions**:

1. **Clean and rebuild**:
   ```bash
   cargo clean
   cargo build --release
   ```

2. **Update dependencies**:
   ```bash
   cargo update
   cargo build --release
   ```

3. **Check Rust version**:
   ```bash
   rustc --version  # Should be 1.70+
   rustup update    # Update if needed
   ```

### Performance Issues

#### Extraction is Very Slow

**Symptom**: Takes hours to extract a few dozen questions

**Causes**:
- Network latency
- Rate limiting too strict
- System performance issue

**Solutions**:

1. **Check network speed**:
   ```bash
   time curl https://api.github.com
   # Should complete in <1 second
   ```

2. **Reduce rate limiting** (carefully):
   - Decrease the request delay in the extraction settings (code configuration)

3. **Monitor system resources**:
   ```bash
   top
   # Check CPU and memory usage
   ```

#### High Memory Usage

**Symptom**: Extractor uses >1GB RAM

**Causes**:
- Large questions being buffered
- Memory leak (unlikely)

**Solutions**:

1. **This is unlikely** - design is async and streaming

2. **Monitor memory**:
   ```bash
   /usr/bin/time -v ./target/release/mksap-extractor
   ```

3. **Report if persistent**:
   - Check GitHub issues
   - File bug report with details

## Debugging Tips

### Enable Verbose Logging

The extractor uses `tracing`. To see more details, enable debug logging in the
logging configuration (code change) or run with a debug-enabled build if
available.

Then rebuild:
```bash
cargo build --release
```

### Check Extraction Progress

While running:

```bash
# In another terminal
watch -n 1 'ls mksap_data/cv | wc -l'
# Shows Cardiovascular questions count, updates every second
```

### Manual API Testing

Test the API directly:

```bash
# With session cookie
curl -H "Cookie: _mksap19_session=YOUR_COOKIE" \
  https://mksap.acponline.org/api/questions/cvmcq24001.json | jq .
```

### Examine Extracted Data

Check what was actually extracted:

```bash
# View question JSON
cat mksap_data/cv/cvmcq24001/cvmcq24001.json | jq .

# View metadata
cat mksap_data/cv/cvmcq24001/cvmcq24001.json

# Count questions by system
for dir in mksap_data/*/; do
  echo "$(basename $dir): $(ls $dir | wc -l)";
done
```

## When to Seek Help

### Create Issue Report

If problem persists, report with:

1. **Exact error message**:
   ```bash
   ./target/release/mksap-extractor 2>&1 | head -50
   ```

2. **System information**:
   ```bash
   rustc --version
   cargo --version
   uname -a
   ```

3. **Extraction context**:
   - Which system was being extracted
   - How many questions completed
   - Network conditions

4. **Steps to reproduce**:
   - Exact commands you ran
   - State of mksap_data/ before failure

## Phase 2: Statement Generator Troubleshooting

### Provider Setup Issues

**Claude CLI missing**:
- Install Claude Code CLI or set `CLAUDE_CLI_PATH`
- Verify: `which claude` or `echo $CLAUDE_CLI_PATH`

**Gemini CLI missing**:
- Install `google-generativeai` or set `GEMINI_CLI_PATH`
- Verify: `python -c "import google.generativeai"`

**OpenAI CLI missing**:
- Install `openai` or set `OPENAI_CLI_PATH`
- Verify: `openai --version`

**Anthropic API key missing**:
- Set `ANTHROPIC_API_KEY` in project `.env`
- Verify: `echo $ANTHROPIC_API_KEY`

### Processing Issues

**Reset checkpoint**:
```bash
./scripts/python -m src.interface.cli reset
```

**Skip reprocessing questions**:
```bash
./scripts/python -m src.interface.cli process --skip-existing --system cv
```

**Remove logs**:
```bash
./scripts/python -m src.interface.cli clean-logs
./scripts/python -m src.interface.cli clean-logs --keep-days 3
```

### Data Quality Issues

**Hallucinated facts**:
- Lower temperature: `--temperature 0.1`
- Review prompts in source code
- Compare extracted statements to critique

**Missing facts**:
- Verify they appear in critique or key_points
- Check statement generator logs for warnings
- Inspect raw LLM output (enable DEBUG logging)

**Invalid JSON response**:
- Inspect statement generator logs
- Check for malformed JSON in prompts
- Try different provider or temperature

## Next Steps

1. Review setup and usage if first time
2. Check validation for data integrity
3. See architecture for technical details
4. For continued help, file issue with details

---

**Last Updated**: January 5, 2026
