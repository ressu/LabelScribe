from PIL import Image
from labeler.renderer import render_label, CANVAS_W, CANVAS_H


def test_render_returns_correct_size():
    img = render_label("MCUs")
    assert img.size == (CANVAS_W, CANVAS_H)


def test_render_is_grayscale():
    img = render_label("MCUs")
    assert img.mode == "L"


def test_render_has_white_background_at_corners():
    img = render_label("MCUs")
    assert img.getpixel((0, 0)) == 255
    assert img.getpixel((CANVAS_W - 1, CANVAS_H - 1)) == 255


def test_render_has_black_text_pixels():
    img = render_label("MCUs")
    w, h = img.size
    black_found = any(
        img.getpixel((x, y)) == 0
        for y in range(h)
        for x in range(w)
    )
    assert black_found


def test_render_long_text_does_not_crash():
    img = render_label("miscellaneous soldering tools and accessories")
    assert img.size == (CANVAS_W, CANVAS_H)


def test_render_two_section_label_size_and_mode():
    img = render_label("Resistors|Capacitors")
    assert img.size == (CANVAS_W, CANVAS_H)
    assert img.mode == "L"


def test_render_two_section_label_has_center_divider():
    img = render_label("Resistors|Capacitors")
    h = img.size[1]
    mid = CANVAS_W // 2
    divider_col = any(
        img.getpixel((x, y)) == 0
        for x in range(mid - 3, mid + 3)
        for y in range(h)
    )
    assert divider_col


def test_render_four_section_label_does_not_crash():
    img = render_label("M3|M4|M5|M6")
    assert img.size == (CANVAS_W, CANVAS_H)


def test_render_plain_label_has_no_forced_divider():
    # A label with no "|" must not gain any section divider rules.
    img = render_label("MM")  # narrow text, leaves the vertical center clear
    h = img.size[1]
    mid = CANVAS_W // 2
    full_black_column = any(
        all(img.getpixel((x, y)) == 0 for y in range(h))
        for x in range(mid - 2, mid + 2)
    )
    assert not full_black_column
