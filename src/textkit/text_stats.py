"""Text statistics and readability analysis, built on word_counter."""

import re

from textkit.word_counter import (
    count_unique_words,
    count_words,
    most_common_words,
    word_frequencies,
)


def average_word_length(text: str) -> float:
    """Return the average length of words in text."""
    words = re.findall(r"[a-zA-Z']+", text)
    if not words:
        return 0.0
    return sum(len(w) for w in words) / len(words)


def sentence_count(text: str) -> int:
    """Return the number of sentences (split on .!?)."""
    sentences = re.split(r"[.!?]+", text)
    return len([s for s in sentences if s.strip()])


def reading_difficulty(text: str) -> str:
    """Estimate reading difficulty: easy, moderate, or hard."""
    avg_len = average_word_length(text)
    num_words = count_words(text)
    num_sentences = sentence_count(text)

    if num_sentences == 0:
        return "easy"

    words_per_sentence = num_words / num_sentences

    if avg_len <= 4 and words_per_sentence <= 12:
        return "easy"
    elif avg_len >= 6 or words_per_sentence >= 20:
        return "hard"
    else:
        return "moderate"


def vocabulary_richness(text: str) -> float:
    """Return ratio of unique words to total words (0.0 to 1.0)."""
    total = count_words(text)
    if total == 0:
        return 0.0
    return count_unique_words(text) / total


def text_summary(text: str) -> dict:
    """Return comprehensive text statistics using word_counter functions."""
    return {
        "word_count": count_words(text),
        "sentence_count": sentence_count(text),
        "average_word_length": round(average_word_length(text), 2),
        "reading_difficulty": reading_difficulty(text),
        "vocabulary_richness": round(vocabulary_richness(text), 2),
        "word_frequencies": word_frequencies(text),
        "top_words": most_common_words(text, 3),
    }
