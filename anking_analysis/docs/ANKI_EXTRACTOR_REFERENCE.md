# AnkiExtractor Reference

## Overview

The `AnkiExtractor` class is the core tool for Phase 1 Task 2 of the AnKing Analysis Pipeline. It extracts flashcards from the Anki SQLite database (collection.anki2) and prepares them for analysis.

**File Location**: `/Users/Mitchell/coding/projects/MKSAP/anking_analysis/tools/anki_extractor.py`

**Module**: `anking_analysis.tools`

## Database Location

The extractor connects to the Anki database at:
```
~/Library/Application Support/Anki2/User 1/collection.anki2
```

## Quick Start

```python
from pathlib import Path
from anking_analysis.tools.anki_extractor import AnkiExtractor

# Connect to Anki database
db_path = Path.home() / "Library/Application Support/Anki2/User 1/collection.anki2"
extractor = AnkiExtractor(db_path)

# List all AnKing decks
decks = extractor.list_decks()
print(f"Found {len(decks)} AnKing decks")

# Extract 25 cards from each deck
cards = extractor.extract_all_samples(n_per_deck=25)
print(f"Extracted {len(cards)} cards total")

# Save to JSON
import json
with open("anking_cards.json", "w") as f:
    json.dump([c.model_dump() for c in cards], f)

# Close connection
extractor.close()
```

## Class Methods

### `__init__(db_path: Path)`

Initialize the extractor and connect to the Anki database.

**Parameters:**
- `db_path` (Path): Path to the collection.anki2 file

**Raises:**
- `FileNotFoundError`: If database file doesn't exist
- `sqlite3.DatabaseError`: If database is corrupt or missing required tables

**Example:**
```python
from pathlib import Path
from anking_analysis.tools.anki_extractor import AnkiExtractor

db_path = Path.home() / "Library/Application Support/Anki2/User 1/collection.anki2"
extractor = AnkiExtractor(db_path)
```

### `list_decks() -> List[Dict]`

Get all AnKing decks with card counts.

Returns a list of dictionaries containing:
- `id` (int): Anki deck ID
- `name` (str): Full deck path (e.g., "MKSAP::Cardiovascular")
- `card_count` (int): Total number of cards in deck

Only returns decks with name containing "AnKing" or "MKSAP" and at least 25 cards.

**Returns:**
```python
[
    {'id': 1234567890, 'name': 'MKSAP::Cardiovascular', 'card_count': 156},
    {'id': 1234567891, 'name': 'MKSAP::Endocrinology', 'card_count': 89},
    ...
]
```

**Example:**
```python
decks = extractor.list_decks()
for deck in decks:
    print(f"{deck['name']}: {deck['card_count']} cards")
```

### `sample_cards(deck_id: int, n: int = 25) -> List[Dict]`

Random sample of N cards from a specific deck.

**Parameters:**
- `deck_id` (int): Anki deck ID
- `n` (int): Number of cards to sample (default: 25)

**Returns:**
List of dictionaries with keys:
- `note_id` (int): Unique note ID from Anki
- `flds` (str): Raw fields (separated by \x1f)
- `tags` (str): Space-separated tag string

**Example:**
```python
# Get 25 cards from first deck
decks = extractor.list_decks()
cards_raw = extractor.sample_cards(decks[0]['id'], n=25)
```

### `extract_all_samples(n_per_deck: int = 25) -> List[AnkingCard]`

Main orchestration method. Extracts and samples cards from ALL AnKing decks.

**Process:**
1. Lists all AnKing decks
2. For each deck, samples N random cards
3. Parses HTML and extracts cloze deletions
4. Returns AnkingCard objects

**Parameters:**
- `n_per_deck` (int): Number of cards to sample per deck (default: 25)

**Returns:**
List of `AnkingCard` objects with all fields populated and parsed.

**Example:**
```python
# Extract 25 cards from each deck (~150-200 total)
cards = extractor.extract_all_samples(n_per_deck=25)
print(f"Extracted {len(cards)} cards")

# Access card data
for card in cards[:5]:
    print(f"{card.deck_name}: {card.text_plain[:50]}...")
    print(f"  Cloze count: {card.cloze_count}")
    print(f"  Has formatting: {any(card.html_features.values())}")
```

### `parse_html(html: str) -> Tuple[str, Dict[str, bool]]`

Strip HTML and detect formatting features.

**Parameters:**
- `html` (str): HTML string potentially containing formatting

**Returns:**
Tuple of:
1. `plain_text` (str): HTML stripped to plain text
2. `features_dict` (Dict[str, bool]): Detected HTML features
   - `uses_bold`: Whether text uses `<b>` or `<strong>`
   - `uses_italic`: Whether text uses `<i>` or `<em>`
   - `uses_lists`: Whether text contains `<ul>`, `<ol>`, or `<li>`
   - `uses_tables`: Whether text contains `<table>`
   - `uses_images`: Whether text contains `<img>`

**Example:**
```python
html = "<b>Hypertension</b> is {{c1::elevated blood pressure}}"
plain, features = extractor.parse_html(html)
print(plain)  # "Hypertension is elevated blood pressure"
print(features['uses_bold'])  # True
```

### `extract_cloze(text: str) -> List[str]`

Extract cloze deletion patterns from text.

Finds all `{{cN::text}}` patterns (where N is a digit) and extracts the text portion.

**Parameters:**
- `text` (str): Text potentially containing cloze patterns

**Returns:**
List of extracted cloze texts (empty list if none found)

**Example:**
```python
text = "This is {{c1::a test}} of {{c2::cloze}}"
clozes = extractor.extract_cloze(text)
print(clozes)  # ['a test', 'cloze']
```

### `close()`

Close database connection.

