# LabelScribe

A CLI tool that generates and prints labels for multibuild drawers on a Brother
PT-P750W label printer via CUPS. Labels are 12mm × 78mm TZe tape.

## Project Overview

- **Purpose:** Automate label generation for electronics storage drawers.
- **Technologies:** Python (>=3.11), Pillow (image rendering), `uv` (dependency
  management), CUPS (printing).
- **Architecture:**
    - `src/labeler/layout.py`: Handles font sizing and text wrapping logic.
    - `src/labeler/renderer.py`: Uses Pillow to generate label images.
    - `src/labeler/printer.py`: Submits jobs to CUPS or saves them as PNGs.
    - `src/labeler/__main__.py`: CLI entry point and orchestration.

## Building and Running

The project is managed with `uv`.

### Development Setup
```sh
# Install dependencies
uv sync
```

### Running the Tool
```sh
# Basic usage
uv run labelscribe "Resistors" "Capacitors"

# Save previews instead of printing
uv run labelscribe --preview ./out "MCUs" "Tools"

# Specify a different CUPS printer
uv run labelscribe --printer "My_Printer_Name" "Label Text"

# Dry run (no rendering)
uv run labelscribe --dry-run "Test Label"
```

### Running Tests
```sh
uv run pytest
```

## Development Conventions

- **Dependencies:** Managed via `uv` in `pyproject.toml`.
- **Testing:** `pytest` is used for unit tests in the `tests/` directory.
- **Formatting:** Adheres to PEP 8.
- **Configuration:**
    - Label dimensions are fixed (12mm x 78mm).
    - Font path is currently a constant in `src/labeler/renderer.py` (Default:
      DejaVu Sans Bold).
    - Default printer name is `PT-P750W` in `src/labeler/printer.py`.

## Key Files

- `pyproject.toml`: Project metadata and dependencies.
- `docs/superpowers/specs/2026-04-12-labeler-design.md`: Original design
  specification.
- `src/labeler/layout.py`: Core logic for fitting text onto the fixed-size
  label.
