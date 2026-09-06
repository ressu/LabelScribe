import pytest
from labeler.layout import compute_layout, compute_sectioned_layout, _split_text
from labeler.renderer import CANVAS_W, FONT_PATH, USABLE_W, USABLE_H


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


def test_sectioned_layout_two_sections():
    result = compute_sectioned_layout(["M3", "M4"], FONT_PATH, CANVAS_W, USABLE_H)
    assert len(result.sections) == 2
    assert result.font_size >= 10
    assert result.bounds[0][0] == 0
    assert result.bounds[-1][1] == CANVAS_W


def test_sectioned_layout_four_sections_cover_canvas_without_overlap():
    result = compute_sectioned_layout(
        ["M3", "M4", "M5", "M6"], FONT_PATH, CANVAS_W, USABLE_H
    )
    assert len(result.sections) == 4
    for (_, prev_end), (next_start, _) in zip(result.bounds, result.bounds[1:]):
        assert prev_end == next_start
    assert result.bounds[0][0] == 0
    assert result.bounds[-1][1] == CANVAS_W


def test_sectioned_layout_uses_single_shared_font_size():
    result = compute_sectioned_layout(
        ["A", "much longer caption here"], FONT_PATH, CANVAS_W, USABLE_H
    )
    # The narrow column with lots of text drives the shared size down.
    assert result.font_size == min(s.font_size for s in result.sections)


def test_sectioned_layout_font_smaller_than_full_label():
    full = compute_layout("Capacitors", FONT_PATH, USABLE_W, USABLE_H)
    sectioned = compute_sectioned_layout(
        ["Capacitors", "Resistors"], FONT_PATH, CANVAS_W, USABLE_H
    )
    assert sectioned.font_size < full.font_size


def test_sectioned_layout_long_section_splits_to_two_rows():
    result = compute_sectioned_layout(
        ["small parts assortment box", "M4"], FONT_PATH, CANVAS_W, USABLE_H
    )
    assert len(result.sections[0].rows) == 2


def test_sectioned_layout_rejects_single_section():
    with pytest.raises(ValueError):
        compute_sectioned_layout(["only"], FONT_PATH, CANVAS_W, USABLE_H)
