# AGENTS.md

Guidance for AI coding agents (Claude Code, Gemini CLI, others) working in this
repo. `CLAUDE.md` and `GEMINI.md` are symlinks to this file — edit only this one.

## Overview

`labelscribe` is a CLI that renders 12mm × 77.5mm labels for a Brother PT-P750W
label printer and submits them to CUPS (`lp`) as one batched multi-page PDF. Each
positional argument produces one label. Intended use: labels for Multibuild
electronics-storage drawers.

## Commands

```sh
uv sync                                          # install deps
uv run pytest                                    # all tests
uv run pytest tests/test_layout.py               # one file
uv run pytest tests/test_layout.py::test_short_text_fits_single_row  # one test

uv run labelscribe "Resistors" "Capacitors"      # print
uv run labelscribe "M3|M4|M5|M6"                 # one label, 4 sections (see below)
uv run labelscribe --preview ./out "Tools"       # write label_NN.png, no printer
uv run labelscribe --printer NAME "Tools"        # override CUPS printer (default: PT-P750W)
uv run labelscribe --dry-run "Tools"             # echo only — no render, no font needed
```

## Architecture

Pipeline: `__main__` → `renderer` → `layout` → `printer`.

- **`layout.py`** — all layout math, no drawing. `compute_layout()` picks a
  one-row or two-row layout by whichever yields the *larger* font size that fits
  the usable area (down to `MIN_FONT_SIZE = 10`; below that it warns and clamps).
  Two-row splits happen automatically at a word boundary. `compute_sectioned_layout()`
  handles `|`-delimited labels: each section is laid out with `compute_layout()`
  in its own equal-width column, then all sections render at the smallest
  per-section font size for a consistent look.
- **`renderer.py`** — `render_label()` returns a PIL `L`-mode (grayscale) image
  at 180 DPI. No `|` → `compute_layout()`; with `|` → `compute_sectioned_layout()`
  plus a thin vertical divider rule between sections. Owns every canvas constant
  (`CANVAS_W = 549`, `CANVAS_H = 85`, `MARGIN_LR/MARGIN_B/MARGIN_T`, `USABLE_W/H`,
  `LABEL_DPI = 180`, `FONT_PATH`, `SECTION_SEP = "|"`); other modules import them
  from here.
- **`printer.py`** — `print_labels()` rotates each image 90° for portrait tape
  orientation, writes one multi-page PDF, and submits it with
  `lp -d <printer> -o PageSize=Custom.<W>x<L>`. Batching into a single job avoids
  the per-job tape priming waste of separate jobs. `save_label()` writes a single
  PNG for `--preview`.
- **`__main__.py`** — argparse CLI. `--dry-run` short-circuits before any render
  or font-existence check.

## Multi-section labels

A `|` splits one physical label into N equal-width columns (N ≥ 2), one per
compartment of a divided bin: `"A|B"`, `"M3|M4|M5|M6"`. Empty sections (`"A||C"`)
render blank. A literal `|` in label text is not supported.

## Conventions

- Tests require DejaVu Bold at
  `/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf` (used by `render_label`
  and `compute_layout`). Printer tests mock `subprocess.run` — no real CUPS
  dependency.
- Python ≥ 3.11, PEP 8. Dependencies managed with `uv` in `pyproject.toml`.
- Fail fast: clear human-readable message, no retries, no silent failures.
  Font-not-found names the path checked; a non-zero `lp` exit surfaces its
  stderr.
- Fixed by design — do not add CLI flags for these: label dimensions, font path
  (a code constant in `renderer.py`), row splitting (auto only, no manual
  separator). Out of scope: label templates, config files, GUI/web interface.
- Committed design docs go in `docs/specs/`. Keep this file and `README.md` in
  sync when behavior changes; `README.md` is the human-facing doc. Don't restate
  this file's content elsewhere.
