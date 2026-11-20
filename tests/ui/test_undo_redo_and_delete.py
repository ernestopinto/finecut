"""UI tests for object deletion (Del), Escape deselection, and Undo/Redo (Ctrl+Z / Ctrl+Y)."""

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QKeyEvent, QPixmap
from pytestqt.qtbot import QtBot

from finecut.domain.models import BaseImage, FontFamily, Point, StrokeColor
from finecut.infrastructure.screen_capturer import pixmap_to_base_image
from finecut.ui.main_window import FinecutMainWindow
from tests.ui.test_main_window import FakeScreenCapturer


def _sample_base_image(width: int = 400, height: int = 300) -> BaseImage:
    pixmap = QPixmap(width, height)
    pixmap.fill(QColor("#FFFFFF"))
    return pixmap_to_base_image(pixmap)


def _load_window_with_crop(qtbot: QtBot) -> FinecutMainWindow:
    window = FinecutMainWindow(screen_capturer=FakeScreenCapturer(400, 300))
    qtbot.addWidget(window)
    window.resize(820, 560)
    window.show()
    window._on_snip_captured(_sample_base_image())
    return window


def test_undo_and_redo_toolbar_buttons_restore_strokes_and_texts(qtbot: QtBot) -> None:
    """Verify Undo and Redo buttons step backward and forward through canvas annotations."""
    window = _load_window_with_crop(qtbot)

    assert window.undo_button.isEnabled() is False
    assert window.redo_button.isEnabled() is False

    window._on_stroke_completed((Point(20.0, 20.0), Point(120.0, 80.0)))
    assert len(window.canvas_scene.stroke_items) == 1
    assert window.undo_button.isEnabled() is True
    assert window.redo_button.isEnabled() is False

    window.set_stroke_color(StrokeColor.BLUE)
    window.set_font_family(FontFamily.BOOK_ANTIQUA)
    window._on_text_committed("Title Box", Point(60.0, 140.0))
    assert len(window.canvas_scene.text_items) == 1

    window.undo_button.click()
    assert len(window.canvas_scene.text_items) == 0
    assert len(window.canvas_scene.stroke_items) == 1
    assert window.redo_button.isEnabled() is True

    window.undo_button.click()
    assert len(window.canvas_scene.stroke_items) == 0
    assert window.undo_button.isEnabled() is False

    window.redo_button.click()
    assert len(window.canvas_scene.stroke_items) == 1
    assert len(window.canvas_scene.text_items) == 0

    window.redo_button.click()
    assert len(window.canvas_scene.stroke_items) == 1
    assert len(window.canvas_scene.text_items) == 1
    assert window.redo_button.isEnabled() is False


def test_delete_selected_stroke_and_text_and_escape_clears_move_mode(qtbot: QtBot) -> None:
    """Verify deleting a move-enabled stroke or selected text object, Undo restore, and Escape."""
    window = _load_window_with_crop(qtbot)

    assert window.delete_selected_objects() == 0
    assert "Select a drawing" in window.statusBar().currentMessage()

    window._on_stroke_completed((Point(40.0, 40.0), Point(160.0, 40.0)))
    window._on_text_committed("Delete Me", Point(80.0, 120.0))
    assert len(window.canvas_scene.stroke_items) == 1
    assert len(window.canvas_scene.text_items) == 1

    stroke_item = next(iter(window.canvas_scene.stroke_items.values()))
    stroke_item.enable_move_mode()
    assert window.canvas_scene.selected_object_ids() == (stroke_item.stroke_id,)

    esc_event = QKeyEvent(
        QKeyEvent.Type.KeyPress,
        Qt.Key.Key_Escape,
        Qt.KeyboardModifier.NoModifier,
    )
    window.canvas_scene.keyPressEvent(esc_event)
    assert stroke_item.is_move_enabled is False
    assert window.canvas_scene.selected_object_ids() == ()

    stroke_item.enable_move_mode()
    window.delete_button.click()
    assert len(window.canvas_scene.stroke_items) == 0
    assert len(window.canvas_scene.text_items) == 1
    assert "Deleted 1 object(s)." in window.statusBar().currentMessage()

    text_item = next(iter(window.canvas_scene.text_items.values()))
    text_item.setSelected(True)
    assert window.canvas_scene.selected_object_ids() == (text_item.text_id,)

    window.delete_button.click()
    assert len(window.canvas_scene.text_items) == 0

    window.undo_button.click()
    assert len(window.canvas_scene.text_items) == 1
    window.undo_button.click()
    assert len(window.canvas_scene.stroke_items) == 1
    assert len(window.canvas_scene.text_items) == 1
