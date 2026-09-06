from __future__ import annotations

import sys
from dataclasses import dataclass

from PIL import ImageFont

MIN_FONT_SIZE = 10

# Multi-section labels: a thin vertical rule between sections plus inner padding
# so text does not touch the divider.
DIVIDER_W = 2
SECTION_PAD = 10


@dataclass
class LayoutResult:
    rows: list[str]
    font_size: int


@dataclass
class SectionedLayout:
    sections: list[LayoutResult]      # one per section, left to right
    font_size: int                    # unified size used for every section
    bounds: list[tuple[int, int]]     # (x_start, x_end) of each section on the canvas


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


def compute_sectioned_layout(
    sections: list[str],
    font_path: str,
    canvas_w: int,
    usable_h: int,
) -> SectionedLayout:
    """Lay out several captions side by side in equal-width columns.

    Each section is laid out independently with ``compute_layout`` inside its own
    column, then all sections are rendered at the smallest of the per-section font
    sizes so the label reads consistently.
    """
    n = len(sections)
    if n < 2:
        raise ValueError("compute_sectioned_layout requires at least 2 sections")

    # Equal columns; hand the rounding remainder to the leftmost sections.
    base_w, extra = divmod(canvas_w, n)
    bounds: list[tuple[int, int]] = []
    x = 0
    for i in range(n):
        col_w = base_w + (1 if i < extra else 0)
        bounds.append((x, x + col_w))
        x += col_w

    results: list[LayoutResult] = []
    for text, (x_start, x_end) in zip(sections, bounds):
        section_usable_w = (x_end - x_start) - 2 * SECTION_PAD - DIVIDER_W
        results.append(compute_layout(text, font_path, section_usable_w, usable_h))

    font_size = max(MIN_FONT_SIZE, min(r.font_size for r in results))
    return SectionedLayout(sections=results, font_size=font_size, bounds=bounds)
