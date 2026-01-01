# Parallel Execution Fix - Provider-Specific Checkpoints

**Enables**: Running multiple providers in parallel on same questions

## Changes Required

### 1. Modify `checkpoint.py`

```python
class CheckpointManager:
    """Manage processing checkpoints for resumability"""

    def __init__(self, checkpoint_path: Path, provider: str = "default"):  # ADD provider param
        # Use provider-specific checkpoint file
        self.checkpoint_file = checkpoint_path / f"{provider}_processed.json"
        self.checkpoint_file.parent.mkdir(parents=True, exist_ok=True)
        self._data = self._load()
```

### 2. Modify `main.py`

```python
@cli.command()
def process(...):
    # Pass provider to checkpoint
    checkpoint = CheckpointManager(
        config.paths.checkpoints,
        provider=config.llm.provider  # ADD THIS
    )
```

### 3. Test

```bash
# Terminal 1: Anthropic
python -m src.main process --provider anthropic --mode production

# Terminal 2: Claude Code (parallel!)
python -m src.main process --provider claude-code --mode production

# Each creates separate checkpoint:
# - outputs/checkpoints/anthropic_processed.json
# - outputs/checkpoints/claude-code_processed.json
```

## Result

- ✅ Safe parallel execution across providers
- ✅ Each provider tracks own progress
- ✅ Can compare outputs across providers
- ✅ Minimal code changes (2 lines)
