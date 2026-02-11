"""Word counting and frequency analysis utilities."""

import re
from collections import Counter


def _normalize_words(text: str) -> list[str]:
    """Extract and lowercase all words from text."""
    return re.findall(r"[a-zA-Z']+", text.lower())


def count_words(text: str) -> int:
    """Return the total number of words in text."""
    return len(_normalize_words(text))


def word_frequencies(text: str) -> dict[str, int]:
    """Return a dictionary mapping each word to its count."""
    return dict(Counter(_normalize_words(text)))


def most_common_words(text: str, n: int = 5) -> list[tuple[str, int]]:
    """Return the top N most common words as (word, count) pairs."""
    return Counter(_normalize_words(text)).most_common(n)


def count_unique_words(text: str) -> int:
    """Return the number of distinct words in text."""
    return len(set(_normalize_words(text)))
