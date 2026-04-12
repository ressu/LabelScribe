from __future__ import annotations

from PIL import Image, ImageDraw, ImageFont

from labeler.layout import compute_layout

LABEL_DPI = 180
CANVAS_W = 549  # 77.5mm @ 180dpi
CANVAS_H = 85   # 12mm @ 180dpi
MARGIN_LR = 7   # ~1mm @ 180dpi
MARGIN_B = 7    # ~1mm @ 180dpi
MARGIN_T = 0
USABLE_W = CANVAS_W - 2 * MARGIN_LR  # 535
USABLE_H = CANVAS_H - MARGIN_B - MARGIN_T  # 78
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def render_label(text: str) -> Image.Image:
    """Render text as a CANVAS_W × CANVAS_H L (grayscale) image."""
    layout = compute_layout(text, FONT_PATH, USABLE_W, USABLE_H)
    img = Image.new("L", (CANVAS_W, CANVAS_H), color="white")
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(FONT_PATH, layout.font_size)

    cx = CANVAS_W // 2

    if len(layout.rows) == 1:
        # Center text in the usable height, shifted by top margin.
        cy = MARGIN_T + USABLE_H // 2
        draw.text((cx, cy), layout.rows[0], fill="black", font=font, anchor="mm")
    else:
        # Split usable height for two rows.
        row_h = USABLE_H // 2
        for i, row in enumerate(layout.rows):
            cy = MARGIN_T + row_h // 2 + i * row_h
            draw.text((cx, cy), row, fill="black", font=font, anchor="mm")

    return img
