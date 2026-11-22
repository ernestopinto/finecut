"""Verification tests for Windows packaging assets, launchers, and version consistency."""

import struct
from pathlib import Path

from pytestqt.qtbot import QtBot

from finecut import __version__
from finecut.ui.toolbar_icons import create_app_icon

REPO_ROOT = Path(__file__).resolve().parents[2]
PACKAGING_DIR = REPO_ROOT / "packaging"


def test_finecut_ico_exists_and_contains_multiple_png_frames() -> None:
    """Verify packaging/assets/finecut.ico is a valid multi-resolution Windows ICO file."""
    ico_path = PACKAGING_DIR / "assets" / "finecut.ico"
    assert ico_path.is_file()

    data = ico_path.read_bytes()
    assert len(data) > 64
    reserved, ico_type, frame_count = struct.unpack("<HHH", data[:6])
    assert reserved == 0
    assert ico_type == 1
    assert frame_count >= 6


def test_packaging_files_exist_and_align_with_app_version() -> None:
    """Verify PyInstaller spec, Inno Setup script, version metadata, and dev launcher exist."""
    spec_path = PACKAGING_DIR / "finecut.spec"
    iss_path = PACKAGING_DIR / "installer.iss"
    version_info_path = PACKAGING_DIR / "version_info.txt"
    build_script_path = PACKAGING_DIR / "build_windows.ps1"
    dev_launcher_path = REPO_ROOT / "run_finecut.bat"

    for path in (spec_path, iss_path, version_info_path, build_script_path, dev_launcher_path):
        assert path.is_file(), f"Missing packaging file: {path}"

    spec_text = spec_path.read_text(encoding="utf-8")
    assert "console=False" in spec_text
    assert 'name="Finecut"' in spec_text

    iss_text = iss_path.read_text(encoding="utf-8")
    assert f'#define AppVersion "{__version__}"' in iss_text
    assert "FinecutSetup-" in iss_text

    version_text = version_info_path.read_text(encoding="utf-8")
    assert f'"{__version__}"' in version_text

    launcher_text = dev_launcher_path.read_text(encoding="utf-8")
    assert "pythonw.exe" in launcher_text
    assert "finecut.main" in launcher_text


def test_create_app_icon_returns_valid_icon(qtbot: QtBot) -> None:
    """Verify runtime window/taskbar QIcon renders cleanly."""
    del qtbot
    icon = create_app_icon()
    assert icon.isNull() is False
    assert len(icon.availableSizes()) >= 4
