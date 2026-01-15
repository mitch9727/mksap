"""
Shared NLP utilities for validation and statement processing.

Uses spaCy/scispaCy for tokenization, lemmatization, and NER.
"""

from __future__ import annotations

from functools import lru_cache
import os
from typing import Iterable, List, Optional

try:
    import spacy
    from spacy.tokens import Doc
except ImportError as exc:  # pragma: no cover - environment-dependent
    spacy = None
    Doc = None  # type: ignore
    _SPACY_IMPORT_ERROR = exc
else:
    _SPACY_IMPORT_ERROR = None


def _env_flag(name: str, default: str = "1") -> bool:
    return os.getenv(name, default).strip().lower() not in {"0", "false", "no"}


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _env_list(name: str, default: str) -> List[str]:
    return [item.strip() for item in os.getenv(name, default).split(",") if item.strip()]


@lru_cache(maxsize=1)
def get_nlp() -> Optional["spacy.language.Language"]:
    """
    Load and cache the spaCy/scispaCy model.

    Set MKSAP_USE_NLP=0 to disable NLP usage.
    """
    if not _env_flag("MKSAP_USE_NLP", "1"):
        return None

    if spacy is None:
        raise RuntimeError(
            "spaCy/scispaCy is not installed. Install requirements and a model "
            "(e.g., en_core_sci_sm), or set MKSAP_USE_NLP=0 to disable NLP."
        ) from _SPACY_IMPORT_ERROR

    model_name = os.getenv("MKSAP_NLP_MODEL", "en_core_sci_sm")
    disable = _env_list("MKSAP_NLP_DISABLE", "parser")
    return spacy.load(model_name, disable=disable)


def nlp_pipe(texts: List[str]) -> List[Optional["Doc"]]:
    """
    Batch-process texts with spaCy/scispaCy using nlp.pipe.

    Returns a list of Docs aligned with the input list. If NLP is disabled,
    returns a list of None entries.
    """
    nlp = get_nlp()
    if nlp is None:
        return [None] * len(texts)

    batch_size = _env_int("MKSAP_NLP_BATCH_SIZE", 32)
    n_process = _env_int("MKSAP_NLP_N_PROCESS", 1)
    return list(nlp.pipe(texts, batch_size=batch_size, n_process=n_process))
