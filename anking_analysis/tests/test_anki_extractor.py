#!/usr/bin/env python3
"""
Test script for AnkiExtractor

Tests the AnkiExtractor implementation with the real Anki database.
"""

import json
import logging
from pathlib import Path
from anking_analysis.tools.anki_extractor import AnkiExtractor

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Run tests on AnkiExtractor."""
    db_path = Path.home() / "Library/Application Support/Anki2/User 1/collection.anki2"

    print("\n" + "="*70)
    print("AnkiExtractor Test Suite")
    print("="*70)

    try:
        # Initialize extractor
        print("\n[INIT] Connecting to Anki database...")
        extractor = AnkiExtractor(db_path)
        print("✓ Successfully connected to Anki database")

        # Test 1: List decks
        print("\n[TEST 1] Listing AnKing decks...")
        decks = extractor.list_decks()
        print(f"✓ Found {len(decks)} AnKing decks")

        if len(decks) > 0:
            print("\nFirst 5 decks:")
            for i, deck in enumerate(decks[:5], 1):
                print(f"  {i}. {deck['name']}")
                print(f"     Cards: {deck['card_count']}, ID: {deck['id']}")
        else:
            print("⚠ Warning: No AnKing decks found!")
            return 1

        # Test 2: Extract all samples
        print("\n[TEST 2] Extracting cards from all decks (25 per deck)...")
        cards = extractor.extract_all_samples(n_per_deck=25)
        print(f"✓ Extracted {len(cards)} cards total from {len(decks)} decks")

        if len(cards) == 0:
            print("⚠ Warning: No cards extracted!")
            return 1

        # Test 3: Examine sample card
        print("\n[TEST 3] Examining sample card...")
        sample_card = cards[0]
        print(f"  Deck: {sample_card.deck_name}")
        print(f"  Deck Path: {sample_card.deck_path}")
        print(f"  Note ID: {sample_card.note_id}")
        print(f"  Front text: {sample_card.text_plain[:100]}{'...' if len(sample_card.text_plain) > 100 else ''}")
        print(f"  Back text: {sample_card.extra_plain[:100] if sample_card.extra_plain else '(empty)'}{'...' if len(sample_card.extra_plain or '') > 100 else ''}")
        print(f"  Cloze deletions: {sample_card.cloze_count}")
        if sample_card.cloze_deletions:
            print(f"    Examples: {sample_card.cloze_deletions[:3]}")
        print(f"  Tags: {sample_card.tags if sample_card.tags else '(none)'}")
        print(f"  HTML features: {sample_card.html_features}")

        # Test 4: Data quality checks
        print("\n[TEST 4] Data quality analysis...")
        cards_with_cloze = sum(1 for c in cards if c.cloze_count > 0)
        cards_with_extra = sum(1 for c in cards if c.extra and c.extra.strip())
        cards_with_formatting = sum(1 for c in cards if any(c.html_features.values()))
        cards_with_tags = sum(1 for c in cards if c.tags)

        print(f"  Total cards: {len(cards)}")
        print(f"  Cards with cloze deletions: {cards_with_cloze}/{len(cards)} ({100*cards_with_cloze/len(cards):.1f}%)")
        print(f"  Cards with Extra field: {cards_with_extra}/{len(cards)} ({100*cards_with_extra/len(cards):.1f}%)")
        print(f"  Cards with HTML formatting: {cards_with_formatting}/{len(cards)} ({100*cards_with_formatting/len(cards):.1f}%)")
        print(f"  Cards with tags: {cards_with_tags}/{len(cards)} ({100*cards_with_tags/len(cards):.1f}%)")

        # Test 5: Distribution by deck
        print("\n[TEST 5] Cards by deck...")
        deck_counts = {}
        for card in cards:
            deck_counts[card.deck_name] = deck_counts.get(card.deck_name, 0) + 1

        for deck_name in sorted(deck_counts.keys()):
            print(f"  {deck_name}: {deck_counts[deck_name]} cards")

        # Test 6: Save to JSON
        print("\n[TEST 6] Saving to JSON...")
        data_dir = Path("/Users/Mitchell/coding/projects/MKSAP/anking_analysis/data/raw")
        data_dir.mkdir(parents=True, exist_ok=True)

        output_file = data_dir / "anking_cards_sample.json"

        # Prepare data for JSON
        cards_data = [c.model_dump() for c in cards]

        with open(output_file, 'w') as f:
            json.dump(cards_data, f, indent=2)

        file_size_kb = output_file.stat().st_size / 1024
        print(f"✓ Saved {len(cards)} cards to {output_file}")
        print(f"  File size: {file_size_kb:.1f} KB")

        # Test 7: Cloze statistics
        print("\n[TEST 7] Cloze deletion statistics...")
        total_clozes = sum(c.cloze_count for c in cards)
        max_clozes = max((c.cloze_count for c in cards), default=0)
        avg_clozes = total_clozes / len(cards) if cards else 0

        print(f"  Total cloze deletions: {total_clozes}")
        print(f"  Average per card: {avg_clozes:.2f}")
        print(f"  Maximum in single card: {max_clozes}")

        # Test 8: Formatting statistics
        print("\n[TEST 8] Formatting statistics...")
        bold_count = sum(1 for c in cards if c.html_features.get('uses_bold', False))
        italic_count = sum(1 for c in cards if c.html_features.get('uses_italic', False))
        lists_count = sum(1 for c in cards if c.html_features.get('uses_lists', False))
        tables_count = sum(1 for c in cards if c.html_features.get('uses_tables', False))
        images_count = sum(1 for c in cards if c.html_features.get('uses_images', False))

        print(f"  Cards with bold: {bold_count} ({100*bold_count/len(cards):.1f}%)")
        print(f"  Cards with italic: {italic_count} ({100*italic_count/len(cards):.1f}%)")
        print(f"  Cards with lists: {lists_count} ({100*lists_count/len(cards):.1f}%)")
        print(f"  Cards with tables: {tables_count} ({100*tables_count/len(cards):.1f}%)")
        print(f"  Cards with images: {images_count} ({100*images_count/len(cards):.1f}%)")

        # Close connection
        extractor.close()
        print("\n✓ Closed database connection")

        print("\n" + "="*70)
        print("✓ All tests passed!")
        print("="*70 + "\n")

        return 0

    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        print(f"\n✗ Error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
