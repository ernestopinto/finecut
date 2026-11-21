"""Square color swatch picker widget and 20-color popover palette."""

from PySide6.QtCore import QPoint, QRectF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPaintEvent, QPen
from PySide6.QtWidgets import QFrame, QGridLayout, QPushButton, QWidget

from finecut.domain.models import StrokeColor

_POPOVER_COLUMNS = 10
_SELECTION_RING_COLOR = QColor("#0067C0")
_SWATCH_BORDER_COLOR = QColor("#8C8C8C")
_HOVER_RING_COLOR = QColor("#60A5FA")


class ColorSwatchButton(QPushButton):
    """Square color swatch button with subtle border and optional active selection frame."""

    def __init__(
        self,
        color: StrokeColor,
        size: int = 24,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._color = color
        self._size = size
        self.setCheckable(True)
        self.setFixedSize(QSize(size + 8, size + 8))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFlat(True)
        self.setToolTip(f"{color.display_name} ({color.value})")
        self.setAccessibleName(color.display_name)

    @property
    def color(self) -> StrokeColor:
        """Return the StrokeColor represented by this swatch button."""
        return self._color

    def paintEvent(self, event: QPaintEvent) -> None:
        """Render the square color swatch with subtle border and selection/hover frame."""
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        outer_rect = QRectF(2.0, 2.0, self.width() - 4.0, self.height() - 4.0)
        if self.isChecked():
            painter.setPen(QPen(_SELECTION_RING_COLOR, 2.0))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(outer_rect, 2.0, 2.0)
        elif self.underMouse():
            painter.setPen(QPen(_HOVER_RING_COLOR, 1.5))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(outer_rect, 2.0, 2.0)

        inset = 5.0
        swatch_rect = QRectF(inset, inset, self.width() - inset * 2.0, self.height() - inset * 2.0)
        painter.setPen(QPen(_SWATCH_BORDER_COLOR, 1.0))
        painter.setBrush(QColor(self._color.value))
        painter.drawRect(swatch_rect)
        painter.end()


class ColorSwatchPopover(QFrame):
    """Popup 2x10 square swatch grid for picking any classic palette color."""

    color_selected = Signal(object)

    def __init__(
        self,
        initial_color: StrokeColor = StrokeColor.RED,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent, Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.setObjectName("colorSwatchPopover")
        self.setStyleSheet(
            """
            QFrame#colorSwatchPopover {
                background-color: #F9F9F9;
                border: 1px solid #C8C8C8;
                border-radius: 6px;
            }
            """
        )

        self._swatch_buttons: dict[StrokeColor, ColorSwatchButton] = {}
        grid = QGridLayout(self)
        grid.setContentsMargins(10, 10, 10, 10)
        grid.setHorizontalSpacing(4)
        grid.setVerticalSpacing(4)

        for index, color in enumerate(StrokeColor):
            row = index // _POPOVER_COLUMNS
            col = index % _POPOVER_COLUMNS
            button = ColorSwatchButton(color=color, size=22, parent=self)
            button.clicked.connect(lambda checked=False, c=color: self._on_swatch_clicked(c))
            grid.addWidget(button, row, col)
            self._swatch_buttons[color] = button

        self.set_active_color(initial_color)

    @property
    def swatch_buttons(self) -> dict[StrokeColor, ColorSwatchButton]:
        """Return mapping of StrokeColor to its square ColorSwatchButton."""
        return self._swatch_buttons

    def set_active_color(self, color: StrokeColor) -> None:
        """Mark only the active color swatch as checked."""
        for swatch_color, button in self._swatch_buttons.items():
            button.setChecked(swatch_color == color)

    def _on_swatch_clicked(self, color: StrokeColor) -> None:
        self.set_active_color(color)
        self.hide()
        self.color_selected.emit(color)


class ColorSwatchPicker(QPushButton):
    """Toolbar active-color square swatch button that opens the 20-color popover on click."""

    color_selected = Signal(object)

    def __init__(
        self,
        initial_color: StrokeColor = StrokeColor.RED,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._active_color = initial_color
        self.setFixedSize(QSize(34, 34))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFlat(True)

        self._popover = ColorSwatchPopover(initial_color=initial_color, parent=self)
        self._popover.color_selected.connect(self._on_popover_color_selected)

        self.clicked.connect(self.toggle_popover)
        self._update_tooltip()

    @property
    def active_color(self) -> StrokeColor:
        """Return the currently active StrokeColor."""
        return self._active_color

    @property
    def popover(self) -> ColorSwatchPopover:
        """Return the swatch palette popover widget."""
        return self._popover

    @property
    def swatch_buttons(self) -> dict[StrokeColor, ColorSwatchButton]:
        """Return the 20 square swatch buttons inside the popover."""
        return self._popover.swatch_buttons

    def set_color(self, color: StrokeColor) -> None:
        """Update the displayed active color and synchronize the popover selection."""
        self._active_color = color
        self._popover.set_active_color(color)
        self._update_tooltip()
        self.update()

    def toggle_popover(self) -> None:
        """Show or hide the color swatch popover anchored directly beneath this button."""
        if self._popover.isVisible():
            self._popover.hide()
            return

        anchor = self.mapToGlobal(QPoint(0, self.height() + 4))
        self._popover.move(anchor)
        self._popover.show()
        self._popover.raise_()

    def paintEvent(self, event: QPaintEvent) -> None:
        """Render the square active-color indicator with a crisp outer selection frame."""
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        outer_rect = QRectF(2.0, 2.0, self.width() - 4.0, self.height() - 4.0)
        painter.setPen(QPen(_SELECTION_RING_COLOR, 2.0))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(outer_rect, 2.0, 2.0)

        inset = 5.5
        inner_rect = QRectF(inset, inset, self.width() - inset * 2.0, self.height() - inset * 2.0)
        painter.setPen(QPen(_SWATCH_BORDER_COLOR, 1.0))
        painter.setBrush(QColor(self._active_color.value))
        painter.drawRect(inner_rect)
        painter.end()

    def _on_popover_color_selected(self, color: StrokeColor) -> None:
        self.set_color(color)
        self.color_selected.emit(color)

    def _update_tooltip(self) -> None:
        self.setToolTip(
            f"Color: {self._active_color.display_name} ({self._active_color.value}) — click to pick"
        )
