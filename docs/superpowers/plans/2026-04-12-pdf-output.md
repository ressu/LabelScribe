# PDF Multi-Page Output Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace PNG-per-job printing with a single multi-page PDF job so the PT-P750W auto-cuts between labels without priming waste.

**Architecture:** Pillow generates a multi-page PDF natively (`save_all=True`); each label is one page whose dimensions (78mm×12mm) are embedded in the PDF at 180 dpi. One `lp` call sends the whole batch; the driver's `AutoCut=True` fires between pages. `--preview` continues to save individual PNGs.

**Tech Stack:** Python, Pillow (already a dependency — no new packages needed), CUPS `lp`.

---

## File Map

| File | Change |
|---|---|
| `src/labeler/renderer.py` | Add `LABEL_DPI = 180` constant |
| `src/labeler/printer.py` | Replace `print_label` with `_save_pdf` + `print_labels`; temp file becomes `.pdf` |
| `src/labeler/__main__.py` | Import `print_labels`; dry-run fast-paths; render all then call `print_labels` once |
| `tests/test_printer.py` | Replace `print_label` tests with `_save_pdf` + `print_labels` tests |
| `tests/test_main.py` | No changes needed |
| `tests/test_layout.py` | No changes needed |
| `tests/test_renderer.py` | No changes needed |

---

## Task 1: Add `LABEL_DPI` to `renderer.py`

**Files:**
- Modify: `src/labeler/renderer.py`

`printer.py` needs to know the rendering DPI to compute the PDF page size in points. It belongs in `renderer.py` as the module that owns all canvas constants.

- [ ] **Step 1: Add the constant**

In `src/labeler/renderer.py`, add `LABEL_DPI = 180` as the first constant, before `CANVAS_W`:

```python
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
    """Render text as a CANVAS_W × CANVAS_H RGB image."""
    layout = compute_layout(text, FONT_PATH, USABLE_W, USABLE_H)
    img = Image.new("RGB", (CANVAS_W, CANVAS_H), color="white")
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
```

- [ ] **Step 2: Verify all existing tests still pass**

```bash
uv run pytest -v
```

Expected: 21 passed.

- [ ] **Step 3: Commit**

```bash
git add src/labeler/renderer.py
git commit -m "feat: export LABEL_DPI constant from renderer"
```

---

## Task 2: Rewrite `printer.py` for multi-page PDF

**Files:**
- Modify: `tests/test_printer.py`
- Modify: `src/labeler/printer.py`

### Background

`print_label(image)` is replaced by `print_labels(images)`. The new module has three public symbols:

| Symbol | Purpose |
|---|---|
| `DEFAULT_PRINTER` | Default CUPS queue name |
| `print_labels(images, printer)` | Generates multi-page PDF, submits one `lp` job |
| `save_label(image, path)` | Saves a single PNG for `--preview` (unchanged) |

Private helper `_save_pdf(images, path)` is tested directly because it encapsulates the Pillow PDF logic.

### Page size math

```
LABEL_W_PT = round(CANVAS_W * 72 / LABEL_DPI) = round(553 * 72 / 180) = 221
LABEL_H_PT = round(CANVAS_H * 72 / LABEL_DPI) = round( 85 * 72 / 180) =  34
PAGE_SIZE   = "Custom.221x34"
```

These are module-level constants so the `lp` command is easy to inspect and test.

- [ ] **Step 1: Write failing tests**

Replace the entire content of `tests/test_printer.py` with:

```python
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from PIL import Image

from labeler.printer import DEFAULT_PRINTER, _save_pdf, print_labels, save_label


def _white_image() -> Image.Image:
    return Image.new("RGB", (553, 85), color="white")


def test_default_printer_name():
    assert DEFAULT_PRINTER == "PT-P750W"


def test_save_pdf_creates_valid_pdf_file(tmp_path):
    out = tmp_path / "labels.pdf"
    _save_pdf([_white_image()], str(out))
    assert out.exists()
    assert out.read_bytes()[:4] == b"%PDF"


def test_save_pdf_multiple_images_creates_larger_file(tmp_path):
    single = tmp_path / "single.pdf"
    multi = tmp_path / "multi.pdf"
    _save_pdf([_white_image()], str(single))
    _save_pdf([_white_image(), _white_image()], str(multi))
    assert multi.stat().st_size > single.stat().st_size


def test_print_labels_calls_lp_with_pdf_and_page_size():
    mock_result = MagicMock(returncode=0)
    with patch("subprocess.run", return_value=mock_result) as mock_run:
        print_labels([_white_image()], printer="PT-P750W")
    cmd = mock_run.call_args[0][0]
    assert cmd[0] == "lp"
    assert cmd[1] == "-d"
    assert cmd[2] == "PT-P750W"
    assert "-o" in cmd
    assert any("PageSize=Custom." in arg for arg in cmd)
    assert cmd[-1].endswith(".pdf")


def test_print_labels_raises_on_lp_failure():
    mock_result = MagicMock(returncode=1, stderr="printer not found")
    with patch("subprocess.run", return_value=mock_result):
        with pytest.raises(RuntimeError, match="lp failed"):
            print_labels([_white_image()])


def test_print_labels_empty_list_does_nothing():
    with patch("subprocess.run") as mock_run:
        print_labels([])
    mock_run.assert_not_called()


def test_save_label_writes_valid_png(tmp_path):
    img = _white_image()
    out = tmp_path / "label.png"
    save_label(img, str(out))
    assert out.exists()
    loaded = Image.open(out)
    assert loaded.size == (553, 85)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_printer.py -v
```

