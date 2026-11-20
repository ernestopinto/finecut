"""Unit tests for Finecut domain models, invariants, and CanvasDocument operations."""

import ast
from dataclasses import replace
from pathlib import Path

import pytest

from finecut.domain import (
    BaseImage,
    CanvasDocument,
    FontFamily,
    Layer,
    Point,
    Rect,
    StrokeColor,
    StrokeObject,
    TextObject,
)


def _sample_base_image() -> BaseImage:
    return BaseImage(width=800, height=600, png_bytes=b"\x89PNG\r\n\x1a\n", device_pixel_ratio=1.25)


def test_allowed_colors_and_fonts_match_spec() -> None:
    """Verify the 20 classic swatch colors and 4 classic font families exist."""
    assert len(StrokeColor) == 20
    assert {StrokeColor.RED, StrokeColor.BLUE, StrokeColor.BLACK}.issubset(set(StrokeColor))
    assert StrokeColor.DARK_RED.display_name == "Dark Red"
    assert StrokeColor.RED.display_name == "Red"
    assert [font.value for font in FontFamily] == [
        "Arial",
        "Times New Roman",
        "Book Antiqua",
        "Courier",
    ]


def test_point_and_rect_validation() -> None:
    """Verify Point translation and Rect positive dimension validation."""
    pt = Point(10.0, 20.0)
    assert pt.translated(5.5, -2.0) == Point(15.5, 18.0)

    rect = Rect(x=0, y=0, width=300, height=200)
    assert rect.width == 300

    with pytest.raises(ValueError, match="positive"):
        Rect(x=0, y=0, width=0, height=100)

    with pytest.raises(ValueError, match="positive"):
        Rect(x=0, y=0, width=100, height=-5)


def test_base_image_invariants() -> None:
    """Verify BaseImage rejects invalid dimensions, empty bytes, or invalid DPI."""
    image = _sample_base_image()
    assert image.width == 800
    assert image.device_pixel_ratio == 1.25

    with pytest.raises(ValueError, match="positive"):
        BaseImage(width=0, height=100, png_bytes=b"data")

    with pytest.raises(ValueError, match="empty"):
        BaseImage(width=100, height=100, png_bytes=b"")

    with pytest.raises(ValueError, match="device_pixel_ratio"):
        BaseImage(width=100, height=100, png_bytes=b"data", device_pixel_ratio=0.0)


def test_stroke_and_text_object_invariants() -> None:
    """Verify StrokeObject and TextObject validate inputs and support moving."""
    stroke = StrokeObject(
        id="stroke-1",
        points=(Point(0.0, 0.0), Point(10.0, 15.0)),
        color=StrokeColor.RED,
    )
    moved_stroke = stroke.moved_to(Point(25.0, 30.0))
    assert moved_stroke.position == Point(25.0, 30.0)

    with pytest.raises(ValueError, match="at least one point"):
        StrokeObject(id="s-empty", points=(), color=StrokeColor.BLUE)

    text_obj = TextObject(
        id="text-1",
        text="Submit Button",
        font_family=FontFamily.ARIAL,
        position=Point(50.0, 60.0),
    )
    moved_text = text_obj.moved_to(Point(100.0, 120.0))
    assert moved_text.position == Point(100.0, 120.0)

    with pytest.raises(ValueError, match="empty or whitespace"):
        TextObject(
            id="t-blank",
            text="   ",
            font_family=FontFamily.COURIER,
            position=Point(0.0, 0.0),
        )


def test_canvas_document_supports_n_objects_moving_and_removing() -> None:
    """Verify adding n strokes/texts over a base image, moving any object, and removing it."""
    doc = CanvasDocument.from_base_image(_sample_base_image())

    stroke_1 = StrokeObject(
        id="s1",
        points=(Point(1.0, 1.0), Point(20.0, 20.0)),
        color=StrokeColor.RED,
    )
    stroke_2 = StrokeObject(
        id="s2",
        points=(Point(5.0, 5.0), Point(40.0, 40.0)),
        color=StrokeColor.BLUE,
    )
    text_1 = TextObject(
        id="t1",
        text="Header Blueprint",
        font_family=FontFamily.BOOK_ANTIQUA,
        position=Point(12.0, 18.0),
    )

    doc = doc.add_object(stroke_1).add_object(stroke_2).add_object(text_1)
    visible = doc.visible_objects()
    assert len(visible) == 3
    assert [obj.id for obj in visible] == ["s1", "s2", "t1"]
    assert [obj.z_index for obj in visible] == [1, 2, 3]

    doc = doc.move_object("s1", Point(150.0, 200.0))
    doc = doc.move_object("t1", Point(300.0, 400.0))
    updated_visible = {obj.id: obj for obj in doc.visible_objects()}
    assert updated_visible["s1"].position == Point(150.0, 200.0)
    assert updated_visible["t1"].position == Point(300.0, 400.0)

    doc = doc.remove_object("s2")
    assert [obj.id for obj in doc.visible_objects()] == ["s1", "t1"]

    with pytest.raises(KeyError, match="not found"):
        doc.move_object("non-existent", Point(0.0, 0.0))


def test_canvas_document_respects_layer_visibility_and_lock() -> None:
    """Verify locked layers reject edits and hidden layers are omitted from visible_objects."""
    base = _sample_base_image()
    locked_layer = Layer(id="locked-1", name="Locked Layer", locked=True)
    doc = CanvasDocument(base_image=base, layers=(locked_layer,), active_layer_id="locked-1")

    stroke = StrokeObject(id="s1", points=(Point(0.0, 0.0),), color=StrokeColor.RED)
    with pytest.raises(ValueError, match="locked layer"):
        doc.add_object(stroke)

    unlocked = replace(locked_layer, locked=False, visible=False, objects=(stroke,))
    hidden_doc = CanvasDocument(base_image=base, layers=(unlocked,), active_layer_id="locked-1")
    assert hidden_doc.visible_objects() == ()


def test_domain_package_has_zero_pyside6_imports() -> None:
    """Enforce architectural boundary: domain layer must never import PySide6."""
    domain_dir = Path(__file__).resolve().parents[2] / "src" / "finecut" / "domain"
    for py_file in domain_dir.glob("*.py"):
        tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert not alias.name.startswith("PySide6")
            elif isinstance(node, ast.ImportFrom) and node.module:
                assert not node.module.startswith("PySide6")
