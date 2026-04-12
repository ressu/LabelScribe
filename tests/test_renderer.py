from PIL import Image
from labeler.renderer import render_label, CANVAS_W, CANVAS_H


def test_render_returns_correct_size():
    img = render_label("MCUs")
    assert img.size == (CANVAS_W, CANVAS_H)


def test_render_is_rgb():
    img = render_label("MCUs")
    assert img.mode == "RGB"


def test_render_has_white_background_at_corners():
    img = render_label("MCUs")
    assert img.getpixel((0, 0)) == (255, 255, 255)
    assert img.getpixel((CANVAS_W - 1, CANVAS_H - 1)) == (255, 255, 255)


def test_render_has_black_text_pixels():
    img = render_label("MCUs")
    pixels = list(img.getdata())
    black = [p for p in pixels if p == (0, 0, 0)]
    assert len(black) > 0


def test_render_long_text_does_not_crash():
    img = render_label("miscellaneous soldering tools and accessories")
    assert img.size == (CANVAS_W, CANVAS_H)
