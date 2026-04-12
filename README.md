# LabelScribe

A CLI tool for generating and printing labels for [Multibuild](https://multibuild.io/) drawers using a Brother P-touch (PT-P750W) printer.

## Features

- Generates 12mm x 77.5mm labels optimized for 3D-printed drawer tolerances.
- Automatic text wrapping (one or two rows).
- Multi-page PDF output for batch printing via CUPS.
- PNG preview support.

## Requirements

- Python 3.11+
- [uv](https://github.com/astral-sh/uv)
- CUPS with a configured P-touch printer (default: `PT-P750W`).

## Usage

```sh
# Install dependencies
uv sync

# Print labels
uv run labelscribe "Resistors" "Capacitors" "MCUs"

# Preview labels as PNGs
uv run labelscribe --preview ./out "Tools"

# Show options
uv run labelscribe --help
```
