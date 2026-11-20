"""Interactive QGraphicsTextItem classes for inline text entry and movable text objects."""

from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QKeyEvent
from PySide6.QtWidgets import (
    QGraphicsItem,
    QGraphicsSceneMouseEvent,
    QGraphicsTextItem,
)

from finecut.domain.models import FontFamily, Point, StrokeColor, TextObject


def resolve_qfont(font_family: FontFamily, font_size: int) -> QFont:
    """Resolve a domain FontFamily into a crisp Windows QFont."""
    font = QFont(font_family.value, font_size)
    if font_family == FontFamily.COURIER:
        font.setFamilies(["Courier New", "Courier"])
    return font


class TextGraphicsItem(QGraphicsTextItem):
    """Committed text annotation object that can be freely moved after creation with Enter."""

    def __init__(
        self,
        text_obj: TextObject,
        on_moved: Callable[[str, Point], None] | None = None,
    ) -> None:
        super().__init__(text_obj.text)
        self._text_id = text_obj.id
        self._font_family = text_obj.font_family
        self._text_color = text_obj.color
        self._font_size = text_obj.font_size
        self._on_moved = on_moved

        self.setFont(resolve_qfont(text_obj.font_family, text_obj.font_size))
        self.setDefaultTextColor(QColor(text_obj.color.value))
        self.setPos(text_obj.position.x, text_obj.position.y)
        self.setZValue(float(text_obj.z_index))

        self.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setCursor(Qt.CursorShape.SizeAllCursor)

    @property
    def text_id(self) -> str:
        """Return the domain ID of this text object."""
        return self._text_id

    @property
    def font_family(self) -> FontFamily:
        """Return the FontFamily of this text object."""
        return self._font_family

    @property
    def text_color(self) -> StrokeColor:
        """Return the StrokeColor of this text object."""
        return self._text_color

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            scene = self.scene()
            if scene is not None:
                for item in scene.selectedItems():
                    if item is not self:
                        item.setSelected(False)
        super().mousePressEvent(event)
        if event.button() == Qt.MouseButton.LeftButton:
            self.setSelected(True)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        super().mouseReleaseEvent(event)
        if event.button() == Qt.MouseButton.LeftButton and self._on_moved is not None:
            pos = self.pos()
            self._on_moved(self._text_id, Point(float(pos.x()), float(pos.y())))


class DraftTextGraphicsItem(QGraphicsTextItem):
    """Inline canvas text editor that commits on Enter and cancels on Escape."""

    def __init__(
        self,
        position: Point,
        font_family: FontFamily,
        color: StrokeColor,
        font_size: int = 16,
        on_committed: Callable[[str, Point], None] | None = None,
        on_cancelled: Callable[[], None] | None = None,
    ) -> None:
        super().__init__()
        self._font_family = font_family
        self._text_color = color
        self._font_size = font_size
        self._on_committed = on_committed
        self._on_cancelled = on_cancelled
        self._is_finalized = False

        self.setPos(position.x, position.y)
        self.setZValue(10000.0)
        self.setFont(resolve_qfont(font_family, font_size))
        self.setDefaultTextColor(QColor(color.value))
        self.setTextInteractionFlags(Qt.TextInteractionFlag.TextEditorInteraction)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsFocusable, True)

    @property
    def font_family(self) -> FontFamily:
        """Return the active FontFamily on this draft editor."""
        return self._font_family

    def set_font_family(self, font_family: FontFamily) -> None:
        """Update the font family while typing."""
        self._font_family = font_family
        self.setFont(resolve_qfont(font_family, self._font_size))
        self.update()

    def set_text_color(self, color: StrokeColor) -> None:
        """Update the text color while typing."""
        self._text_color = color
        self.setDefaultTextColor(QColor(color.value))
        self.update()

    def commit_or_cancel(self) -> None:
        """Commit non-empty text via on_committed or cancel if blank."""
        if self._is_finalized:
            return
        self._is_finalized = True
        content = self.toPlainText().strip()
        pos = self.pos()
        if content and self._on_committed is not None:
            self._on_committed(content, Point(float(pos.x()), float(pos.y())))
        elif self._on_cancelled is not None:
            self._on_cancelled()

    def cancel(self) -> None:
        """Cancel and discard this draft text editor."""
        if self._is_finalized:
            return
        self._is_finalized = True
        if self._on_cancelled is not None:
            self._on_cancelled()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.commit_or_cancel()
            event.accept()
            return
        if event.key() == Qt.Key.Key_Escape:
            self.cancel()
            event.accept()
            return
        super().keyPressEvent(event)
