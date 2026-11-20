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


def build_painter_path(points: tuple[Point, ...]) -> QPainterPath:
    """Build a QPainterPath from an immutable sequence of domain Points."""
    path = QPainterPath()
    if not points:
        return path

    first = points[0]
    path.moveTo(first.x, first.y)
    if len(points) == 1:
        path.lineTo(first.x + 0.1, first.y + 0.1)
    else:
        for pt in points[1:]:
            path.lineTo(pt.x, pt.y)
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
            super().mousePressEvent(event)
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
