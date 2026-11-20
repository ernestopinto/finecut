"""UI tests for the circular color swatch picker and 20-color popover palette."""

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QPixmap
from PySide6.QtTest import QTest
from pytestqt.qtbot import QtBot

from finecut.domain.models import BaseImage, StrokeColor, StrokeObject, TextObject
from finecut.infrastructure.screen_capturer import pixmap_to_base_image
from finecut.ui.main_window import FinecutMainWindow
from tests.ui.test_main_window import FakeScreenCapturer


def _sample_base_image(width: int = 500, height: int = 400) -> BaseImage:
    pixmap = QPixmap(width, height)
    pixmap.fill(QColor("#FFFFFF"))
    return pixmap_to_base_image(pixmap)


def _load_window_with_crop(qtbot: QtBot) -> FinecutMainWindow:
    window = FinecutMainWindow(screen_capturer=FakeScreenCapturer(500, 400))
    qtbot.addWidget(window)
    window.resize(820, 560)
    window.show()
    window._on_snip_captured(_sample_base_image())
    return window


def test_color_swatch_picker_opens_20_color_popover_and_selects_swatch(qtbot: QtBot) -> None:
    """Verify clicking the active swatch opens all 20 swatches and selecting one closes it."""
    window = _load_window_with_crop(qtbot)
    picker = window.color_swatch_picker

    def _active_colors() -> tuple[StrokeColor, StrokeColor, StrokeColor]:
        return (
            picker.active_color,
            window.document_controller.active_color,
            window.canvas_scene.active_color,
        )

    assert _active_colors() == (StrokeColor.RED, StrokeColor.RED, StrokeColor.RED)
    assert len(picker.swatch_buttons) == 20
    assert picker.popover.isVisible() is False

    picker.click()
    assert picker.popover.isVisible() is True

    picker.swatch_buttons[StrokeColor.GREEN].click()
    assert picker.popover.isVisible() is False
    assert _active_colors() == (StrokeColor.GREEN, StrokeColor.GREEN, StrokeColor.GREEN)
    assert picker.swatch_buttons[StrokeColor.GREEN].isChecked() is True
    assert picker.swatch_buttons[StrokeColor.RED].isChecked() is False


def test_selected_swatch_color_applies_to_strokes_and_text(qtbot: QtBot) -> None:
    """Verify newly drawn strokes and committed texts use the chosen swatch palette color."""
    window = _load_window_with_crop(qtbot)
    viewport = window.canvas_view.viewport()

    window.color_swatch_picker.click()
    window.color_swatch_picker.swatch_buttons[StrokeColor.PURPLE].click()

    p1 = window.canvas_view.mapFromScene(QPointF(40.0, 40.0))
    p2 = window.canvas_view.mapFromScene(QPointF(140.0, 80.0))
    QTest.mousePress(viewport, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, p1)
    QTest.mouseMove(viewport, p2)
    QTest.mouseRelease(viewport, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, p2)

    window.text_tool_button.click()
    window.color_swatch_picker.click()
    window.color_swatch_picker.swatch_buttons[StrokeColor.ORANGE].click()

    dclick_pos = window.canvas_view.mapFromScene(QPointF(100.0, 150.0))
    QTest.mouseDClick(
        viewport,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        dclick_pos,
    )
    draft = window.canvas_scene.draft_text_item
    assert draft is not None
    draft.setPlainText("Orange Label")

    outside_pos = window.canvas_view.mapFromScene(QPointF(380.0, 320.0))
    QTest.mouseClick(
        viewport,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        outside_pos,
    )

    doc = window.document_controller.current_document
    assert doc is not None
    objects = doc.visible_objects()
    assert len(objects) == 2
    assert isinstance(objects[0], StrokeObject)
    assert objects[0].color == StrokeColor.PURPLE
    assert isinstance(objects[1], TextObject)
    assert objects[1].color == StrokeColor.ORANGE
