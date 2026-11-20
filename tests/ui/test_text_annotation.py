"""UI tests for Text Annotation Tool (4 fonts, Enter-to-commit) and movable text objects."""

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
    window.resize(760, 560)
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


def test_text_tool_click_type_enter_commits_and_escape_cancels(qtbot: QtBot) -> None:
    """Verify clicking canvas in Text mode opens draft editor, Enter commits, and Esc cancels."""
    window = _load_window_with_crop(qtbot)
    viewport = window.canvas_view.viewport()

    window.text_tool_button.click()
    window.blue_color_button.click()
    window.set_font_family(FontFamily.COURIER)

    click_pos: QPoint = window.canvas_view.mapFromScene(QPointF(80.0, 90.0))
    QTest.mouseClick(
        viewport,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        click_pos,
    )

    draft = window.canvas_scene.draft_text_item
    assert draft is not None
    assert draft.font_family == FontFamily.COURIER

    draft.setPlainText("Login Button")
    enter_event = QKeyEvent(
        QKeyEvent.Type.KeyPress,
        Qt.Key.Key_Return,
        Qt.KeyboardModifier.NoModifier,
    )
    draft.keyPressEvent(enter_event)

    assert window.canvas_scene.draft_text_item is None
    assert len(window.canvas_scene.text_items) == 1

    text_item = next(iter(window.canvas_scene.text_items.values()))
    assert text_item.toPlainText() == "Login Button"
    assert text_item.font_family == FontFamily.COURIER
    assert text_item.text_color == StrokeColor.BLUE

    second_pos: QPoint = window.canvas_view.mapFromScene(QPointF(200.0, 200.0))
    QTest.mouseClick(
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


def test_committed_text_object_is_movable_and_coexists_with_n_drawings(
    qtbot: QtBot,
) -> None:
    """Verify committed text objects can be dragged/moved and coexist with n drawings."""
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
    for idx, font in enumerate((FontFamily.ARIAL, FontFamily.TIMES_NEW_ROMAN)):
        window.set_font_family(font)
        pos = window.canvas_view.mapFromScene(QPointF(60.0, 110.0 + idx * 80.0))
        QTest.mouseClick(
            viewport,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
            pos,
        )
        draft = window.canvas_scene.draft_text_item
        assert draft is not None
        draft.setPlainText(f"Note {idx + 1}")
        enter_event = QKeyEvent(
            QKeyEvent.Type.KeyPress,
            Qt.Key.Key_Return,
            Qt.KeyboardModifier.NoModifier,
        )
        draft.keyPressEvent(enter_event)

    assert len(window.canvas_scene.stroke_items) == 1
    assert len(window.canvas_scene.text_items) == 2

    first_text_item = next(iter(window.canvas_scene.text_items.values()))
    initial_pos = QPointF(first_text_item.pos())
    item_center = first_text_item.sceneBoundingRect().center()
    start_view_pt: QPoint = window.canvas_view.mapFromScene(item_center)
    target_view_pt: QPoint = window.canvas_view.mapFromScene(
        QPointF(item_center.x() + 80.0, item_center.y() + 60.0)
    )

    QTest.mousePress(
        viewport,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        start_view_pt,
    )
    QTest.mouseMove(viewport, target_view_pt)
    QTest.mouseRelease(
        viewport,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        target_view_pt,
    )

    assert first_text_item.pos() != initial_pos
    doc = window.document_controller.current_document
    assert doc is not None
    visible_objs = doc.visible_objects()
    assert len(visible_objs) == 3
    assert isinstance(visible_objs[0], StrokeObject)
    assert isinstance(visible_objs[1], TextObject)
    assert isinstance(visible_objs[2], TextObject)
    assert visible_objs[1].position == Point(
        float(first_text_item.pos().x()),
        float(first_text_item.pos().y()),
    )
