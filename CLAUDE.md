# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository. See also `GEMINI.md` for Gemini CLI guidance on this same project.

## Commands

```sh
# Install dependencies
uv sync

# Run all tests
uv run pytest

# Run a single test file
uv run pytest tests/test_layout.py

# Run a single test by name
uv run pytest tests/test_layout.py::test_short_text_fits_single_row

# Print labels
uv run labelscribe "Resistors" "Capacitors"

# Preview labels as PNGs (no printer required)
uv run labelscribe --preview ./out "Tools"

# Multi-section label ("|" splits one label into equal-width sections)
uv run labelscribe "M3|M4|M5|M6"

# Dry run (no rendering, no font required)
uv run labelscribe --dry-run "Tools"
```

## Architecture

The tool renders 12mm × 77.5mm labels for a Brother PT-P750W printer and sends them as a multi-page PDF via CUPS (`lp`).

**Pipeline:** `__main__` → `renderer` → `layout` → `printer`

- **`layout.py`** — `compute_layout()` decides whether text fits on one or two rows and finds the largest font size that fits within the usable canvas area. `compute_sectioned_layout()` handles `|`-delimited multi-section labels: it lays out each section with `compute_layout()` inside its own equal-width column and unifies them to one font size. All layout decisions happen here.
- **`renderer.py`** — `render_label()` produces a PIL grayscale (`L` mode) image at 180 DPI. Text with no `|` goes through `compute_layout()`; text with `|` goes through `compute_sectioned_layout()` and gets thin divider rules drawn between sections. Canvas constants (`CANVAS_W`, `CANVAS_H`, `USABLE_W`, `USABLE_H`, `FONT_PATH`) live here and are imported by other modules.
- **`printer.py`** — `print_labels()` saves all images as a single multi-page PDF (each image rotated 90° for portrait tape orientation), then submits the PDF to CUPS with the correct custom page size. Batching into one job avoids per-job tape priming waste.
- **`__main__.py`** — CLI entry point; handles `--preview` (save PNGs), `--dry-run` (no rendering), and default print mode.

Tests require the DejaVu Bold font at `/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf` (used by `render_label` and `compute_layout`). Printer tests mock `subprocess.run` to avoid a real CUPS dependency.
