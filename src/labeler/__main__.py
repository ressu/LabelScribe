from __future__ import annotations

import argparse
import sys
from pathlib import Path

from labeler.printer import DEFAULT_PRINTER, print_label, save_label
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

    if not args.dry_run and not Path(FONT_PATH).exists():
        print(f"Error: font not found: {FONT_PATH}", file=sys.stderr)
        sys.exit(1)

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
