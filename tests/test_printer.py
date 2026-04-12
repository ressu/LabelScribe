import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from PIL import Image

from labeler.printer import DEFAULT_PRINTER, print_label, save_label


def _white_image() -> Image.Image:
    return Image.new("RGB", (553, 85), color="white")


def test_default_printer_name():
    assert DEFAULT_PRINTER == "PT-P750W"


def test_print_label_calls_lp_with_correct_args():
    img = _white_image()
    mock_result = MagicMock(returncode=0)
    with patch("subprocess.run", return_value=mock_result) as mock_run:
        print_label(img, printer="PT-P750W")
    cmd = mock_run.call_args[0][0]
    assert cmd[0] == "lp"
    assert cmd[1] == "-d"
    assert cmd[2] == "PT-P750W"
    assert cmd[3].endswith(".png")


def test_print_label_raises_on_lp_failure():
    img = _white_image()
    mock_result = MagicMock(returncode=1, stderr="printer not found")
    with patch("subprocess.run", return_value=mock_result):
        with pytest.raises(RuntimeError, match="lp failed"):
            print_label(img)


def test_save_label_writes_valid_png(tmp_path):
    img = _white_image()
    out = tmp_path / "label.png"
    save_label(img, str(out))
    assert out.exists()
    loaded = Image.open(out)
    assert loaded.size == (553, 85)
