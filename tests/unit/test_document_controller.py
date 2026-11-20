"""Unit tests for DocumentController."""

import pytest

from finecut.application.document_controller import DocumentController
from finecut.domain.models import (
    BaseImage,
    CanvasTool,
    FontFamily,
    Point,
    StrokeColor,
    StrokeObject,
    TextObject,
)


def _sample_image() -> BaseImage:
    return BaseImage(
        width=640,
        height=400,
        png_bytes=b"\x89PNG\r\n\x1a\n",
        device_pixel_ratio=1.0,
    )


def test_document_controller_lifecycle() -> None:
    """Verify DocumentController starts empty and initializes a CanvasDocument on snip."""
    controller = DocumentController()
    assert controller.current_document is None
    assert controller.has_document is False
    assert controller.can_undo is False
    assert controller.can_redo is False
    assert controller.active_tool == CanvasTool.DRAW
    assert controller.active_color == StrokeColor.RED
    assert controller.active_font == FontFamily.ARIAL

    sample_image = _sample_image()
    document = controller.start_new_document(sample_image)

    assert controller.has_document is True
    assert controller.current_document == document
    assert document.base_image == sample_image
    assert len(document.layers) == 1
    assert document.layers[0].name == "Layer 1"


def test_document_controller_add_and_move_strokes_in_three_colors() -> None:
    """Verify adding n strokes in Red, Blue, and Black and moving a stroke by ID."""
    controller = DocumentController()

    with pytest.raises(RuntimeError, match="no document is loaded"):
        controller.add_stroke((Point(0.0, 0.0), Point(10.0, 10.0)))

    with pytest.raises(RuntimeError, match="no document is loaded"):
        controller.move_object("s-1", Point(5.0, 5.0))

    controller.start_new_document(_sample_image())

    red_stroke = controller.add_stroke((Point(10.0, 10.0), Point(50.0, 50.0)))
    assert red_stroke.color == StrokeColor.RED
    assert red_stroke.z_index == 1

    controller.set_active_color(StrokeColor.BLUE)
    blue_stroke = controller.add_stroke((Point(20.0, 20.0), Point(80.0, 60.0)))
    assert blue_stroke.color == StrokeColor.BLUE
    assert blue_stroke.z_index == 2

    controller.set_active_color(StrokeColor.BLACK)
    black_stroke = controller.add_stroke((Point(30.0, 30.0), Point(90.0, 90.0)))
    assert black_stroke.color == StrokeColor.BLACK
    assert black_stroke.z_index == 3

    updated_doc = controller.move_object(red_stroke.id, Point(120.0, 140.0))
    visible = {
        obj.id: obj for obj in updated_doc.visible_objects() if isinstance(obj, StrokeObject)
    }
    assert visible[red_stroke.id].position == Point(120.0, 140.0)
    assert visible[blue_stroke.id].position == Point(0.0, 0.0)
    assert visible[black_stroke.id].position == Point(0.0, 0.0)


def test_document_controller_add_and_move_text_in_four_fonts() -> None:
    """Verify adding n text objects across the 4 fonts and moving a committed text object."""
    controller = DocumentController()

    with pytest.raises(RuntimeError, match="no document is loaded"):
        controller.add_text("Header", Point(10.0, 20.0))

    controller.start_new_document(_sample_image())
    controller.set_active_tool(CanvasTool.TEXT)
    assert controller.active_tool.value == "text"

    created_texts: list[TextObject] = []
    for idx, font in enumerate(FontFamily):
        controller.set_active_font(font)
        text_obj = controller.add_text(
            text=f"Label {idx}",
            position=Point(float(idx * 20), float(idx * 30)),
        )
        assert text_obj.font_family == font
        created_texts.append(text_obj)

    assert len(created_texts) == 4
    assert [t.font_family for t in created_texts] == [
        FontFamily.ARIAL,
        FontFamily.TIMES_NEW_ROMAN,
        FontFamily.BOOK_ANTIQUA,
        FontFamily.COURIER,
    ]

    updated_doc = controller.move_object(created_texts[0].id, Point(250.0, 310.0))
    visible_texts = {
        obj.id: obj for obj in updated_doc.visible_objects() if isinstance(obj, TextObject)
    }
    assert visible_texts[created_texts[0].id].position == Point(250.0, 310.0)


def test_document_controller_undo_redo_and_remove_object() -> None:
    """Verify undo/redo history across stroke add, text add, move, and remove_object."""
    controller = DocumentController()

    with pytest.raises(RuntimeError, match="no document is loaded"):
        controller.remove_object("missing")
    assert controller.undo() is None
    assert controller.redo() is None

    controller.start_new_document(_sample_image())
    assert controller.can_undo is False
    assert controller.can_redo is False

    stroke = controller.add_stroke((Point(0.0, 0.0), Point(25.0, 25.0)))
    assert controller.can_undo is True
    assert controller.can_redo is False

    text_obj = controller.add_text("Action", Point(40.0, 50.0))
    assert controller.current_document is not None
    assert len(controller.current_document.visible_objects()) == 2

    controller.move_object(text_obj.id, Point(40.0, 50.0))
    controller.move_object(text_obj.id, Point(100.0, 120.0))
    controller.remove_object(stroke.id)

    assert [obj.id for obj in controller.current_document.visible_objects()] == [text_obj.id]

    doc_after_undo_remove = controller.undo()
    assert doc_after_undo_remove is not None
    assert [obj.id for obj in doc_after_undo_remove.visible_objects()] == [
        stroke.id,
        text_obj.id,
    ]
    assert controller.can_redo is True

    doc_after_undo_move = controller.undo()
    assert doc_after_undo_move is not None
    restored_text = doc_after_undo_move.visible_objects()[1]
    assert restored_text.position == Point(40.0, 50.0)

    doc_after_redo_move = controller.redo()
    assert doc_after_redo_move is not None
    reapplied_text = doc_after_redo_move.visible_objects()[1]
    assert reapplied_text.position == Point(100.0, 120.0)

    controller.start_new_document(_sample_image())
    assert controller.can_undo is False
    assert controller.can_redo is False
