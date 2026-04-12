# Labeler Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a CLI tool that renders 12mm×78mm labels as PNG images and sends them to a Brother PT-P750W via CUPS.

**Architecture:** Three single-responsibility modules (`layout.py`, `renderer.py`, `printer.py`) wired together by `__main__.py`. Layout computes font size and row splits; renderer generates a Pillow image; printer submits via `lp` or saves to disk.

**Tech Stack:** Python ≥ 3.11, Pillow ≥ 10, uv, pytest, CUPS (`lp` CLI), DejaVu Sans Bold system font.

---

## File Map

| Path | Purpose |
|---|---|
| `pyproject.toml` | Project metadata, dependencies, entry point |
| `src/labeler/__init__.py` | Empty package marker |
| `src/labeler/layout.py` | Font-size search and text-split logic |
| `src/labeler/renderer.py` | Pillow image generation; owns canvas constants |
| `src/labeler/printer.py` | `lp` subprocess submission and file save |
| `src/labeler/__main__.py` | `argparse` CLI, wires the three modules |
| `tests/test_layout.py` | Unit tests for layout logic |
| `tests/test_renderer.py` | Unit tests for image output |
| `tests/test_printer.py` | Unit tests for printer (mocked subprocess) |
| `tests/test_main.py` | Integration tests via subprocess |

---

## Task 1: Project Scaffold

**Files:**
- Create: `pyproject.toml`
- Create: `src/labeler/__init__.py`
- Create: `tests/__init__.py`

- [ ] **Step 1: Write `pyproject.toml`**

```toml
[project]
name = "labeler"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "Pillow>=10.0.0",
]

[project.scripts]
labeler = "labeler.__main__:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/labeler"]

[dependency-groups]
dev = [
    "pytest>=8.0.0",
]
```

- [ ] **Step 2: Create package and test markers**

```bash
mkdir -p src/labeler tests
touch src/labeler/__init__.py tests/__init__.py
```

- [ ] **Step 3: Install dependencies**

```bash
uv sync --group dev
```

Expected: lock file written, `.venv` created, Pillow and pytest installed.

- [ ] **Step 4: Verify pytest runs**

```bash
uv run pytest --collect-only
```

Expected: `no tests ran` (0 items collected), exit 0.

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml uv.lock src/ tests/
git commit -m "chore: scaffold project with uv and pytest"
```

---

## Task 2: `layout.py` — Font Sizing and Row Splitting

**Files:**
- Create: `tests/test_layout.py`
- Create: `src/labeler/layout.py`

### Constants referenced throughout this task

```
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
USABLE_W  = 545   # CANVAS_W (553) - 2 * MARGIN (4)
USABLE_H  = 77    # CANVAS_H (85)  - 2 * MARGIN (4)
MIN_FONT  = 10
```

- [ ] **Step 1: Write failing tests**

Create `tests/test_layout.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_layout.py -v
```

Expected: `ImportError: cannot import name 'compute_layout'` for all tests.

- [ ] **Step 3: Implement `layout.py`**

Create `src/labeler/layout.py`:

```python
from __future__ import annotations

from dataclasses import dataclass, field

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
    """Return the best single- or two-row layout for text."""
    # Try single row: largest font size (bounded by usable_h) that fits width.
    for size in range(usable_h, MIN_FONT_SIZE - 1, -1):
        if _measure_width(text, font_path, size) <= usable_w:
            return LayoutResult(rows=[text], font_size=size)

    # Fall back to two rows at the same font size.
    row1, row2 = _split_text(text)
    row_h = usable_h // 2
    for size in range(row_h, MIN_FONT_SIZE - 1, -1):
        if (
            _measure_width(row1, font_path, size) <= usable_w
            and _measure_width(row2, font_path, size) <= usable_w
        ):
            return LayoutResult(rows=[row1, row2], font_size=size)

    return LayoutResult(rows=[row1, row2], font_size=MIN_FONT_SIZE)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/test_layout.py -v
```

Expected: all 6 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/labeler/layout.py tests/test_layout.py
git commit -m "feat: add layout module with font sizing and auto row split"
```

---

## Task 3: `renderer.py` — Pillow Image Generation

**Files:**
- Create: `tests/test_renderer.py`
- Create: `src/labeler/renderer.py`

### Constants this module owns

```
CANVAS_W = 553   # px  (78mm @ 180 dpi)
CANVAS_H = 85    # px  (12mm @ 180 dpi)
MARGIN   = 4     # px
USABLE_W = 545   # CANVAS_W - 2*MARGIN
USABLE_H = 77    # CANVAS_H - 2*MARGIN
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
```

- [ ] **Step 1: Write failing tests**

Create `tests/test_renderer.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_renderer.py -v
```

Expected: `ImportError: cannot import name 'render_label'` for all tests.

- [ ] **Step 3: Implement `renderer.py`**

Create `src/labeler/renderer.py`:

```python
from __future__ import annotations

from PIL import Image, ImageDraw, ImageFont

from labeler.layout import compute_layout

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

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/test_renderer.py -v
```

