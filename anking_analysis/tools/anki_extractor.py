"""
AnKing Flashcard Extractor

Extracts flashcards from the Anki SQLite database (collection.anki2).

Handles:
- Connecting to Anki SQLite database
- Listing all AnKing decks
- Sampling N random cards per deck
- Parsing HTML and extracting cloze deletions
- Creating AnkingCard data models

Author: Claude Code
Date: 2026-01-20
"""

import sqlite3
import json
import re
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from bs4 import BeautifulSoup

from anking_analysis.models import AnkingCard

logger = logging.getLogger(__name__)


class AnkiExtractor:
    """
    Extract flashcards from Anki database.

    Connects to the Anki SQLite database and extracts cards from AnKing decks,
    including parsing HTML, extracting cloze deletions, and detecting formatting features.
    """

    def __init__(self, db_path: Path):
        """
        Initialize AnkiExtractor with database connection.

        Args:
            db_path: Path to collection.anki2 file

        Raises:
            FileNotFoundError: If database file does not exist
            sqlite3.DatabaseError: If database is corrupt or inaccessible
        """
        self.db_path = Path(db_path)

        if not self.db_path.exists():
            raise FileNotFoundError(f"Anki database not found at {self.db_path}")

        try:
            self.conn = sqlite3.connect(str(self.db_path))
            self.conn.row_factory = sqlite3.Row

            # Verify database is readable and has required tables
            cursor = self.conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = {row[0] for row in cursor.fetchall()}

            required_tables = {'decks', 'cards', 'notes', 'col'}
            if not required_tables.issubset(tables):
                raise sqlite3.DatabaseError(
                    f"Anki database missing required tables. Found: {tables}"
                )

            logger.info(f"Connected to Anki database at {self.db_path}")
        except sqlite3.DatabaseError as e:
            raise sqlite3.DatabaseError(f"Failed to open Anki database: {e}")

    def list_decks(self) -> List[Dict]:
        """
        Get all AnKing decks with card counts.

        Returns a list of dictionaries containing deck information including
        deck ID, name, and total card count for each AnKing deck with at least 25 cards.

        Returns:
            List of dicts with keys: 'id', 'name', 'card_count'
            Ordered alphabetically by deck name

        Example:
            [
                {'id': 1234567890, 'name': 'MKSAP::Cardiovascular', 'card_count': 156},
                {'id': 1234567891, 'name': 'MKSAP::Endocrinology', 'card_count': 89},
            ]
        """
        cursor = self.conn.cursor()

        try:
            # Query all decks first (avoiding collation issues)
            cursor.execute("""
                SELECT id, name FROM decks WHERE name IS NOT NULL
            """)

            decks = []
            for row in cursor.fetchall():
                deck_id = row['id']
                deck_name = row['name']

                # Count cards in this deck
                cursor.execute("SELECT COUNT(*) as card_count FROM cards WHERE did = ?", (deck_id,))
                card_count = cursor.fetchone()['card_count']

                # Include only AnKing and MKSAP decks with >= 25 cards
                if card_count >= 25 and ('AnKing' in deck_name or 'MKSAP' in deck_name):
                    decks.append({
                        'id': deck_id,
                        'name': deck_name,
                        'card_count': card_count
                    })

            # Sort by name (Python sort instead of SQL due to custom Anki collation)
            decks.sort(key=lambda d: d['name'])

            logger.info(f"Found {len(decks)} AnKing decks with >= 25 cards")
            return decks

        except sqlite3.Error as e:
            logger.error(f"Error listing decks: {e}")
            raise

    def sample_cards(self, deck_id: int, n: int = 25) -> List[Dict]:
        """
        Random sample of N cards from a specific deck.

        Performs random sampling from the specified deck, returning up to N cards.
        If deck has fewer than N cards, returns all available cards.

        Args:
            deck_id: Anki deck ID
            n: Number of cards to sample (default: 25)

        Returns:
            List of dicts with keys: 'note_id', 'flds', 'tags'
            Limited to n cards (or fewer if deck has fewer cards)
        """
        cursor = self.conn.cursor()

        try:
            cursor.execute("""
                SELECT n.id as note_id, n.flds, n.tags
                FROM notes n
                JOIN cards c ON c.nid = n.id
                WHERE c.did = ?
                ORDER BY RANDOM()
                LIMIT ?
            """, (deck_id, n))

            cards = []
            for row in cursor.fetchall():
                cards.append({
                    'note_id': row['note_id'],
                    'flds': row['flds'],
                    'tags': row['tags']
                })

            logger.debug(f"Sampled {len(cards)} cards from deck {deck_id}")
            return cards

        except sqlite3.Error as e:
            logger.error(f"Error sampling cards from deck {deck_id}: {e}")
            raise

    def get_deck_path(self, deck_id: int) -> str:
        """
        Get the full deck path from deck ID.

        Args:
            deck_id: Anki deck ID

        Returns:
            Full deck path (e.g., 'MKSAP::Cardiovascular::HF')
        """
        cursor = self.conn.cursor()

        try:
            cursor.execute("SELECT name FROM decks WHERE id = ?", (deck_id,))
            row = cursor.fetchone()

            if row:
                return row['name']
            return ""

        except sqlite3.Error as e:
            logger.error(f"Error getting deck path for {deck_id}: {e}")
            return ""

    def extract_all_samples(self, n_per_deck: int = 25) -> List[AnkingCard]:
        """
        Extract and sample cards from ALL AnKing decks.

        Main method that orchestrates extraction:
        1. Lists all AnKing decks
        2. For each deck, samples N random cards
        3. Parses HTML and extracts cloze deletions
        4. Returns AnkingCard objects

        Args:
            n_per_deck: Number of cards to sample per deck (default: 25)

        Returns:
            List of AnkingCard objects extracted from all decks
        """
        anking_cards = []

        # Get all AnKing decks
        decks = self.list_decks()
        logger.info(f"Extracting {n_per_deck} cards from {len(decks)} decks")

        for deck_info in decks:
            deck_id = deck_info['id']
            deck_path = deck_info['name']
            deck_name = deck_path.split('::')[-1] if '::' in deck_path else deck_path

            logger.info(f"Processing deck: {deck_path}")

            # Sample cards from this deck
            sampled = self.sample_cards(deck_id, n_per_deck)
            logger.info(f"  Sampled {len(sampled)} cards from {deck_info['card_count']} total")

            # Process each sampled card
            for card_data in sampled:
                try:
                    # Parse fields (separated by \x1f)
                    fields = card_data['flds'].split('\x1f')

                    # Extract front and back fields
                    # Most AnKing cards use first field as front, second as back
                    text = fields[0] if len(fields) > 0 else ""
                    extra = fields[1] if len(fields) > 1 else ""

                    # Parse HTML
                    text_plain, html_features = self.parse_html(text)
                    extra_plain, _ = self.parse_html(extra)

                    # Extract cloze deletions
                    cloze_deletions = self.extract_cloze(text)

                    # Parse tags
                    tags = card_data['tags'].split() if card_data['tags'] else []

                    # Create AnkingCard object
                    card = AnkingCard(
                        note_id=card_data['note_id'],
                        deck_path=deck_path,
                        deck_name=deck_name,
                        text=text,
                        text_plain=text_plain,
                        extra=extra,
                        extra_plain=extra_plain,
                        cloze_deletions=cloze_deletions,
                        cloze_count=len(cloze_deletions),
                        tags=tags,
                        html_features=html_features
                    )

                    anking_cards.append(card)

                except Exception as e:
                    logger.warning(
                        f"Failed to parse card {card_data['note_id']} from deck {deck_path}: {e}"
                    )
                    continue

        logger.info(f"Successfully extracted {len(anking_cards)} cards total")
        return anking_cards

    def parse_html(self, html: str) -> Tuple[str, Dict[str, bool]]:
        """
        Strip HTML and detect formatting features.

        Parses HTML content, extracts plain text, and detects which HTML
        formatting features are used (bold, italic, lists, tables, images, etc.).

        Args:
            html: HTML string potentially containing formatting

        Returns:
            Tuple of:
            - plain_text: HTML stripped to plain text
            - features_dict: Dict with keys like 'uses_bold', 'uses_italic', etc.
                            indicating which formatting features are present
        """
        if not html:
            return "", {
                'uses_bold': False,
                'uses_italic': False,
                'uses_lists': False,
                'uses_tables': False,
                'uses_images': False
            }

        # Detect formatting features before parsing
        html_lower = html.lower()

        uses_bold = bool(re.search(r'<(b|strong)\b', html_lower))
        uses_italic = bool(re.search(r'<(i|em)\b', html_lower))
        uses_lists = bool(re.search(r'<(ul|ol|li)\b', html_lower))
        uses_tables = bool(re.search(r'<table\b', html_lower))
        uses_images = bool(re.search(r'<img\b', html_lower))

        # Parse HTML and extract plain text
        try:
            soup = BeautifulSoup(html, 'html.parser')

            # Remove script and style elements
            for script in soup(['script', 'style']):
                script.decompose()

            # Get plain text
            plain_text = soup.get_text()

            # Clean up whitespace
            plain_text = re.sub(r'\s+', ' ', plain_text).strip()

        except Exception as e:
            logger.warning(f"Failed to parse HTML: {e}")
            # Fallback: use regex to strip basic HTML tags
            plain_text = re.sub(r'<[^>]+>', '', html)
            plain_text = re.sub(r'\s+', ' ', plain_text).strip()

        features = {
            'uses_bold': uses_bold,
            'uses_italic': uses_italic,
            'uses_lists': uses_lists,
            'uses_tables': uses_tables,
            'uses_images': uses_images
        }

        return plain_text, features

    def extract_cloze(self, text: str) -> List[str]:
        """
        Extract cloze deletion patterns from text.

        Finds all {{c1::text}}, {{c2::text}}, etc. patterns and extracts
        the text portion.

        Args:
            text: Text potentially containing cloze patterns

        Returns:
            List of extracted cloze texts (empty list if none found)

        Example:
            >>> extractor.extract_cloze("This is {{c1::a test}} of {{c2::cloze}}")
            ['a test', 'cloze']
        """
        if not text:
            return []

        # Regex pattern for {{cN::text}} where N is a digit
        pattern = r'\{\{c\d+::([^}]+)\}\}'

        matches = re.findall(pattern, text)
        return matches

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Closed Anki database connection")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


