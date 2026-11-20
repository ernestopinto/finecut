"""UI tests for Text Tool double-click creation, click-outside commit, and independent moving."""

from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtGui import QColor, QKeyEvent, QPixmap
from PySide6.QtTest import QTest
from pytestqt.qtbot import QtBot

from finecut.domain.models import (
    BaseImage,
    CanvasTool,
    FontFamily,
    Point,
    StrokeColor,
    StrokeObject,
    TextObject,
)
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


def test_toolbar_tool_toggle_and_four_fonts_selector(qtbot: QtBot) -> None:
    """Verify Draw/Text toggle and 4-font dropdown selector."""
    window = _load_window_with_crop(qtbot)

    assert window.draw_tool_button.isChecked() is True
    assert window.text_tool_button.isChecked() is False

    combo_fonts = [window.font_combo_box.itemText(i) for i in range(window.font_combo_box.count())]
    assert combo_fonts == [
        "Arial",
        "Times New Roman",
        "Book Antiqua",
        "Courier",
    ]

    window.text_tool_button.click()
    assert window.text_tool_button.isChecked() is True
    assert window.draw_tool_button.isChecked() is False
    assert window.document_controller.active_tool.value == CanvasTool.TEXT.value
    assert window.canvas_scene.active_tool.value == CanvasTool.TEXT.value

    window.font_combo_box.setCurrentIndex(2)
    assert window.document_controller.active_font.value == FontFamily.BOOK_ANTIQUA.value
    assert window.canvas_scene.active_font.value == FontFamily.BOOK_ANTIQUA.value


def test_text_tool_requires_double_click_and_validates_on_single_click_outside(
    qtbot: QtBot,
) -> None:
    """Verify double-click starts text, single-click outside validates/saves, and Esc cancels."""
    window = _load_window_with_crop(qtbot)
    viewport = window.canvas_view.viewport()

    window.text_tool_button.click()
    window.blue_color_button.click()
    window.set_font_family(FontFamily.COURIER)

    single_click_pos: QPoint = window.canvas_view.mapFromScene(QPointF(50.0, 50.0))
    QTest.mouseClick(
        viewport,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        single_click_pos,
    )
    assert window.canvas_scene.draft_text_item is None

    dclick_pos: QPoint = window.canvas_view.mapFromScene(QPointF(80.0, 90.0))
    QTest.mouseDClick(
        viewport,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        dclick_pos,
    )

    draft = window.canvas_scene.draft_text_item
    assert draft is not None
    assert draft.font_family == FontFamily.COURIER

    draft.setPlainText("Login Button")

    outside_click_pos: QPoint = window.canvas_view.mapFromScene(QPointF(350.0, 300.0))
    QTest.mouseClick(
        viewport,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        outside_click_pos,
    )

    assert window.canvas_scene.draft_text_item is None
    assert len(window.canvas_scene.text_items) == 1

    text_item = next(iter(window.canvas_scene.text_items.values()))
    assert text_item.toPlainText() == "Login Button"
    assert text_item.font_family == FontFamily.COURIER
    assert text_item.text_color == StrokeColor.BLUE

    second_pos: QPoint = window.canvas_view.mapFromScene(QPointF(200.0, 200.0))
    QTest.mouseDClick(
        viewport,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        second_pos,
    )
    second_draft = window.canvas_scene.draft_text_item
    assert second_draft is not None
    second_draft.setPlainText("Discard Me")
    esc_event = QKeyEvent(
        QKeyEvent.Type.KeyPress,
        Qt.Key.Key_Escape,
        Qt.KeyboardModifier.NoModifier,
    )
    second_draft.keyPressEvent(esc_event)

    assert window.canvas_scene.draft_text_item is None
    assert len(window.canvas_scene.text_items) == 1


def test_multiple_objects_move_independently_one_at_a_time(
    qtbot: QtBot,
) -> None:
    """Regression test: dragging object 2 must never move object 1 (each object is independent)."""
    window = _load_window_with_crop(qtbot)
    viewport = window.canvas_view.viewport()

    p1 = window.canvas_view.mapFromScene(QPointF(30.0, 30.0))
    p2 = window.canvas_view.mapFromScene(QPointF(120.0, 30.0))
    QTest.mousePress(
        viewport,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        p1,
    )
    QTest.mouseMove(viewport, p2)
    QTest.mouseRelease(
        viewport,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        p2,
    )

    window.text_tool_button.click()
    outside_pt = window.canvas_view.mapFromScene(QPointF(420.0, 350.0))

    for idx, font in enumerate((FontFamily.ARIAL, FontFamily.TIMES_NEW_ROMAN)):
        window.set_font_family(font)
        pos = window.canvas_view.mapFromScene(QPointF(60.0, 100.0 + idx * 100.0))
        QTest.mouseDClick(
            viewport,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
            pos,
        )
        draft = window.canvas_scene.draft_text_item
        assert draft is not None
        draft.setPlainText(f"Note {idx + 1}")
        QTest.mouseClick(
            viewport,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
            outside_pt,
        )
        assert window.canvas_scene.draft_text_item is None

    assert len(window.canvas_scene.stroke_items) == 1
    assert len(window.canvas_scene.text_items) == 2

    text_items_list = list(window.canvas_scene.text_items.values())
    first_text = text_items_list[0]
    second_text = text_items_list[1]

    first_initial_pos = QPointF(first_text.pos())
    second_initial_pos = QPointF(second_text.pos())

    c1 = first_text.sceneBoundingRect().center()
    c1_view = window.canvas_view.mapFromScene(c1)
    c1_target_view = window.canvas_view.mapFromScene(QPointF(c1.x() + 90.0, c1.y() + 20.0))
    QTest.mousePress(
        viewport,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        c1_view,
    )
    QTest.mouseMove(viewport, c1_target_view)
    QTest.mouseRelease(
        viewport,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        c1_target_view,
    )

    first_moved_pos = QPointF(first_text.pos())
    assert first_moved_pos != first_initial_pos
    assert second_text.pos() == second_initial_pos

    c2 = second_text.sceneBoundingRect().center()
    c2_view = window.canvas_view.mapFromScene(c2)
    c2_target_view = window.canvas_view.mapFromScene(QPointF(c2.x() + 110.0, c2.y() + 40.0))
    QTest.mousePress(
        viewport,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        c2_view,
    )
    QTest.mouseMove(viewport, c2_target_view)
    QTest.mouseRelease(
        viewport,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        c2_target_view,
    )

    second_moved_pos = QPointF(second_text.pos())
    assert second_moved_pos != second_initial_pos
    assert first_text.pos() == first_moved_pos

    doc = window.document_controller.current_document
    assert doc is not None
    visible_objs = doc.visible_objects()
    assert len(visible_objs) == 3
    assert isinstance(visible_objs[0], StrokeObject)
    assert isinstance(visible_objs[1], TextObject)
    assert isinstance(visible_objs[2], TextObject)
    assert visible_objs[1].position == Point(
        float(first_moved_pos.x()),
        float(first_moved_pos.y()),
    )
    assert visible_objs[2].position == Point(
        float(second_moved_pos.x()),
        float(second_moved_pos.y()),
    )