Expected: `ImportError: cannot import name '_save_pdf'` and `cannot import name 'print_labels'`.

- [ ] **Step 3: Implement the new `printer.py`**

Replace the entire content of `src/labeler/printer.py` with:

```python
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from PIL import Image

from labeler.renderer import CANVAS_H, CANVAS_W, LABEL_DPI

DEFAULT_PRINTER = "PT-P750W"

# Label page size in PDF points (1 pt = 1/72 inch).
# 553 px @ 180 dpi = 221 pt ≈ 78 mm (feed direction / page width)
#  85 px @ 180 dpi =  34 pt ≈ 12 mm (tape width / page height)
_LABEL_W_PT = round(CANVAS_W * 72 / LABEL_DPI)
_LABEL_H_PT = round(CANVAS_H * 72 / LABEL_DPI)
_PAGE_SIZE = f"Custom.{_LABEL_W_PT}x{_LABEL_H_PT}"


def _save_pdf(images: list[Image.Image], path: str) -> None:
    """Save images as a multi-page PDF at LABEL_DPI. Each image becomes one page."""
    images[0].save(
        path,
        format="PDF",
        save_all=True,
        append_images=images[1:],
        resolution=LABEL_DPI,
    )


def print_labels(images: list[Image.Image], printer: str = DEFAULT_PRINTER) -> None:
    """Submit all labels as one multi-page PDF job.

    The driver prints each page as one label and auto-cuts between pages,
    eliminating the per-job tape priming waste of separate jobs.
    """
    if not images:
        return
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        tmp_path = f.name
    try:
        _save_pdf(images, tmp_path)
        result = subprocess.run(
            ["lp", "-d", printer, "-o", f"PageSize={_PAGE_SIZE}", tmp_path],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(f"lp failed: {result.stderr.strip()}")
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def save_label(image: Image.Image, path: str) -> None:
    """Save a single label image to path as PNG (used for --preview)."""
    image.save(path)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/test_printer.py -v
```

Expected: all 7 tests PASS.

- [ ] **Step 5: Run the full suite to catch any breakage**

```bash
uv run pytest -v
```

Expected: some tests in `test_main.py` will now fail because `__main__.py` still imports `print_label` (which no longer exists). That is expected — it will be fixed in Task 3.

- [ ] **Step 6: Commit**

```bash
git add src/labeler/printer.py tests/test_printer.py
git commit -m "feat: replace print_label with multi-page PDF print_labels"
```

---

## Task 3: Update `__main__.py` to use `print_labels`

**Files:**
- Modify: `src/labeler/__main__.py`

### Behaviour changes

- Dry-run fast-paths before rendering (no font needed, no Pillow calls)
- All labels are rendered upfront before any I/O
- Print path calls `print_labels(images, printer)` once — one PDF job, one prime, one cut at the end

`tests/test_main.py` does **not** need changes: all its tests use `--dry-run` or `--preview`, and the font-error test patches `FONT_PATH` at the `__main__` module level (still works since `__main__` still imports `FONT_PATH` from `renderer`).

- [ ] **Step 1: Confirm current test_main.py failures are only due to the broken import**

```bash
uv run pytest tests/test_main.py -v
```

Expected: errors mentioning `cannot import name 'print_label'`.

- [ ] **Step 2: Implement the updated `__main__.py`**

Replace the entire content of `src/labeler/__main__.py` with:

```python
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from labeler.printer import DEFAULT_PRINTER, print_labels, save_label
from labeler.renderer import FONT_PATH, render_label


def main() -> None:
    parser = argparse.ArgumentParser(description="Print labels for multiboard drawers")
    parser.add_argument("labels", nargs="+", metavar="LABEL", help="Text for each label")
    parser.add_argument(
        "--preview", metavar="PATH",
        help="Save label PNGs to directory instead of printing",
    )
    parser.add_argument(
        "--printer", default=DEFAULT_PRINTER,
        help=f"CUPS printer name (default: {DEFAULT_PRINTER})",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Render but do not print or save",
    )
    args = parser.parse_args()

    # Dry-run: no rendering or font required — just echo the label texts.
    if args.dry_run:
        for i, text in enumerate(args.labels, start=1):
            print(f"[dry-run] Rendered label {i}: {text!r}")
        return

    if not Path(FONT_PATH).exists():
        print(f"Error: font not found: {FONT_PATH}", file=sys.stderr)
        sys.exit(1)

    images = [render_label(text) for text in args.labels]

    if args.preview:
        out_dir = Path(args.preview)
        out_dir.mkdir(parents=True, exist_ok=True)
        for i, (text, image) in enumerate(zip(args.labels, images), start=1):
            out_path = out_dir / f"label_{i:02d}.png"
            save_label(image, str(out_path))
            print(f"Saved: {out_path}")
    else:
        print_labels(images, args.printer)
        for i, text in enumerate(args.labels, start=1):
            print(f"Printed label {i}: {text!r}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Run all tests**

```bash
uv run pytest -v
```

Expected: all 21 tests PASS.

- [ ] **Step 4: Smoke-test dry-run and preview**

```bash
uv run labeler --dry-run "MCUs" "misc soldering tools"
```

Expected:
```
[dry-run] Rendered label 1: 'MCUs'
[dry-run] Rendered label 2: 'misc soldering tools'
```

```bash
mkdir -p /tmp/label-test && uv run labeler --preview /tmp/label-test "MCUs" "resistors" && ls /tmp/label-test
```

Expected: `label_01.png  label_02.png`

- [ ] **Step 5: Commit**

```bash
git add src/labeler/__main__.py
git commit -m "feat: use print_labels in CLI, dry-run fast-path, render all before printing"
```
