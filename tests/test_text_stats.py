from textkit.text_stats import (
    average_word_length,
    reading_difficulty,
    sentence_count,
    text_summary,
)


def test_average_word_length():
    assert average_word_length("hi there") == 3.5  # (2 + 5) / 2
    assert average_word_length("") == 0.0


def test_sentence_count():
    assert sentence_count("Hello. World! How?") == 3
    assert sentence_count("No punctuation") == 1
    assert sentence_count("") == 0


def test_reading_difficulty_easy():
    assert reading_difficulty("The cat sat. The dog ran.") == "easy"


def test_reading_difficulty_hard():
    long_sentence = " ".join(["extraordinary"] * 25)
    assert reading_difficulty(long_sentence + ".") == "hard"


def test_text_summary():
    text = "The quick brown fox. The lazy dog."
    summary = text_summary(text)
    assert summary["word_count"] == 7
    assert summary["sentence_count"] == 2
    assert isinstance(summary["average_word_length"], float)
    assert summary["reading_difficulty"] in ("easy", "moderate", "hard")
    assert isinstance(summary["word_frequencies"], dict)
    assert isinstance(summary["top_words"], list)
