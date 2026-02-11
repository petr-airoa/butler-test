from textkit.word_counter import (
    _normalize_words,
    count_unique_words,
    count_words,
    most_common_words,
    word_frequencies,
)


def test_normalize_words():
    assert _normalize_words("Hello World") == ["hello", "world"]
    assert _normalize_words("it's a test") == ["it's", "a", "test"]
    assert _normalize_words("") == []


def test_count_words():
    assert count_words("one two three") == 3
    assert count_words("") == 0
    assert count_words("hello hello hello") == 3


def test_word_frequencies():
    freqs = word_frequencies("the cat sat on the mat")
    assert freqs["the"] == 2
    assert freqs["cat"] == 1
    assert freqs["mat"] == 1


def test_most_common_words():
    text = "apple banana apple cherry apple banana"
    result = most_common_words(text, 2)
    assert result[0] == ("apple", 3)
    assert result[1] == ("banana", 2)


def test_most_common_words_default_n():
    text = "a b c d e f g"
    result = most_common_words(text)
    assert len(result) == 5


def test_count_unique_words():
    assert count_unique_words("the cat sat on the mat") == 5
    assert count_unique_words("hello hello hello") == 1
    assert count_unique_words("") == 0
