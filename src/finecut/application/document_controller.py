"""Application controller managing CanvasDocument lifecycle and state transitions."""

from collections.abc import Sequence
from uuid import uuid4

from finecut.domain.models import (
    BaseImage,
    CanvasDocument,
    Point,
    StrokeColor,
    StrokeObject,
)


class DocumentController:
    """Orchestrates active CanvasDocument creation and annotation mutations."""

    def __init__(self) -> None:
        self._current_document: CanvasDocument | None = None
        self._active_color: StrokeColor = StrokeColor.RED

    @property
    def current_document(self) -> CanvasDocument | None:
        """Return the currently loaded CanvasDocument, or None if no snip is loaded."""
        return self._current_document

    @property
    def has_document(self) -> bool:
        """Return True when a captured base image document is loaded."""
        return self._current_document is not None

    @property
    def active_color(self) -> StrokeColor:
        """Return the currently selected drawing color."""
        return self._active_color

    def set_active_color(self, color: StrokeColor) -> None:
        """Set the active drawing color (Red, Blue, or Black)."""
        self._active_color = color

    def start_new_document(self, base_image: BaseImage) -> CanvasDocument:
        """Initialize and activate a new CanvasDocument from a captured BaseImage."""
        document = CanvasDocument.from_base_image(base_image)
        self._current_document = document
        return document

    def add_stroke(
        self,
        points: Sequence[Point],
        color: StrokeColor | None = None,
        stroke_width: float = 3.0,
    ) -> StrokeObject:
        """Add a completed freehand stroke to the active document and return the stored object."""
        if self._current_document is None:
            raise RuntimeError("Cannot add stroke when no document is loaded.")

        stroke_id = f"stroke-{uuid4().hex[:8]}"
        chosen_color = color if color is not None else self._active_color
        draft_stroke = StrokeObject(
            id=stroke_id,
            points=tuple(points),
            color=chosen_color,
            stroke_width=stroke_width,
        )
        self._current_document = self._current_document.add_object(draft_stroke)

        for obj in self._current_document.visible_objects():
            if isinstance(obj, StrokeObject) and obj.id == stroke_id:
                return obj

        return draft_stroke

    def move_object(self, object_id: str, new_position: Point) -> CanvasDocument:
        """Update the position of an existing stroke or text object in the active document."""
        if self._current_document is None:
            raise RuntimeError("Cannot move object when no document is loaded.")

        self._current_document = self._current_document.move_object(object_id, new_position)
        return self._current_document