**Example:**
```python
extractor.close()
```

### Context Manager Support

The extractor can be used as a context manager for automatic cleanup:

```python
with AnkiExtractor(db_path) as extractor:
    cards = extractor.extract_all_samples()
    # Connection automatically closed when exiting block
```

## AnkingCard Data Model

Each extracted card is an `AnkingCard` object with the following fields:

```python
@dataclass
class AnkingCard:
    note_id: int              # Unique note ID from Anki
    deck_path: str            # Full deck path (e.g., 'MKSAP::Cardiovascular::HF')
    deck_name: str            # Human-readable deck name
    text: str                 # Front side with HTML
    text_plain: str           # Front side without HTML
    extra: str                # Back side with HTML
    extra_plain: str          # Back side without HTML
    cloze_deletions: List[str]    # Extracted cloze patterns
    cloze_count: int          # Number of cloze deletions
    tags: List[str]           # Card tags from Anki
    html_features: Dict[str, bool]  # Detected HTML features
```

## Anki Database Schema

The extractor uses the following tables from collection.anki2:

### `decks` Table
- `id` (INTEGER): Unique deck ID
- `name` (TEXT): Full deck path (e.g., "MKSAP::Cardiovascular")

### `cards` Table
- `id` (INTEGER): Card ID
- `nid` (INTEGER): Note ID (foreign key to notes table)
- `did` (INTEGER): Deck ID (foreign key to decks table)

### `notes` Table
- `id` (INTEGER): Note ID
- `flds` (TEXT): Field data, separated by ASCII 31 character (\x1f)
- `tags` (TEXT): Space-separated tag strings

### `col` Table
- Collection metadata (not directly queried)

## Field Parsing

Anki card fields are stored in the `notes.flds` column as a single text string with fields separated by the ASCII 31 character (\x1f).

For AnKing cards:
- **Field 0 (flds[0])**: Front side (question/statement with HTML)
- **Field 1 (flds[1])**: Back side (answer/extra info with HTML)

**Example:**
```python
# Raw field data from Anki
raw_flds = "{{c1::Hypertension}}\x1fBlood pressure > 140/90 mmHg"

# After parsing
fields = raw_flds.split('\x1f')
front = fields[0]  # "{{c1::Hypertension}}"
back = fields[1]   # "Blood pressure > 140/90 mmHg"
```

## Common Usage Patterns

### Extract and Save to JSON

```python
from pathlib import Path
from anking_analysis.tools.anki_extractor import AnkiExtractor
import json

db_path = Path.home() / "Library/Application Support/Anki2/User 1/collection.anki2"

with AnkiExtractor(db_path) as extractor:
    cards = extractor.extract_all_samples(n_per_deck=25)

    # Save to JSON
    output = Path("anking_cards.json")
    with open(output, 'w') as f:
        json.dump([c.model_dump() for c in cards], f, indent=2)

    print(f"Extracted and saved {len(cards)} cards")
```

### Filter Cards by Criteria

```python
# Cards with cloze deletions
cards_with_cloze = [c for c in cards if c.cloze_count > 0]

# Cards with formatting
cards_formatted = [c for c in cards if any(c.html_features.values())]

# Cards from specific deck
cv_cards = [c for c in cards if 'Cardiovascular' in c.deck_name]
```

### Statistics and Analysis

```python
# Calculate statistics
total_cards = len(cards)
cards_with_cloze = sum(1 for c in cards if c.cloze_count > 0)
avg_cloze_per_card = sum(c.cloze_count for c in cards) / total_cards if cards else 0

# Deck breakdown
from collections import Counter
deck_counts = Counter(c.deck_name for c in cards)

print(f"Total cards: {total_cards}")
print(f"Cards with cloze: {cards_with_cloze} ({100*cards_with_cloze/total_cards:.1f}%)")
print(f"Avg cloze per card: {avg_cloze_per_card:.2f}")
print("\nCards by deck:")
for deck, count in deck_counts.most_common():
    print(f"  {deck}: {count}")
```

## Error Handling

### Database Connection Errors

```python
try:
    extractor = AnkiExtractor(db_path)
except FileNotFoundError:
    print("Anki database not found")
except sqlite3.DatabaseError as e:
    print(f"Database error: {e}")
```

### Query Errors

The extractor logs warnings for cards that fail to parse but continues processing:

```python
import logging
logging.basicConfig(level=logging.INFO)

# Any parsing errors are logged but don't stop extraction
cards = extractor.extract_all_samples()
# Check logs for any skipped cards
```

## Performance Considerations

- **Database Connection**: Connection is established once during initialization
- **Query Performance**: Queries use RANDOM() for sampling, which is efficient for large decks
- **HTML Parsing**: Uses BeautifulSoup with fallback regex stripping
- **Memory Usage**: Entire card set kept in memory (typically 150-200 cards)

## Testing

A test script is available at:
`/Users/Mitchell/coding/projects/MKSAP/test_anki_extractor.py`

Run with:
```bash
python /Users/Mitchell/coding/projects/MKSAP/test_anki_extractor.py
```

## Related Files

- **Data Model**: `/Users/Mitchell/coding/projects/MKSAP/anking_analysis/models.py`
- **Package Init**: `/Users/Mitchell/coding/projects/MKSAP/anking_analysis/tools/__init__.py`
- **Test Script**: `/Users/Mitchell/coding/projects/MKSAP/test_anki_extractor.py`

## Notes

- Only extracts from decks containing "AnKing" or "MKSAP" in the name
- Only considers decks with 25+ cards
- Sampling is random (not reproducible without seed)
- HTML parsing handles both well-formed and malformed HTML gracefully
- Cloze pattern extraction uses regex: `\{\{c\d+::([^}]+)\}\}`
