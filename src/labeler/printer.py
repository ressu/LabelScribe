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
