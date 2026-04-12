import pytest
from labeler.layout import compute_layout, _split_text

FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
USABLE_W = 545
USABLE_H = 77


def test_short_text_fits_single_row():
    result = compute_layout("MCUs", FONT_PATH, USABLE_W, USABLE_H)
    assert result.rows == ["MCUs"]
    assert result.font_size >= 10


def test_long_text_splits_to_two_rows():
    result = compute_layout(
        "miscellaneous soldering tools and accessories",
        FONT_PATH, USABLE_W, USABLE_H,
    )
    assert len(result.rows) == 2
    assert result.font_size >= 10


def test_two_rows_preserve_all_words():
    text = "miscellaneous soldering tools and accessories"
    result = compute_layout(text, FONT_PATH, USABLE_W, USABLE_H)
    assert " ".join(result.rows) == text


def test_split_text_two_words():
    assert _split_text("hello world") == ("hello", "world")


def test_split_text_single_word_splits_at_midpoint():
    left, right = _split_text("hello")
    assert left + right == "hello"
    assert len(left) > 0 and len(right) > 0


def test_split_text_balances_line_lengths():
    left, right = _split_text("one two three four")
    assert abs(len(left) - len(right)) <= 5
