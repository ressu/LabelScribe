# Labeler — Design Spec

**Date:** 2026-04-12
**Status:** Approved

## Overview

A CLI tool that generates and prints labels for multibuild drawers on a Brother PT-P750W label printer via CUPS. Labels are 12mm × 78mm TZe tape. Each positional argument to the command produces one label.

## Label Dimensions & Rendering

- Tape size: 12mm × 78mm
- Printer resolution: 180 dpi
- Canvas size: 85 px tall × 553 px wide (black on white)
- Font: DejaVu Sans Bold (path is a configurable constant for easy swapping)
- Margin: 4 px on all sides (leaves 77 px × 545 px usable area)

## Layout Logic (`layout.py`)

1. Attempt to fit the full text on a single row at the largest font size that fits the usable area.
2. If the text cannot fit at font size 10 px or larger on one row, split into two rows. Both rows use the same font size, chosen as the largest size where the longer row fits the usable width.
3. Auto-splitting only — no manual row separator needed for now.

## Architecture

Three internal modules, each with a single responsibility:

| Module | Responsibility |
|---|---|
| `layout.py` | Font sizing, single vs. two-row decision, text wrapping |
| `renderer.py` | Pillow image generation using layout output |
| `printer.py` | CUPS submission via `lp`, or PNG file save |

`__main__.py` handles CLI parsing and wires the modules together.

## CLI Interface

```
labeler [OPTIONS] LABEL [LABEL ...]
```

| Option | Description |
|---|---|
| `--preview PATH` | Save label PNGs to directory PATH instead of printing |
| `--printer NAME` | Override CUPS printer name (default: `PT-P750W`) |
| `--dry-run` | Render labels but do not print or save |

**Examples:**
```sh
labeler "MCUs" "misc soldering tools" "capacitors"
labeler --preview ./out "MCUs" "resistors"
labeler --dry-run "test label"
```

Preview filenames: `label_01.png`, `label_02.png`, etc.

## Project Structure

```
labeler/
├── pyproject.toml          # uv-managed; defines [project.scripts] entry point
├── uv.lock
├── src/
│   └── labeler/
│       ├── __init__.py
│       ├── __main__.py     # CLI entry point
│       ├── layout.py       # font sizing and row layout
│       ├── renderer.py     # Pillow image generation
│       └── printer.py      # lp submission / file save
└── docs/
    └── superpowers/
        └── specs/
            └── 2026-04-12-labeler-design.md
```

## Error Handling

- Fail fast with a clear, human-readable message.
- Font not found → tell the user which path was checked.
- `lp` non-zero exit → surface the error output.
- No silent failures, no retries.

## Dependencies

- **Runtime:** `Pillow` (image generation)
- **Python toolchain:** `uv` for dependency management and virtual environment isolation
- **System:** CUPS with `PT-P750W` printer already configured

## Out of Scope

- Manual row splitting syntax (can be added later)
- Font selection via CLI flag (font path is a code constant)
- Label templates or configuration files
- GUI or web interface
