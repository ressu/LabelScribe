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
