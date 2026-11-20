"""UI tests for freehand drawing in Red/Blue/Black and double-click-to-move stroke objects."""

from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtGui import QColor, QPixmap
from PySide6.QtTest import QTest
from pytestqt.qtbot import QtBot

from finecut.domain.models import BaseImage, Point, StrokeColor, StrokeObject
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
    window.resize(700, 560)
    window.show()
    window._on_snip_captured(_sample_base_image())
    return window


def test_toolbar_color_buttons_switch_active_color(qtbot: QtBot) -> None:
    """Verify clicking Red, Blue, and Black toolbar buttons updates controller and scene color."""
    window = _load_window_with_crop(qtbot)

    def _current_colors() -> tuple[StrokeColor, StrokeColor]:
        return (window.document_controller.active_color, window.canvas_scene.active_color)

    assert window.red_color_button.isChecked() is True
    assert _current_colors() == (StrokeColor.RED, StrokeColor.RED)

    window.blue_color_button.click()
    assert window.blue_color_button.isChecked() is True
    assert window.red_color_button.isChecked() is False
    assert _current_colors() == (StrokeColor.BLUE, StrokeColor.BLUE)

    window.black_color_button.click()
    assert window.black_color_button.isChecked() is True
    assert window.blue_color_button.isChecked() is False
    assert _current_colors() == (StrokeColor.BLACK, StrokeColor.BLACK)


def test_freehand_drawing_creates_n_independent_stroke_objects(qtbot: QtBot) -> None:
    """Verify dragging on the canvas creates n independent strokes in Red, Blue, and Black."""
    window = _load_window_with_crop(qtbot)
    viewport = window.canvas_view.viewport()

    p1_start = window.canvas_view.mapFromScene(QPointF(40.0, 40.0))
    p1_end = window.canvas_view.mapFromScene(QPointF(140.0, 90.0))
    QTest.mousePress(
        viewport,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        p1_start,
    )
    QTest.mouseMove(viewport, p1_end)
    QTest.mouseRelease(
        viewport,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        p1_end,
    )

    window.blue_color_button.click()
    p2_start = window.canvas_view.mapFromScene(QPointF(60.0, 120.0))
    p2_end = window.canvas_view.mapFromScene(QPointF(180.0, 180.0))
    QTest.mousePress(
        viewport,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        p2_start,
    )
    QTest.mouseMove(viewport, p2_end)
    QTest.mouseRelease(
        viewport,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        p2_end,
    )

    window.black_color_button.click()
    p3_start = window.canvas_view.mapFromScene(QPointF(80.0, 200.0))
    p3_end = window.canvas_view.mapFromScene(QPointF(220.0, 250.0))
    QTest.mousePress(
        viewport,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        p3_start,
    )
    QTest.mouseMove(viewport, p3_end)
    QTest.mouseRelease(
        viewport,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        p3_end,
    )

    doc = window.document_controller.current_document
    assert doc is not None
    strokes = [obj for obj in doc.visible_objects() if isinstance(obj, StrokeObject)]
    assert len(strokes) == 3
    assert [s.color for s in strokes] == [
        StrokeColor.RED,
        StrokeColor.BLUE,
        StrokeColor.BLACK,
    ]
    assert len(window.canvas_scene.stroke_items) == 3


def test_double_click_enables_move_mode_and_dragging_updates_stroke_position(
    qtbot: QtBot,
) -> None:
    """Verify double-clicking a completed stroke unlocks it for dragging and syncs position."""
    window = _load_window_with_crop(qtbot)
    viewport = window.canvas_view.viewport()

    start_pt = QPointF(100.0, 100.0)
    mid_pt = QPointF(150.0, 100.0)
    end_pt = QPointF(200.0, 100.0)

    QTest.mousePress(
        viewport,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        window.canvas_view.mapFromScene(start_pt),
    )
    QTest.mouseMove(viewport, window.canvas_view.mapFromScene(mid_pt))
    QTest.mouseRelease(
        viewport,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        window.canvas_view.mapFromScene(end_pt),
    )

    stroke_items = list(window.canvas_scene.stroke_items.values())
    assert len(stroke_items) == 1
    stroke_item = stroke_items[0]
    assert stroke_item.is_move_enabled is False
    assert stroke_item.pos() == QPointF(0.0, 0.0)

    mid_view_pt: QPoint = window.canvas_view.mapFromScene(mid_pt)
    QTest.mouseDClick(
        viewport,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        mid_view_pt,
    )
    assert stroke_item.is_move_enabled is True

    drag_target_view_pt: QPoint = window.canvas_view.mapFromScene(QPointF(200.0, 160.0))
    QTest.mousePress(
        viewport,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        mid_view_pt,
    )
    QTest.mouseMove(viewport, drag_target_view_pt)
    QTest.mouseRelease(
        viewport,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        drag_target_view_pt,
    )

    assert stroke_item.pos() != QPointF(0.0, 0.0)
    doc = window.document_controller.current_document
    assert doc is not None
    stored_stroke = doc.visible_objects()[0]
    assert stored_stroke.position == Point(
        float(stroke_item.pos().x()),
        float(stroke_item.pos().y()),
    )

    empty_start = window.canvas_view.mapFromScene(QPointF(20.0, 20.0))
    empty_end = window.canvas_view.mapFromScene(QPointF(50.0, 20.0))
    QTest.mousePress(
        viewport,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        empty_start,
    )
    QTest.mouseMove(viewport, empty_end)
    QTest.mouseRelease(
        viewport,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        empty_end,
    )
    assert stroke_item.is_move_enabled is False
    assert len(window.canvas_scene.stroke_items) == 2
