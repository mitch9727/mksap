"""
Negation detection using spaCy dependency parsing.

Detects negation in medical text using:
- Dependency parsing (walking up tree to find negation triggers)
- Preceding window analysis (for patterns like "no evidence of <entity>")
- Medical-specific negation patterns
"""

from typing import Optional, Tuple

try:
    from spacy.tokens import Doc, Span, Token
except ImportError:
    Doc = None
    Span = None
    Token = None


class NegationDetector:
    """Detect negation using dependency parsing.

    Handles medical negation patterns:
    - "no evidence of"
    - "absence of" / "absent"
    - "without"
    - "does not show" / "does not require"
    - "negative for"
    - "denies" / "denied"
    - "normal" (contextual - implies NOT abnormal)
    - "ruled out"
    """

    # Primary negation triggers
    NEGATION_TRIGGERS = frozenset({
        "no", "not", "n't", "without", "absence", "absent",
        "negative", "denies", "denied", "deny", "none",
        "neither", "nor", "never", "nothing", "nowhere",
    })

    # Medical-specific negation phrases (multi-word)
    NEGATION_PHRASES = frozenset({
        "no evidence of",
        "absence of",
        "negative for",
        "ruled out",
        "no sign of",
        "no signs of",
        "no history of",
        "fails to show",
        "failed to show",
        "does not show",
        "did not show",
        "does not require",
        "did not require",
        "not indicated",
        "not recommended",
        "contraindicated",
    })

    # Contextual negation (implies NOT the opposite)
    CONTEXTUAL_NEGATION = frozenset({
        "normal",  # implies NOT abnormal
        "unremarkable",  # implies nothing remarkable
        "stable",  # in some contexts implies NOT worsening
    })

    # Window size for preceding text analysis
    PRECEDING_WINDOW = 5

    def is_negated(
        self,
        entity: "Span",
        use_dependency_parse: bool = True
    ) -> Tuple[bool, Optional[str]]:
        """Check if entity is negated using dependency parse and pattern matching.

        Args:
            entity: spaCy Span representing the entity
            use_dependency_parse: Whether to use dependency parsing (requires parser enabled)

        Returns:
            Tuple of (is_negated: bool, negation_trigger: Optional[str])
            The trigger is the word/phrase that caused the negation detection.
        """
        if entity is None or len(entity) == 0:
            return (False, None)

        # Method 1: Check for multi-word negation phrases in context
        phrase_result = self._check_negation_phrases(entity)
        if phrase_result[0]:
            return phrase_result

        # Method 2: Dependency-based negation (if parser enabled)
        if use_dependency_parse and entity.doc.has_annotation("DEP"):
            dep_result = self._check_dependency_negation(entity)
            if dep_result[0]:
                return dep_result

        # Method 3: Preceding window analysis (fallback)
        window_result = self._check_preceding_window(entity)
        if window_result[0]:
            return window_result

        return (False, None)

    def _check_negation_phrases(self, entity: "Span") -> Tuple[bool, Optional[str]]:
        """Check for multi-word negation phrases before the entity."""
        doc_text = entity.doc.text.lower()
        entity_start = entity.start_char

        # Look for negation phrases before the entity
        for phrase in self.NEGATION_PHRASES:
            # Find phrase in the window before entity
            search_start = max(0, entity_start - 50)  # Look back up to 50 chars
            search_text = doc_text[search_start:entity_start]

            if phrase in search_text:
                return (True, phrase)

        return (False, None)

    def _check_dependency_negation(self, entity: "Span") -> Tuple[bool, Optional[str]]:
        """Check for negation using dependency parsing.

        Walks up the dependency tree from entity tokens to find negation.
        """
        for token in entity:
            # Check if token itself has negation dependency
            for child in token.children:
                if child.dep_ == "neg":
                    return (True, child.text)

            # Walk up ancestors
            for ancestor in token.ancestors:
                # Check ancestor's text
                if ancestor.text.lower() in self.NEGATION_TRIGGERS:
                    return (True, ancestor.text)

                # Check ancestor's children for negation
                for child in ancestor.children:
                    if child.dep_ == "neg":
                        return (True, child.text)

                    # Also check "not" attached via advmod
                    if child.dep_ == "advmod" and child.text.lower() in self.NEGATION_TRIGGERS:
                        return (True, child.text)

        return (False, None)

    def _check_preceding_window(self, entity: "Span") -> Tuple[bool, Optional[str]]:
        """Check preceding tokens for negation triggers."""
        sent = entity.sent
        entity_start_idx = entity.start - sent.start

        # Look at tokens before entity in same sentence
        start_idx = max(0, entity_start_idx - self.PRECEDING_WINDOW)

        for i in range(start_idx, entity_start_idx):
            token = sent[i]
            token_lower = token.text.lower()

            if token_lower in self.NEGATION_TRIGGERS:
                return (True, token.text)

            # Check for "n't" contractions
            if token_lower.endswith("n't"):
                return (True, token.text)

        return (False, None)

    def find_negation_spans(self, doc: "Doc") -> list[Tuple[str, int, int]]:
        """Find all negation trigger spans in a document.

        Returns:
            List of (trigger_text, start_char, end_char) tuples
        """
        spans = []

        for token in doc:
            token_lower = token.text.lower()

            # Single-word triggers
            if token_lower in self.NEGATION_TRIGGERS:
                spans.append((token.text, token.idx, token.idx + len(token)))

            # Contractions
            elif token_lower.endswith("n't"):
                spans.append((token.text, token.idx, token.idx + len(token)))

        # Multi-word phrases
        doc_text = doc.text.lower()
        for phrase in self.NEGATION_PHRASES:
            start = 0
            while True:
                idx = doc_text.find(phrase, start)
                if idx == -1:
                    break
                spans.append((phrase, idx, idx + len(phrase)))
                start = idx + 1

        # Sort by position and remove duplicates
        spans = sorted(set(spans), key=lambda x: x[1])

        return spans

    def get_negation_context(
        self,
        entity: "Span",
        window: int = 10
    ) -> str:
        """Get text context around entity for debugging negation detection.

        Args:
            entity: spaCy Span
            window: Number of characters before/after to include

        Returns:
            Context string with entity marked
        """
        doc_text = entity.doc.text
        start = max(0, entity.start_char - window)
        end = min(len(doc_text), entity.end_char + window)

        before = doc_text[start:entity.start_char]
        entity_text = entity.text
        after = doc_text[entity.end_char:end]

        return f"{before}[{entity_text}]{after}"
