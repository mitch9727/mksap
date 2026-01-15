"""Debug script to test table extraction with different providers"""

import sys
import json
import logging
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT_DIR))

from src.infrastructure.llm.providers.claude_code import ClaudeCodeProvider
from src.infrastructure.llm.providers.codex import CodexProvider

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Simple test table
TABLE_CAPTION = "Characteristics of Biologic Agents Indicated to Treat Severe Asthma"
TABLE_CONTENT = """
| Medication | Mechanism | Target | Adverse Effects |
|------------|-----------|--------|-----------------|
| Omalizumab | Anti-IgE monoclonal antibody | IgE | Anaphylaxis, increased risk of malignancy |
| Mepolizumab | Anti-IL-5 monoclonal antibody | IL-5 | Infections, headache |
| Reslizumab | Anti-IL-5 monoclonal antibody | IL-5 | Anaphylaxis, headache, helminth infections |
"""

# Load prompt template
PROMPT_TEMPLATE = (ROOT_DIR / "prompts" / "table_extraction.md").read_text(encoding="utf-8")

def test_provider(provider, provider_name):
    """Test table extraction with a provider"""
    logger.info(f"\n{'='*60}")
    logger.info(f"Testing {provider_name}")
    logger.info(f"{'='*60}\n")

    # Format prompt
    prompt = PROMPT_TEMPLATE.format(
        table_caption=TABLE_CAPTION,
        table_content=TABLE_CONTENT
    )

    logger.info(f"Prompt length: {len(prompt)} chars")

    # Call provider
    try:
        response = provider.generate(prompt)
        logger.info(f"\n{'='*60}")
        logger.info(f"RAW RESPONSE ({len(response)} chars):")
        logger.info(f"{'='*60}")
        logger.info(response)
        logger.info(f"{'='*60}\n")

        # Try to parse JSON
        try:
            data = json.loads(response)
            logger.info(f"✓ Valid JSON: {len(data.get('statements', []))} statements")
            for i, stmt in enumerate(data.get('statements', []), 1):
                logger.info(f"  {i}. {stmt['statement'][:80]}...")
        except json.JSONDecodeError as e:
            logger.error(f"✗ JSON parsing failed: {e}")
            logger.error(f"First 500 chars: {response[:500]}")

            # Try to find JSON in response
            if "```json" in response:
                logger.info("Found markdown JSON block, attempting extraction...")
                start = response.find("```json") + 7
                end = response.find("```", start)
                json_text = response[start:end].strip()
                try:
                    data = json.loads(json_text)
                    logger.info(f"✓ Extracted JSON from markdown: {len(data.get('statements', []))} statements")
                except json.JSONDecodeError as e2:
                    logger.error(f"✗ Still failed: {e2}")
            elif "```" in response:
                logger.info("Found markdown code block, attempting extraction...")
                start = response.find("```") + 3
                end = response.find("```", start)
                json_text = response[start:end].strip()
                try:
                    data = json.loads(json_text)
                    logger.info(f"✓ Extracted JSON from code block: {len(data.get('statements', []))} statements")
                except json.JSONDecodeError as e2:
                    logger.error(f"✗ Still failed: {e2}")

    except Exception as e:
        logger.error(f"Provider call failed: {e}")

if __name__ == "__main__":
    print("\n" + "="*80)
    print("TABLE EXTRACTION DEBUG TEST")
    print("="*80 + "\n")

    # Test Claude Code
    try:
        claude_provider = ClaudeCodeProvider(model="sonnet", temperature=0.2)
        test_provider(claude_provider, "Claude Code CLI")
    except Exception as e:
        logger.error(f"Claude Code provider initialization failed: {e}")

    # Test Codex (if available)
    try:
        codex_provider = CodexProvider(model="gpt-4", temperature=0.2)
        test_provider(codex_provider, "Codex CLI")
    except Exception as e:
        logger.error(f"Codex provider initialization failed: {e}")
