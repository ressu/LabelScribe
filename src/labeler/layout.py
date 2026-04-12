from __future__ import annotations

import sys
from dataclasses import dataclass

from PIL import ImageFont

MIN_FONT_SIZE = 10


@dataclass
class LayoutResult:
    rows: list[str]
    font_size: int


def _measure_width(text: str, font_path: str, size: int) -> int:
    font = ImageFont.truetype(font_path, size)
    bbox = font.getbbox(text)
    return bbox[2] - bbox[0]


def _split_text(text: str) -> tuple[str, str]:
    """Split text into two roughly equal halves at a word boundary."""
    words = text.split()
    if len(words) == 1:
        mid = len(text) // 2
        return text[:mid], text[mid:]
    best = 1
    best_diff = float("inf")
    for i in range(1, len(words)):
        diff = abs(len(" ".join(words[:i])) - len(" ".join(words[i:])))
        if diff < best_diff:
            best_diff = diff
            best = i
    return " ".join(words[:best]), " ".join(words[best:])


def compute_layout(
    text: str,
    font_path: str,
    usable_w: int,
    usable_h: int,
) -> LayoutResult:
    """Return the best single- or two-row layout for text.

    Chooses whichever layout (one row or two rows) yields the larger font size,
    so that long text is split rather than crammed onto one line at a tiny size.
    """
    # Find the largest font size for single-row layout.
    single_size = MIN_FONT_SIZE - 1
    for size in range(usable_h, MIN_FONT_SIZE - 1, -1):
        if _measure_width(text, font_path, size) <= usable_w:
            single_size = size
            break

    # Find the largest font size for two-row layout.
    row1, row2 = _split_text(text)
    row_h = usable_h // 2
    two_size = MIN_FONT_SIZE - 1
    for size in range(row_h, MIN_FONT_SIZE - 1, -1):
        if (
            _measure_width(row1, font_path, size) <= usable_w
            and _measure_width(row2, font_path, size) <= usable_w
        ):
            two_size = size
            break

    # Prefer the layout that allows the larger font size.
    if two_size > single_size and two_size >= MIN_FONT_SIZE:
        return LayoutResult(rows=[row1, row2], font_size=two_size)
    if single_size >= MIN_FONT_SIZE:
        return LayoutResult(rows=[text], font_size=single_size)
    print(f"Warning: text too long to fit, clamped to minimum font size: {text!r}", file=sys.stderr)
    return LayoutResult(rows=[row1, row2], font_size=MIN_FONT_SIZE)
