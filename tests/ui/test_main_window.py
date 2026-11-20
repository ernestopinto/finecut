"""Smoke tests for the Finecut main window."""

from PySide6.QtGui import QColor, QPixmap
from pytestqt.qtbot import QtBot

from finecut.domain.models import BaseImage, Rect
from finecut.infrastructure.screen_capturer import crop_base_image, pixmap_to_base_image
from finecut.ui.main_window import FinecutMainWindow


class FakeScreenCapturer:
    """Deterministic in-memory ScreenCapturer for UI tests."""

    def __init__(self, width: int = 400, height: int = 300) -> None:
        pixmap = QPixmap(width, height)
        pixmap.fill(QColor("#DCEEFB"))
        self._image = pixmap_to_base_image(pixmap)

    def capture_full_screen(self) -> BaseImage:
        return self._image

    def capture_region(self, region: Rect) -> BaseImage:
        return crop_base_image(self._image, region)


def test_main_window_displays_new_snip_button_and_launches_overlay(qtbot: QtBot) -> None:
    """Verify the window renders its title, + Novo button, and opens SnipOverlay on click."""
    window = FinecutMainWindow(screen_capturer=FakeScreenCapturer())
    qtbot.addWidget(window)

    assert window.windowTitle() == "Finecut"
    assert window.new_snip_button.text() == "+ Novo"
    assert window.is_showing_canvas is False

    window.new_snip_button.click()
    assert window.active_overlay is not None

    window.active_overlay.cancel_snip()
    assert window.active_overlay is None
    assert "cancelled" in window.statusBar().currentMessage()
