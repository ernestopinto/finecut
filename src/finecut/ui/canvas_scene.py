"""QGraphicsScene hosting the immutable cropped base image and annotation objects."""

from math import hypot

from PySide6.QtCore import QObject, QPointF, Qt, Signal
from PySide6.QtGui import QColor, QPen
from PySide6.QtWidgets import (
    QGraphicsItem,
    QGraphicsPathItem,
    QGraphicsPixmapItem,
    QGraphicsScene,
    QGraphicsSceneMouseEvent,
)

from finecut.domain.models import (
    CanvasDocument,
    CanvasTool,
    FontFamily,
    Point,
    StrokeColor,
    StrokeObject,
    TextObject,
)
from finecut.infrastructure.screen_capturer import base_image_to_pixmap
from finecut.ui.items.stroke_item import StrokeGraphicsItem, build_painter_path
from finecut.ui.items.text_item import DraftTextGraphicsItem, TextGraphicsItem

BASE_IMAGE_Z_VALUE = -1000.0
PREVIEW_STROKE_Z_VALUE = 10000.0
MIN_STROKE_DRAG_DISTANCE_PX = 2.0


class BlueprintCanvasScene(QGraphicsScene):
    """Interactive graphics scene displaying the base crop and foreground objects."""

    stroke_completed = Signal(object)
    text_committed = Signal(str, object)
    object_moved = Signal(str, object)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._base_pixmap_item: QGraphicsPixmapItem | None = None
        self._active_tool: CanvasTool = CanvasTool.DRAW
        self._active_color: StrokeColor = StrokeColor.RED
        self._active_font: FontFamily = FontFamily.ARIAL
        self._stroke_width: float = 3.0

        self._is_drawing_stroke: bool = False
        self._active_points: list[Point] = []
        self._preview_path_item: QGraphicsPathItem | None = None
        self._stroke_items: dict[str, StrokeGraphicsItem] = {}
        self._text_items: dict[str, TextGraphicsItem] = {}
        self._draft_text_item: DraftTextGraphicsItem | None = None

    @property
    def has_base_image(self) -> bool:
        """Return True if a base image pixmap is currently loaded in the scene."""
        return self._base_pixmap_item is not None

    @property
    def base_pixmap_item(self) -> QGraphicsPixmapItem | None:
        """Return the background QGraphicsPixmapItem if loaded."""
        return self._base_pixmap_item

    @property
    def active_tool(self) -> CanvasTool:
        """Return the active interaction tool (Draw or Text)."""
        return self._active_tool

    def set_active_tool(self, tool: CanvasTool) -> None:
        """Switch the active interaction tool and finalize any open draft text editor."""
        if self._draft_text_item is not None and tool != CanvasTool.TEXT:
            self._draft_text_item.commit_or_cancel()
        self._active_tool = tool

    @property
    def active_color(self) -> StrokeColor:
        """Return the active drawing/annotation color."""
        return self._active_color

    def set_active_color(self, color: StrokeColor) -> None:
        """Set the active drawing/annotation color (Red, Blue, or Black)."""
        self._active_color = color
        if self._draft_text_item is not None:
            self._draft_text_item.set_text_color(color)

    @property
    def active_font(self) -> FontFamily:
        """Return the active text annotation font family."""
        return self._active_font

    def set_active_font(self, font: FontFamily) -> None:
        """Set the active text annotation font family."""
        self._active_font = font
        if self._draft_text_item is not None:
            self._draft_text_item.set_font_family(font)

    @property
    def stroke_items(self) -> dict[str, StrokeGraphicsItem]:
        """Return a mapping of stroke IDs to their StrokeGraphicsItem instances."""
        return dict(self._stroke_items)

    @property
    def text_items(self) -> dict[str, TextGraphicsItem]:
        """Return a mapping of text IDs to their TextGraphicsItem instances."""
        return dict(self._text_items)

    @property
    def draft_text_item(self) -> DraftTextGraphicsItem | None:
        """Return the currently active inline DraftTextGraphicsItem if typing."""
        return self._draft_text_item

    def set_document(self, document: CanvasDocument) -> None:
        """Load the document's BaseImage and any existing annotation objects onto the scene."""
        self.clear()
        self._stroke_items.clear()
        self._text_items.clear()
        self._preview_path_item = None
        self._draft_text_item = None
        self._is_drawing_stroke = False
        self._active_points.clear()

        pixmap = base_image_to_pixmap(document.base_image)
        item = self.addPixmap(pixmap)
        item.setZValue(BASE_IMAGE_Z_VALUE)
        item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
        item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)
        self._base_pixmap_item = item

        logical_size = pixmap.deviceIndependentSize()
        self.setSceneRect(0.0, 0.0, logical_size.width(), logical_size.height())

        for obj in document.visible_objects():
            if isinstance(obj, StrokeObject):
                self.add_stroke_item(obj)
            elif isinstance(obj, TextObject):
                self.add_text_item(obj)

    def add_stroke_item(self, stroke: StrokeObject) -> StrokeGraphicsItem:
        """Create and add a StrokeGraphicsItem to the scene for a domain StrokeObject."""
        stroke_item = StrokeGraphicsItem(stroke, on_moved=self._notify_object_moved)
        self.addItem(stroke_item)
        self._stroke_items[stroke.id] = stroke_item
        return stroke_item

    def add_text_item(self, text_obj: TextObject) -> TextGraphicsItem:
        """Create and add a movable TextGraphicsItem to the scene for a domain TextObject."""
        text_item = TextGraphicsItem(text_obj, on_moved=self._notify_object_moved)
        self.addItem(text_item)
        self._text_items[text_obj.id] = text_item
        return text_item

    def deactivate_all_move_modes(self, except_id: str | None = None) -> None:
        """Disable double-click move mode on all stroke items except except_id."""
        for stroke_id, item in self._stroke_items.items():
            if stroke_id != except_id and item.is_move_enabled:
                item.disable_move_mode()

    def _notify_object_moved(self, object_id: str, new_position: Point) -> None:
        self.object_moved.emit(object_id, new_position)

    def _stroke_item_at(self, scene_pos: QPointF) -> StrokeGraphicsItem | None:
        for item in self.items(scene_pos):
            if isinstance(item, StrokeGraphicsItem):
                return item
        return None

    def _text_item_at(self, scene_pos: QPointF) -> TextGraphicsItem | None:
        for item in self.items(scene_pos):
            if isinstance(item, TextGraphicsItem):
                return item
        return None

    def _draft_item_at(self, scene_pos: QPointF) -> DraftTextGraphicsItem | None:
        for item in self.items(scene_pos):
            if isinstance(item, DraftTextGraphicsItem):
                return item
        return None

    def mouseDoubleClickEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self.has_base_image:
            self._cancel_preview_stroke()
            scene_pos = event.scenePos()
            hit_stroke = self._stroke_item_at(scene_pos)
            if hit_stroke is not None:
                self.deactivate_all_move_modes(except_id=hit_stroke.stroke_id)
                hit_stroke.enable_move_mode()
                event.accept()
                return
            if (
                self._active_tool == CanvasTool.TEXT
                and self._draft_text_item is None
                and self._text_item_at(scene_pos) is None
            ):
                self._start_draft_text(scene_pos)
                event.accept()
                return
        super().mouseDoubleClickEvent(event)

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self.has_base_image:
            scene_pos = event.scenePos()

            if self._draft_item_at(scene_pos) is not None:
                super().mousePressEvent(event)
                return

            if self._draft_text_item is not None:
                self._draft_text_item.commit_or_cancel()

            hit_text = self._text_item_at(scene_pos)
            if hit_text is not None:
                self.deactivate_all_move_modes()
                super().mousePressEvent(event)
                return

            hit_stroke = self._stroke_item_at(scene_pos)
            if hit_stroke is not None and hit_stroke.is_move_enabled:
                super().mousePressEvent(event)
                return

            self.deactivate_all_move_modes()

            if self._active_tool == CanvasTool.TEXT:
                self._start_draft_text(scene_pos)
                event.accept()
                return

            self._start_preview_stroke(scene_pos)
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        if self._is_drawing_stroke and self._preview_path_item is not None:
            pos = event.scenePos()
            self._active_points.append(Point(float(pos.x()), float(pos.y())))
            self._preview_path_item.setPath(build_painter_path(tuple(self._active_points)))
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self._is_drawing_stroke:
            pos = event.scenePos()
            end_pt = Point(float(pos.x()), float(pos.y()))
            if not self._active_points or self._active_points[-1] != end_pt:
                self._active_points.append(end_pt)

            points = tuple(self._active_points)
            self._cancel_preview_stroke()

            if self._has_minimum_drag_distance(points):
                self.stroke_completed.emit(points)
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def _start_draft_text(self, scene_pos: QPointF) -> None:
        position = Point(float(scene_pos.x()), float(scene_pos.y()))
        draft = DraftTextGraphicsItem(
            position=position,
            font_family=self._active_font,
            color=self._active_color,
            on_committed=self._on_draft_text_committed,
            on_cancelled=self._on_draft_text_cancelled,
        )
        self.addItem(draft)
        self._draft_text_item = draft
        self.setFocusItem(draft)
        draft.setFocus()

    def _on_draft_text_committed(self, text: str, position: Point) -> None:
        self._remove_draft_text_item()
        self.text_committed.emit(text, position)

    def _on_draft_text_cancelled(self) -> None:
        self._remove_draft_text_item()

    def _remove_draft_text_item(self) -> None:
        if self._draft_text_item is not None:
            item = self._draft_text_item
            self._draft_text_item = None
            if item.scene() is self:
                self.removeItem(item)

    def _start_preview_stroke(self, scene_pos: QPointF) -> None:
        self._is_drawing_stroke = True
        start_pt = Point(float(scene_pos.x()), float(scene_pos.y()))
        self._active_points = [start_pt]

        preview = QGraphicsPathItem()
        pen = QPen(
            QColor(self._active_color.value),
            self._stroke_width,
            Qt.PenStyle.SolidLine,
            Qt.PenCapStyle.RoundCap,
            Qt.PenJoinStyle.RoundJoin,
        )
        preview.setPen(pen)
        preview.setZValue(PREVIEW_STROKE_Z_VALUE)
        preview.setPath(build_painter_path(tuple(self._active_points)))
        self.addItem(preview)
        self._preview_path_item = preview

    def _cancel_preview_stroke(self) -> None:
        if self._preview_path_item is not None:
            self.removeItem(self._preview_path_item)
            self._preview_path_item = None
        self._is_drawing_stroke = False
        self._active_points.clear()

    @staticmethod
    def _has_minimum_drag_distance(points: tuple[Point, ...]) -> bool:
        if len(points) < 2:
            return False
        origin = points[0]
        return any(
            hypot(pt.x - origin.x, pt.y - origin.y) >= MIN_STROKE_DRAG_DISTANCE_PX
            for pt in points[1:]
        )
