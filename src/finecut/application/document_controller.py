"""Application controller managing CanvasDocument lifecycle, mutations, and undo/redo history."""

from collections.abc import Sequence
from uuid import uuid4

from finecut.domain.models import (
    BaseImage,
    CanvasDocument,
    CanvasTool,
    FontFamily,
    Point,
    StrokeColor,
    StrokeObject,
    TextObject,
)


class DocumentController:
    """Orchestrates active CanvasDocument creation, annotation mutations, and undo/redo stacks."""

    def __init__(self) -> None:
        self._current_document: CanvasDocument | None = None
        self._active_tool: CanvasTool = CanvasTool.DRAW
        self._active_color: StrokeColor = StrokeColor.RED
        self._active_font: FontFamily = FontFamily.ARIAL
        self._undo_stack: list[CanvasDocument] = []
        self._redo_stack: list[CanvasDocument] = []

    @property
    def current_document(self) -> CanvasDocument | None:
        """Return the currently loaded CanvasDocument, or None if no snip is loaded."""
        return self._current_document

    @property
    def has_document(self) -> bool:
        """Return True when a captured base image document is loaded."""
        return self._current_document is not None

    @property
    def can_undo(self) -> bool:
        """Return True if at least one previous document snapshot is available to undo."""
        return len(self._undo_stack) > 0

    @property
    def can_redo(self) -> bool:
        """Return True if at least one undone document snapshot is available to redo."""
        return len(self._redo_stack) > 0

    @property
    def active_tool(self) -> CanvasTool:
        """Return the currently active canvas tool (Draw or Text)."""
        return self._active_tool

    def set_active_tool(self, tool: CanvasTool) -> None:
        """Switch the active canvas tool between Draw and Text."""
        self._active_tool = tool

    @property
    def active_color(self) -> StrokeColor:
        """Return the currently selected drawing/annotation color."""
        return self._active_color

    def set_active_color(self, color: StrokeColor) -> None:
        """Set the active drawing/annotation color (Red, Blue, or Black)."""
        self._active_color = color

    @property
    def active_font(self) -> FontFamily:
        """Return the currently selected text annotation font family."""
        return self._active_font

    def set_active_font(self, font: FontFamily) -> None:
        """Set the active text annotation font family."""
        self._active_font = font

    def start_new_document(self, base_image: BaseImage) -> CanvasDocument:
        """Initialize and activate a new CanvasDocument and clear undo/redo history."""
        document = CanvasDocument.from_base_image(base_image)
        self._current_document = document
        self._undo_stack.clear()
        self._redo_stack.clear()
        return document

    def add_stroke(
        self,
        points: Sequence[Point],
        color: StrokeColor | None = None,
        stroke_width: float = 3.0,
    ) -> StrokeObject:
        """Add a completed freehand stroke to the active document and record undo snapshot."""
        if self._current_document is None:
            raise RuntimeError("Cannot add stroke when no document is loaded.")

        previous = self._current_document
        stroke_id = f"stroke-{uuid4().hex[:8]}"
        chosen_color = color if color is not None else self._active_color
        draft_stroke = StrokeObject(
            id=stroke_id,
            points=tuple(points),
            color=chosen_color,
            stroke_width=stroke_width,
        )
        self._current_document = previous.add_object(draft_stroke)
        self._record_snapshot(previous)

        for obj in self._current_document.visible_objects():
            if isinstance(obj, StrokeObject) and obj.id == stroke_id:
                return obj

        return draft_stroke

    def add_text(
        self,
        text: str,
        position: Point,
        font_family: FontFamily | None = None,
        color: StrokeColor | None = None,
        font_size: int = 16,
    ) -> TextObject:
        """Add a committed text object to the active document and record undo snapshot."""
        if self._current_document is None:
            raise RuntimeError("Cannot add text when no document is loaded.")

        previous = self._current_document
        text_id = f"text-{uuid4().hex[:8]}"
        chosen_font = font_family if font_family is not None else self._active_font
        chosen_color = color if color is not None else self._active_color
        draft_text = TextObject(
            id=text_id,
            text=text.strip(),
            font_family=chosen_font,
            position=position,
            color=chosen_color,
            font_size=font_size,
        )
        self._current_document = previous.add_object(draft_text)
        self._record_snapshot(previous)

        for obj in self._current_document.visible_objects():
            if isinstance(obj, TextObject) and obj.id == text_id:
                return obj

        return draft_text

    def move_object(self, object_id: str, new_position: Point) -> CanvasDocument:
        """Update the position of an existing object and record an undo snapshot if changed."""
        if self._current_document is None:
            raise RuntimeError("Cannot move object when no document is loaded.")

        previous = self._current_document
        for obj in previous.visible_objects():
            if obj.id == object_id and obj.position == new_position:
                return previous

        self._current_document = previous.move_object(object_id, new_position)
        self._record_snapshot(previous)
        return self._current_document

    def remove_object(self, object_id: str) -> CanvasDocument:
        """Remove an existing stroke or text object by ID and record an undo snapshot."""
        if self._current_document is None:
            raise RuntimeError("Cannot remove object when no document is loaded.")

        previous = self._current_document
        self._current_document = previous.remove_object(object_id)
        self._record_snapshot(previous)
        return self._current_document

    def undo(self) -> CanvasDocument | None:
        """Restore the previous CanvasDocument snapshot if available."""
        if not self._undo_stack or self._current_document is None:
            return None

        self._redo_stack.append(self._current_document)
        self._current_document = self._undo_stack.pop()
        return self._current_document

    def redo(self) -> CanvasDocument | None:
        """Reapply the most recently undone CanvasDocument snapshot if available."""
        if not self._redo_stack or self._current_document is None:
            return None

        self._undo_stack.append(self._current_document)
        self._current_document = self._redo_stack.pop()
        return self._current_document

    def _record_snapshot(self, previous: CanvasDocument) -> None:
        self._undo_stack.append(previous)
        self._redo_stack.clear()
