"""Unit tests for DocumentController."""

import pytest

from finecut.application.document_controller import DocumentController
from finecut.domain.models import BaseImage, Point, StrokeColor, StrokeObject


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
    assert controller.active_color == StrokeColor.RED

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