Expected: all 5 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/labeler/renderer.py tests/test_renderer.py
git commit -m "feat: add renderer module using Pillow"
```

---

## Task 4: `printer.py` — CUPS Submission and File Save

**Files:**
- Create: `tests/test_printer.py`
- Create: `src/labeler/printer.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_printer.py`:

```python
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from PIL import Image

from labeler.printer import DEFAULT_PRINTER, print_label, save_label


def _white_image() -> Image.Image:
    return Image.new("RGB", (553, 85), color="white")


def test_default_printer_name():
    assert DEFAULT_PRINTER == "PT-P750W"


def test_print_label_calls_lp_with_correct_args():
    img = _white_image()
    mock_result = MagicMock(returncode=0)
    with patch("subprocess.run", return_value=mock_result) as mock_run:
        print_label(img, printer="PT-P750W")
    cmd = mock_run.call_args[0][0]
    assert cmd[0] == "lp"
    assert cmd[1] == "-d"
    assert cmd[2] == "PT-P750W"
    assert cmd[3].endswith(".png")


def test_print_label_raises_on_lp_failure():
    img = _white_image()
    mock_result = MagicMock(returncode=1, stderr="printer not found")
    with patch("subprocess.run", return_value=mock_result):
        with pytest.raises(RuntimeError, match="lp failed"):
            print_label(img)


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

Expected: `ImportError: cannot import name 'print_label'` for all tests.

- [ ] **Step 3: Implement `printer.py`**

Create `src/labeler/printer.py`:

```python
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from PIL import Image

DEFAULT_PRINTER = "PT-P750W"


def print_label(image: Image.Image, printer: str = DEFAULT_PRINTER) -> None:
    """Submit image to CUPS printer via lp."""
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        tmp_path = f.name
    try:
        image.save(tmp_path)
        result = subprocess.run(
            ["lp", "-d", printer, tmp_path],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(f"lp failed: {result.stderr.strip()}")
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def save_label(image: Image.Image, path: str) -> None:
    """Save image to path as PNG."""
    image.save(path)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/test_printer.py -v
```

Expected: all 4 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/labeler/printer.py tests/test_printer.py
git commit -m "feat: add printer module for CUPS submission and file save"
```

---

## Task 5: `__main__.py` — CLI Entry Point

**Files:**
- Create: `tests/test_main.py`
- Create: `src/labeler/__main__.py`

- [ ] **Step 1: Write failing integration tests**

Create `tests/test_main.py`:

```python
import sys
import subprocess
from pathlib import Path

from PIL import Image


def _run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "labeler", *args],
        capture_output=True,
        text=True,
    )


def test_dry_run_single_label():
    result = _run("--dry-run", "MCUs")
    assert result.returncode == 0
    assert "MCUs" in result.stdout


def test_dry_run_multiple_labels():
    result = _run("--dry-run", "MCUs", "resistors")
    assert result.returncode == 0
    assert "MCUs" in result.stdout
    assert "resistors" in result.stdout


def test_preview_saves_numbered_pngs(tmp_path):
    result = _run("--preview", str(tmp_path), "MCUs", "resistors")
    assert result.returncode == 0
    assert (tmp_path / "label_01.png").exists()
    assert (tmp_path / "label_02.png").exists()


def test_preview_writes_correct_image_size(tmp_path):
    _run("--preview", str(tmp_path), "MCUs")
    img = Image.open(tmp_path / "label_01.png")
    assert img.size == (553, 85)


def test_no_args_exits_nonzero():
    result = _run()
    assert result.returncode != 0
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_main.py -v
```

Expected: all tests fail — `No module named labeler.__main__` or missing argument error.

- [ ] **Step 3: Implement `__main__.py`**

Create `src/labeler/__main__.py`:

```python
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from labeler.printer import DEFAULT_PRINTER, print_label, save_label
from labeler.renderer import FONT_PATH, render_label


def main() -> None:
    if not Path(FONT_PATH).exists():
        print(f"Error: font not found: {FONT_PATH}", file=sys.stderr)
        sys.exit(1)

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

    for i, text in enumerate(args.labels, start=1):
        image = render_label(text)
        if args.dry_run:
            print(f"[dry-run] Rendered label {i}: {text!r}")
        elif args.preview:
            out_dir = Path(args.preview)
            out_dir.mkdir(parents=True, exist_ok=True)
            out_path = out_dir / f"label_{i:02d}.png"
            save_label(image, str(out_path))
            print(f"Saved: {out_path}")
        else:
            print_label(image, args.printer)
            print(f"Printed label {i}: {text!r}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run all tests**

```bash
uv run pytest -v
```

Expected: all 20 tests PASS.

- [ ] **Step 5: Smoke-test the entry point**

```bash
uv run labeler --dry-run "MCUs" "misc soldering tools"
```

Expected output:
```
[dry-run] Rendered label 1: 'MCUs'
[dry-run] Rendered label 2: 'misc soldering tools'
```

- [ ] **Step 6: Commit**

```bash
git add src/labeler/__main__.py tests/test_main.py
git commit -m "feat: add CLI entry point, wire layout/renderer/printer"
```