if __name__ == "__main__":
    # Test the extractor with real Anki database
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    db_path = Path.home() / "Library/Application Support/Anki2/User 1/collection.anki2"

    try:
        extractor = AnkiExtractor(db_path)

        # Test 1: List decks
        print("\n=== Test 1: List AnKing Decks ===")
        decks = extractor.list_decks()
        print(f"Found {len(decks)} AnKing decks")
        for deck in decks[:5]:
            print(f"  - {deck['name']}: {deck['card_count']} cards")

        # Test 2: Extract all samples
        print("\n=== Test 2: Extract All Samples ===")
        cards = extractor.extract_all_samples(n_per_deck=25)
        print(f"Extracted {len(cards)} cards total")

        if cards:
            sample_card = cards[0]
            print(f"\nSample card:")
            print(f"  Deck: {sample_card.deck_name}")
            print(f"  Note ID: {sample_card.note_id}")
            print(f"  Text: {sample_card.text_plain[:80]}...")
            print(f"  Cloze count: {sample_card.cloze_count}")
            print(f"  Tags: {sample_card.tags}")
            print(f"  HTML features: {sample_card.html_features}")

        # Test 3: Data quality checks
        print("\n=== Test 3: Data Quality Checks ===")
        cards_with_cloze = sum(1 for c in cards if c.cloze_count > 0)
        cards_with_extra = sum(1 for c in cards if c.extra and c.extra.strip())
        cards_with_formatting = sum(1 for c in cards if any(c.html_features.values()))

        print(f"Cards with cloze deletions: {cards_with_cloze}/{len(cards)} ({100*cards_with_cloze/len(cards):.1f}%)")
        print(f"Cards with Extra field: {cards_with_extra}/{len(cards)} ({100*cards_with_extra/len(cards):.1f}%)")
        print(f"Cards with formatting: {cards_with_formatting}/{len(cards)} ({100*cards_with_formatting/len(cards):.1f}%)")

        # Test 4: Save to JSON
        print("\n=== Test 4: Save to JSON ===")
        data_dir = Path("/Users/Mitchell/coding/projects/MKSAP/anking_analysis/data/raw")
        data_dir.mkdir(parents=True, exist_ok=True)

        output_file = data_dir / "anking_cards_sample.json"

        import json
        with open(output_file, 'w') as f:
            json.dump([c.model_dump() for c in cards], f, indent=2)

        print(f"Saved {len(cards)} cards to {output_file}")

        extractor.close()
        print("\n=== Tests Complete ===")

    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        print(f"\nError: {e}")
