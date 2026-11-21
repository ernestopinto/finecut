"""Interactive QGraphicsPathItem representing a movable freehand drawing stroke."""

from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPainterPathStroker, QPen
from PySide6.QtWidgets import (
    QGraphicsItem,
    QGraphicsPathItem,
    QGraphicsSceneMouseEvent,
    QStyleOptionGraphicsItem,
    QWidget,
)

from finecut.domain.models import Point, StrokeColor, StrokeObject

HIT_TEST_PADDING_PX = 12.0


def smooth_points(points: tuple[Point, ...], passes: int = 2) -> tuple[Point, ...]:
    """Apply gentle 1-2-1 weighted neighbor smoothing while preserving exact endpoints."""
    if len(points) < 3 or passes <= 0:
        return points

    current = list(points)
    for _ in range(passes):
        smoothed: list[Point] = [current[0]]
        for idx in range(1, len(current) - 1):
            prev_pt = current[idx - 1]
            curr_pt = current[idx]
            next_pt = current[idx + 1]
            smoothed.append(
                Point(
                    x=0.25 * prev_pt.x + 0.5 * curr_pt.x + 0.25 * next_pt.x,
                    y=0.25 * prev_pt.y + 0.5 * curr_pt.y + 0.25 * next_pt.y,
                )
            )
        smoothed.append(current[-1])
        current = smoothed
    return tuple(current)


def build_painter_path(points: tuple[Point, ...]) -> QPainterPath:
    """Build a smooth quadratic-Bezier QPainterPath from an immutable sequence of domain Points."""
    path = QPainterPath()
    if not points:
        return path

    first = points[0]
    path.moveTo(first.x, first.y)
    if len(points) == 1:
        path.lineTo(first.x + 0.1, first.y + 0.1)
        return path
    if len(points) == 2:
        path.lineTo(points[1].x, points[1].y)
        return path

    smoothed = smooth_points(points)
    for idx in range(1, len(smoothed) - 1):
        ctrl = smoothed[idx]
        nxt = smoothed[idx + 1]
        mid_x = (ctrl.x + nxt.x) * 0.5
        mid_y = (ctrl.y + nxt.y) * 0.5
        path.quadTo(ctrl.x, ctrl.y, mid_x, mid_y)

    last = smoothed[-1]
    path.lineTo(last.x, last.y)
    return path


class StrokeGraphicsItem(QGraphicsPathItem):
    """Scene item for a freehand stroke that becomes movable on double-click."""

    def __init__(
        self,
        stroke: StrokeObject,
        on_moved: Callable[[str, Point], None] | None = None,
    ) -> None:
        super().__init__()
        self._stroke_id = stroke.id
        self._stroke_color = stroke.color
        self._stroke_width = stroke.stroke_width
        self._on_moved = on_moved
        self._is_move_enabled = False

        self.setPath(build_painter_path(stroke.points))
        pen = QPen(
            QColor(stroke.color.value),
            stroke.stroke_width,
            Qt.PenStyle.SolidLine,
            Qt.PenCapStyle.RoundCap,
            Qt.PenJoinStyle.RoundJoin,
        )
        self.setPen(pen)
        self.setPos(stroke.position.x, stroke.position.y)
        self.setZValue(float(stroke.z_index))

    @property
    def stroke_id(self) -> str:
        """Return the domain ID of this stroke object."""
        return self._stroke_id

    @property
    def stroke_color(self) -> StrokeColor:
        """Return the StrokeColor of this stroke object."""
        return self._stroke_color

    @property
    def is_move_enabled(self) -> bool:
        """Return True if double-click move mode is currently active on this item."""
        return self._is_move_enabled

    def enable_move_mode(self) -> None:
        """Unlock this stroke object so the user can drag and reposition it."""
        scene = self.scene()
        if scene is not None:
            for item in scene.selectedItems():
                if item is not self:
                    item.setSelected(False)
        self._is_move_enabled = True
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setSelected(True)
        self.setCursor(Qt.CursorShape.SizeAllCursor)
        self.update()

    def disable_move_mode(self) -> None:
        """Lock this stroke object back into normal non-dragging state."""
        self._is_move_enabled = False
        self.setSelected(False)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)
        self.unsetCursor()
        self.update()

    def shape(self) -> QPainterPath:
        """Return a wider hit-testing path so thin freehand strokes are easy to double-click."""
        stroker = QPainterPathStroker()
        stroker.setWidth(max(HIT_TEST_PADDING_PX, self._stroke_width + 8.0))
        stroker.setCapStyle(Qt.PenCapStyle.RoundCap)
        stroker.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        return stroker.createStroke(self.path())

    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionGraphicsItem,
        widget: QWidget | None = None,
    ) -> None:
        del option, widget
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setPen(self.pen())
        painter.drawPath(self.path())

        if self._is_move_enabled:
            highlight_pen = QPen(QColor("#1E88E5"), 1.0, Qt.PenStyle.DashLine)
            painter.setPen(highlight_pen)
            painter.drawRect(self.boundingRect().adjusted(-3.0, -3.0, 3.0, 3.0))

    def mouseDoubleClickEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.enable_move_mode()
            event.accept()
            return
        super().mouseDoubleClickEvent(event)

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        if self._is_move_enabled and event.button() == Qt.MouseButton.LeftButton:
            scene = self.scene()
            if scene is not None:
                for item in scene.selectedItems():
                    if item is not self:
                        item.setSelected(False)
            super().mousePressEvent(event)
            self.setSelected(True)
            event.accept()
            return
        event.ignore()

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        if self._is_move_enabled and event.button() == Qt.MouseButton.LeftButton:
            super().mouseReleaseEvent(event)
            if self._on_moved is not None:
                pos = self.pos()
                self._on_moved(self._stroke_id, Point(float(pos.x()), float(pos.y())))
            event.accept()
            return
        super().mouseReleaseEvent(event)
