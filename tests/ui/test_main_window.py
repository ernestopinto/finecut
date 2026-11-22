"""Smoke tests for the Finecut main window."""

from PySide6.QtGui import QColor, QPixmap
from pytestqt.qtbot import QtBot

from finecut.domain.models import BaseImage, CanvasTool, Rect
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
    """Verify the window renders uniform icon-only toolbar buttons and opens SnipOverlay."""
    window = FinecutMainWindow(screen_capturer=FakeScreenCapturer())
    qtbot.addWidget(window)

    assert window.windowTitle() == "Finecut"
    icon_buttons = (
        (window.new_snip_button, "New Snip"),
        (window.area_selection_tool_button, "Area Selection"),
        (window.draw_tool_button, "Draw"),
        (window.text_tool_button, "Text"),
        (window.undo_button, "Undo"),
        (window.redo_button, "Redo"),
        (window.delete_button, "Delete"),
        (window.copy_button, "Copy"),
        (window.save_button, "Save"),
    )
    for button, expected_name in icon_buttons:
        assert button.text() == ""
        assert button.icon().isNull() is False
        assert button.accessibleName() == expected_name

    assert window.is_showing_canvas is False

    window.new_snip_button.click()
    assert window.active_overlay is not None

    window.active_overlay.cancel_snip()
    assert window.active_overlay is None
    assert "cancelled" in window.statusBar().currentMessage()


def test_toolbar_area_selection_tool_and_right_aligned_actions(qtbot: QtBot) -> None:
    """Verify Area Selection sits between New Snip and Draw, and actions align to the right."""
    window = FinecutMainWindow(screen_capturer=FakeScreenCapturer())
    qtbot.addWidget(window)
    window.resize(900, 480)
    window.show()
    qtbot.waitExposed(window)

    assert window.new_snip_button.x() < window.area_selection_tool_button.x()
    assert window.area_selection_tool_button.x() < window.draw_tool_button.x()

    # Expanding spacer pushes Undo..Save cleanly to the right edge of the toolbar
    gap_before_actions = window.undo_button.x() - (
        window.font_combo_box.x() + window.font_combo_box.width()
    )
    assert gap_before_actions > 100
    assert window.save_button.x() + window.save_button.width() > window.width() - 30

    window.area_selection_tool_button.click()
    assert window.area_selection_tool_button.isChecked() is True
    assert window.draw_tool_button.isChecked() is False
    assert window.document_controller.active_tool == CanvasTool.AREA_SELECT
    assert window.canvas_scene.active_tool == CanvasTool.AREA_SELECT
