"""Full-screen frozen desktop snipping overlay for selecting a rectangular crop."""

from PySide6.QtCore import QPoint, QRect, Qt, Signal
from PySide6.QtGui import (
    QColor,
    QGuiApplication,
    QKeyEvent,
    QMouseEvent,
    QPainter,
    QPaintEvent,
    QPen,
)
from PySide6.QtWidgets import QWidget

from finecut.domain.models import BaseImage, Rect
from finecut.infrastructure.screen_capturer import base_image_to_pixmap, crop_base_image

MIN_SNIP_DIMENSION_PX = 5


class SnipOverlay(QWidget):
    """Frameless top-most screen overlay that crops a user-dragged rectangular region."""

    snip_captured = Signal(object)
    snip_cancelled = Signal()

    def __init__(
        self,
        frozen_screen: BaseImage,
        virtual_geometry: QRect | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._frozen_screen = frozen_screen
        self._frozen_pixmap = base_image_to_pixmap(frozen_screen)

        self._drag_origin: QPoint | None = None
        self._current_pos: QPoint | None = None
        self._is_dragging = False

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setCursor(Qt.CursorShape.CrossCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        target_geo = virtual_geometry or self._resolve_default_geometry()
        self.setGeometry(target_geo)

    def _resolve_default_geometry(self) -> QRect:
        screen = QGuiApplication.primaryScreen()
        if screen is not None:
            return screen.virtualGeometry()
        logical_size = self._frozen_pixmap.deviceIndependentSize()
        return QRect(0, 0, max(1, int(logical_size.width())), max(1, int(logical_size.height())))

    def selection_rect(self) -> QRect:
        """Return the current normalized selection rectangle clamped to widget bounds."""
        if self._drag_origin is None or self._current_pos is None:
            return QRect()

        x = min(self._drag_origin.x(), self._current_pos.x())
        y = min(self._drag_origin.y(), self._current_pos.y())
        width = abs(self._current_pos.x() - self._drag_origin.x())
        height = abs(self._current_pos.y() - self._drag_origin.y())
        return QRect(x, y, width, height).intersected(self.rect())

    def cancel_snip(self) -> None:
        """Cancel the current snip operation and close the overlay."""
        self._is_dragging = False
        self._drag_origin = None
        self._current_pos = None
        self.close()
        self.snip_cancelled.emit()

    def paintEvent(self, event: QPaintEvent) -> None:
        del event
        painter = QPainter(self)
        painter.drawPixmap(0, 0, self._frozen_pixmap)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 110))

        selection = self.selection_rect()
        if selection.width() > 0 and selection.height() > 0:
            dpr = self._frozen_screen.device_pixel_ratio
            src_rect = QRect(
                round(selection.x() * dpr),
                round(selection.y() * dpr),
                round(selection.width() * dpr),
                round(selection.height() * dpr),
            )
            painter.drawPixmap(selection, self._frozen_pixmap, src_rect)

            border_pen = QPen(QColor("#1E88E5"), 2)
            painter.setPen(border_pen)
            painter.drawRect(selection)

            badge_text = f"{selection.width()} x {selection.height()} px"
            badge_y = selection.top() - 8 if selection.top() > 24 else selection.top() + 18
            painter.setPen(QColor("#FFFFFF"))
            painter.drawText(selection.left() + 4, badge_y, badge_text)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.position().toPoint()
            self._drag_origin = pos
            self._current_pos = pos
            self._is_dragging = True
            self.update()
        elif event.button() == Qt.MouseButton.RightButton:
            self.cancel_snip()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._is_dragging:
            self._current_pos = event.position().toPoint()
            self.update()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self._is_dragging:
            self._current_pos = event.position().toPoint()
            self._is_dragging = False
            selection = self.selection_rect()

            if (
                selection.width() < MIN_SNIP_DIMENSION_PX
                or selection.height() < MIN_SNIP_DIMENSION_PX
            ):
                self.cancel_snip()
                return

            cropped = crop_base_image(
                self._frozen_screen,
                Rect(
                    x=selection.x(),
                    y=selection.y(),
                    width=selection.width(),
                    height=selection.height(),
                ),
            )
            self.close()
            self.snip_captured.emit(cropped)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.cancel_snip()
            return
        super().keyPressEvent(event)
