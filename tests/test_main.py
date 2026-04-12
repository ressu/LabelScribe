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
