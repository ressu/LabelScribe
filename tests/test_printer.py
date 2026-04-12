import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from PIL import Image

from labeler.printer import DEFAULT_PRINTER, _save_pdf, print_labels, save_label


def _white_image() -> Image.Image:
    return Image.new("RGB", (553, 85), color="white")


def test_default_printer_name():
    assert DEFAULT_PRINTER == "PT-P750W"


def test_save_pdf_creates_valid_pdf_file(tmp_path):
    out = tmp_path / "labels.pdf"
    _save_pdf([_white_image()], str(out))
    assert out.exists()
    assert out.read_bytes()[:4] == b"%PDF"


def test_save_pdf_multiple_images_creates_larger_file(tmp_path):
    single = tmp_path / "single.pdf"
    multi = tmp_path / "multi.pdf"
    _save_pdf([_white_image()], str(single))
    _save_pdf([_white_image(), _white_image()], str(multi))
    assert multi.stat().st_size > single.stat().st_size


def test_print_labels_calls_lp_with_pdf_and_page_size():
    mock_result = MagicMock(returncode=0)
    with patch("subprocess.run", return_value=mock_result) as mock_run:
        print_labels([_white_image()], printer="PT-P750W")
    cmd = mock_run.call_args[0][0]
    assert cmd[0] == "lp"
    assert cmd[1] == "-d"
    assert cmd[2] == "PT-P750W"
    assert "-o" in cmd
    assert any("PageSize=Custom." in arg for arg in cmd)
    assert cmd[-1].endswith(".pdf")


def test_print_labels_raises_on_lp_failure():
    mock_result = MagicMock(returncode=1, stderr="printer not found")
    with patch("subprocess.run", return_value=mock_result):
        with pytest.raises(RuntimeError, match="lp failed"):
            print_labels([_white_image()])


def test_print_labels_empty_list_does_nothing():
    with patch("subprocess.run") as mock_run:
        print_labels([])
    mock_run.assert_not_called()


def test_save_label_writes_valid_png(tmp_path):
    img = _white_image()
    out = tmp_path / "label.png"
    save_label(img, str(out))
    assert out.exists()
    loaded = Image.open(out)
    assert loaded.size == (553, 85)
