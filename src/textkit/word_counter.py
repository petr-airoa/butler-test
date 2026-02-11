"""Word counting and frequency analysis utilities."""

import re
from collections import Counter


def _normalize_words(text: str) -> list[str]:
    """Extract and lowercase all words from text."""
    return re.findall(r"[a-zA-Z']+", text.lower())


def count_words(text: str, ignore_short: int = 0, strip_punctuation: bool = False) -> int:
    """Return the total number of words, with optional filtering."""
    if strip_punctuation:
        text = re.sub(r"[^\w\s]", "", text)
    words = _normalize_words(text)
    if ignore_short > 0:
        words = [w for w in words if len(w) > ignore_short]
    return len(words)


def word_frequencies(text: str) -> dict[str, int]:
    """Return a dictionary mapping each word to its count."""
    return dict(Counter(_normalize_words(text)))


def most_common_words(text: str, n: int = 5) -> list[tuple[str, int]]:
    """Return the top N most common words as (word, count) pairs."""
    return Counter(_normalize_words(text)).most_common(n)


def unique_word_count(text: str) -> int:
    """Return the number of distinct words in text."""
    return len(set(_normalize_words(text)))
