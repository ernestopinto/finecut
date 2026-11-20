"""Full-screen frozen desktop snipping overlay with top floating action strip on Screen 1."""

from PySide6.QtCore import QPoint, QRect, Qt, Signal
from PySide6.QtGui import (
    QColor,
    QGuiApplication,
    QKeyEvent,
    QMouseEvent,
    QPainter,
    QPaintEvent,
    QPen,
    QResizeEvent,
)
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QWidget,
)

from finecut.domain.models import BaseImage, Rect
from finecut.infrastructure.screen_capturer import base_image_to_pixmap, crop_base_image

MIN_SNIP_DIMENSION_PX = 5
ACTION_STRIP_TOP_MARGIN_PX = 16


class SnipOverlay(QWidget):
    """Frameless top-most screen overlay that crops a user-dragged rectangular region."""

    snip_captured = Signal(object)
    snip_cancelled = Signal()

    def __init__(
        self,
        frozen_screen: BaseImage,
        virtual_geometry: QRect | None = None,
        primary_screen_geometry: QRect | None = None,
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

        self.action_strip = QFrame(self)
        self.mode_label = QLabel("Select area", self.action_strip)
        self.cancel_button = QPushButton("Cancel Selection", self.action_strip)
        self._build_action_strip()

        target_virtual_geo = virtual_geometry or self._resolve_default_virtual_geometry()
        self._primary_screen_geometry = primary_screen_geometry or (
            virtual_geometry
            if virtual_geometry is not None
            else self._resolve_default_primary_geometry(target_virtual_geo)
        )
        self.setGeometry(target_virtual_geo)
        self._position_action_strip()

    def _build_action_strip(self) -> None:
        self.action_strip.setObjectName("snipActionStrip")
        self.action_strip.setCursor(Qt.CursorShape.ArrowCursor)
        self.action_strip.setStyleSheet(
            "#snipActionStrip {"
            " background-color: #F3F4F6;"
            " border: 1px solid #D1D5DB;"
            " border-radius: 8px;"
            "}"
        )

        layout = QHBoxLayout(self.action_strip)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(10)

        self.mode_label.setStyleSheet("color: #111827; font-weight: 600;")
        layout.addWidget(self.mode_label)

        self.cancel_button.setToolTip("Cancel screen selection (Esc)")
        self.cancel_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cancel_button.setStyleSheet(
            "QPushButton {"
            " background-color: #FFFFFF;"
            " color: #111827;"
            " border: 1px solid #D1D5DB;"
            " border-radius: 5px;"
            " padding: 4px 10px;"
            "}"
            "QPushButton:hover {"
            " background-color: #FEE2E2;"
            " border-color: #EF4444;"
            " color: #991B1B;"
            "}"
        )
        self.cancel_button.clicked.connect(self.cancel_snip)
        layout.addWidget(self.cancel_button)

        self.action_strip.adjustSize()

    def _position_action_strip(self) -> None:
        """Align the floating action strip to the top-center of Screen 1 (primary screen)."""
        self.action_strip.adjustSize()
        strip_w = self.action_strip.width()

        overlay_geo = self.geometry()
        primary_geo = self._primary_screen_geometry

        local_screen_x = primary_geo.x() - overlay_geo.x()
        local_screen_y = primary_geo.y() - overlay_geo.y()
        screen_w = primary_geo.width() if primary_geo.width() > 0 else self.width()

        x = local_screen_x + max(8, (screen_w - strip_w) // 2)
        y = max(0, local_screen_y) + ACTION_STRIP_TOP_MARGIN_PX
        self.action_strip.move(x, y)
        self.action_strip.raise_()

    def _resolve_default_virtual_geometry(self) -> QRect:
        screen = QGuiApplication.primaryScreen()
        if screen is not None:
            return screen.virtualGeometry()
        logical_size = self._frozen_pixmap.deviceIndependentSize()
        return QRect(0, 0, max(1, int(logical_size.width())), max(1, int(logical_size.height())))

    @staticmethod
    def _resolve_default_primary_geometry(fallback_virtual_geo: QRect) -> QRect:
        screen = QGuiApplication.primaryScreen()
        if screen is not None:
            return screen.geometry()
        return fallback_virtual_geo

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

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self._position_action_strip()

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
