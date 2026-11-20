"""Core domain value objects, movable canvas objects, layers, and document aggregate."""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import StrEnum


class StrokeColor(StrEnum):
    """Allowed drawing and annotation colors (strictly Red and Blue per KIS spec)."""

    RED = "#E53935"
    BLUE = "#1E88E5"


class FontFamily(StrEnum):
    """Allowed font families for text annotations."""

    ARIAL = "Arial"
    TIMES_NEW_ROMAN = "Times New Roman"
    BOOK_ANTIQUA = "Book Antiqua"
    COURIER = "Courier"


@dataclass(frozen=True, slots=True)
class Point:
    """Immutable 2D canvas coordinate."""

    x: float
    y: float

    def translated(self, dx: float, dy: float) -> Point:
        """Return a new Point shifted by (dx, dy)."""
        return Point(self.x + dx, self.y + dy)


@dataclass(frozen=True, slots=True)
class Rect:
    """Immutable rectangular screen region in pixel coordinates."""

    x: int
    y: int
    width: int
    height: int

    def __post_init__(self) -> None:
        if self.width <= 0 or self.height <= 0:
            raise ValueError("Rect width and height must be positive integers.")


@dataclass(frozen=True, slots=True)
class BaseImage:
    """Immutable cropped base screenshot decoupled from UI frameworks."""

    width: int
    height: int
    png_bytes: bytes
    device_pixel_ratio: float = 1.0

    def __post_init__(self) -> None:
        if self.width <= 0 or self.height <= 0:
            raise ValueError("BaseImage width and height must be positive integers.")
        if not self.png_bytes:
            raise ValueError("BaseImage png_bytes cannot be empty.")
        if self.device_pixel_ratio <= 0.0:
            raise ValueError("BaseImage device_pixel_ratio must be positive.")


@dataclass(frozen=True, slots=True)
class StrokeObject:
    """Independent movable freehand drawing object on the canvas."""

    id: str
    points: tuple[Point, ...]
    color: StrokeColor
    stroke_width: float = 3.0
    position: Point = Point(0.0, 0.0)
    z_index: int = 0

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("StrokeObject id cannot be empty.")
        if not self.points:
            raise ValueError("StrokeObject must contain at least one point.")
        if self.stroke_width <= 0.0:
            raise ValueError("StrokeObject stroke_width must be positive.")

    def moved_to(self, new_position: Point) -> StrokeObject:
        """Return a new StrokeObject repositioned to new_position."""
        return replace(self, position=new_position)

    def with_z_index(self, z_index: int) -> StrokeObject:
        """Return a new StrokeObject with an updated z_index."""
        return replace(self, z_index=z_index)


@dataclass(frozen=True, slots=True)
class TextObject:
    """Independent movable text annotation object committed via Enter."""

    id: str
    text: str
    font_family: FontFamily
    position: Point
    color: StrokeColor = StrokeColor.RED
    font_size: int = 16
    z_index: int = 0

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("TextObject id cannot be empty.")
        if not self.text.strip():
            raise ValueError("TextObject text cannot be empty or whitespace.")
        if self.font_size <= 0:
            raise ValueError("TextObject font_size must be positive.")

    def moved_to(self, new_position: Point) -> TextObject:
        """Return a new TextObject repositioned to new_position."""
        return replace(self, position=new_position)

    def with_z_index(self, z_index: int) -> TextObject:
        """Return a new TextObject with an updated z_index."""
        return replace(self, z_index=z_index)


type CanvasObject = StrokeObject | TextObject


@dataclass(frozen=True, slots=True)
class Layer:
    """Ordered container of canvas objects (Photoshop-ready layer abstraction)."""

    id: str
    name: str
    objects: tuple[CanvasObject, ...] = ()
    visible: bool = True
    locked: bool = False

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("Layer id cannot be empty.")
        if not self.name.strip():
            raise ValueError("Layer name cannot be empty.")


@dataclass(frozen=True, slots=True)
class CanvasDocument:
    """Root aggregate holding the cropped base image and ordered annotation layers."""

    base_image: BaseImage
    layers: tuple[Layer, ...]
    active_layer_id: str

    def __post_init__(self) -> None:
        if not self.layers:
            raise ValueError("CanvasDocument must contain at least one layer.")
        if not any(layer.id == self.active_layer_id for layer in self.layers):
            raise ValueError(f"active_layer_id '{self.active_layer_id}' not found in layers.")

    @classmethod
    def from_base_image(
        cls,
        base_image: BaseImage,
        default_layer_id: str = "layer-1",
        default_layer_name: str = "Layer 1",
    ) -> CanvasDocument:
        """Create a fresh document from a captured screen crop with one active layer."""
        default_layer = Layer(id=default_layer_id, name=default_layer_name)
        return cls(
            base_image=base_image,
            layers=(default_layer,),
            active_layer_id=default_layer.id,
        )

    def add_object(self, obj: CanvasObject) -> CanvasDocument:
        """Add a stroke or text object to the active layer with an ordered z_index."""
        next_z = (
            max((item.z_index for layer in self.layers for item in layer.objects), default=0) + 1
        )
        assigned_obj = obj.with_z_index(next_z) if obj.z_index <= 0 else obj

        updated_layers: list[Layer] = []
        for layer in self.layers:
            if layer.id == self.active_layer_id:
                if layer.locked:
                    raise ValueError("Cannot add object to a locked layer.")
                updated_layers.append(replace(layer, objects=(*layer.objects, assigned_obj)))
            else:
                updated_layers.append(layer)

        return replace(self, layers=tuple(updated_layers))

    def move_object(self, object_id: str, new_position: Point) -> CanvasDocument:
        """Return a new CanvasDocument with the target object moved to new_position."""
        found = False
        updated_layers: list[Layer] = []

        for layer in self.layers:
            new_objects: list[CanvasObject] = []
            for item in layer.objects:
                if item.id == object_id:
                    if layer.locked:
                        raise ValueError("Cannot move object on a locked layer.")
                    new_objects.append(item.moved_to(new_position))
                    found = True
                else:
                    new_objects.append(item)
            updated_layers.append(replace(layer, objects=tuple(new_objects)))

        if not found:
            raise KeyError(f"Canvas object '{object_id}' not found.")

        return replace(self, layers=tuple(updated_layers))

    def remove_object(self, object_id: str) -> CanvasDocument:
        """Return a new CanvasDocument with the target object removed."""
        found = False
        updated_layers: list[Layer] = []

        for layer in self.layers:
            new_objects: list[CanvasObject] = []
            for item in layer.objects:
                if item.id == object_id:
                    if layer.locked:
                        raise ValueError("Cannot remove object from a locked layer.")
                    found = True
                else:
                    new_objects.append(item)
            updated_layers.append(replace(layer, objects=tuple(new_objects)))

        if not found:
            raise KeyError(f"Canvas object '{object_id}' not found.")

        return replace(self, layers=tuple(updated_layers))

    def visible_objects(self) -> tuple[CanvasObject, ...]:
        """Return all objects from visible layers ordered by layer stack and z_index."""
        result: list[CanvasObject] = []
        for layer in self.layers:
            if layer.visible:
                sorted_layer_objs = sorted(layer.objects, key=lambda item: item.z_index)
                result.extend(sorted_layer_objs)
        return tuple(result)
