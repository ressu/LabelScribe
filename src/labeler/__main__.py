from __future__ import annotations

import argparse
import sys
from pathlib import Path

from labeler.printer import DEFAULT_PRINTER, print_labels, save_label
from labeler.renderer import FONT_PATH, render_label


def main() -> None:
    parser = argparse.ArgumentParser(description="Print labels for multibuild drawers")
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
        print(f"Printed {len(images)} label(s) to {args.printer}:")
        for i, text in enumerate(args.labels, start=1):
            print(f"  {i}. {text}")


if __name__ == "__main__":
    main()
