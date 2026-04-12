from __future__ import annotations

from PIL import Image, ImageDraw, ImageFont

from labeler.layout import compute_layout

LABEL_DPI = 180
CANVAS_W = 553
CANVAS_H = 85
MARGIN = 4
USABLE_W = CANVAS_W - 2 * MARGIN  # 545
USABLE_H = CANVAS_H - 2 * MARGIN  # 77
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def render_label(text: str) -> Image.Image:
    """Render text as a CANVAS_W × CANVAS_H L (grayscale) image."""
    layout = compute_layout(text, FONT_PATH, USABLE_W, USABLE_H)
    img = Image.new("L", (CANVAS_W, CANVAS_H), color="white")
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(FONT_PATH, layout.font_size)

    cx = CANVAS_W // 2

    if len(layout.rows) == 1:
        draw.text((cx, CANVAS_H // 2), layout.rows[0], fill="black", font=font, anchor="mm")
    else:
        row_h = CANVAS_H // 2
        for i, row in enumerate(layout.rows):
            cy = row_h // 2 + i * row_h
            draw.text((cx, cy), row, fill="black", font=font, anchor="mm")

    return img
