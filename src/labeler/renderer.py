from __future__ import annotations

from PIL import Image, ImageDraw, ImageFont

from labeler.layout import DIVIDER_W, compute_layout, compute_sectioned_layout

SECTION_SEP = "|"

LABEL_DPI = 180
CANVAS_W = 549  # 77.5mm @ 180dpi
CANVAS_H = 85   # 12mm @ 180dpi
MARGIN_LR = 7   # ~1mm @ 180dpi
MARGIN_B = 7    # ~1mm @ 180dpi
MARGIN_T = 0
USABLE_W = CANVAS_W - 2 * MARGIN_LR  # 535
USABLE_H = CANVAS_H - MARGIN_B - MARGIN_T  # 78
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def _draw_rows(draw: ImageDraw.ImageDraw, rows: list[str], font: ImageFont.FreeTypeFont, cx: int) -> None:
    """Draw one or two rows vertically centered in the usable canvas height."""
    if len(rows) == 1:
        cy = MARGIN_T + USABLE_H // 2
        draw.text((cx, cy), rows[0], fill="black", font=font, anchor="mm")
    else:
        row_h = USABLE_H // 2
        for i, row in enumerate(rows):
            cy = MARGIN_T + row_h // 2 + i * row_h
            draw.text((cx, cy), row, fill="black", font=font, anchor="mm")


def render_label(text: str) -> Image.Image:
    """Render text as a CANVAS_W × CANVAS_H L (grayscale) image.

    A ``|`` in the text splits the label into that many equal-width sections,
    each with its own caption and a thin divider rule between them.
    """
    img = Image.new("L", (CANVAS_W, CANVAS_H), color="white")
    draw = ImageDraw.Draw(img)

    sections = text.split(SECTION_SEP)
    if len(sections) == 1:
        layout = compute_layout(text, FONT_PATH, USABLE_W, USABLE_H)
        font = ImageFont.truetype(FONT_PATH, layout.font_size)
        _draw_rows(draw, layout.rows, font, CANVAS_W // 2)
        return img

    sectioned = compute_sectioned_layout(sections, FONT_PATH, CANVAS_W, USABLE_H)
    font = ImageFont.truetype(FONT_PATH, sectioned.font_size)
    for i, ((x_start, x_end), result) in enumerate(zip(sectioned.bounds, sectioned.sections)):
        _draw_rows(draw, result.rows, font, (x_start + x_end) // 2)
        if i > 0:
            # Divider rule at the boundary between this section and the previous one.
            draw.line(
                [(x_start, MARGIN_T), (x_start, CANVAS_H - MARGIN_B)],
                fill="black",
                width=DIVIDER_W,
            )

    return img
