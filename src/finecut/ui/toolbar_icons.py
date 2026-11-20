"""Vector-rendered QIcon factories for Finecut toolbar buttons."""

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap

_ICON_LOGICAL_SIZE = 24
_ICON_SCALE = 2
_STROKE_COLOR = QColor("#1F2937")
_ACCENT_FILL = QColor("#3B82F6")
_PAPER_FILL = QColor("#FFFFFF")


def _new_icon_canvas() -> tuple[QPixmap, QPainter]:
    pixmap = QPixmap(_ICON_LOGICAL_SIZE * _ICON_SCALE, _ICON_LOGICAL_SIZE * _ICON_SCALE)
    pixmap.setDevicePixelRatio(_ICON_SCALE)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    return pixmap, painter


def create_brush_icon() -> QIcon:
    """Render a crisp diagonal paintbrush icon for the Freehand Draw tool."""
    pixmap, painter = _new_icon_canvas()

    # Brush handle (diagonal tapered shaft from top-right to mid-left)
    handle = QPainterPath()
    handle.moveTo(18.5, 3.0)
    handle.lineTo(21.0, 5.5)
    handle.lineTo(12.2, 14.3)
    handle.lineTo(9.7, 11.8)
    handle.closeSubpath()

    painter.setPen(QPen(_STROKE_COLOR, 1.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    painter.setBrush(_ACCENT_FILL)
    painter.drawPath(handle)

    # Metal ferrule band
    painter.setPen(QPen(_STROKE_COLOR, 1.6, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    painter.drawLine(QPointF(9.4, 12.1), QPointF(11.9, 14.6))

    # Teardrop bristle tip at bottom-left
    bristles = QPainterPath()
    bristles.moveTo(9.5, 13.0)
    bristles.cubicTo(6.6, 13.2, 5.4, 15.6, 5.2, 17.6)
    bristles.cubicTo(5.0, 19.0, 3.8, 19.6, 3.0, 20.0)
    bristles.cubicTo(5.8, 21.0, 9.6, 20.4, 11.0, 17.8)
    bristles.cubicTo(11.6, 16.7, 11.6, 15.3, 11.0, 14.5)
    bristles.closeSubpath()

    painter.setBrush(_STROKE_COLOR)
    painter.drawPath(bristles)

    painter.end()
    return QIcon(pixmap)


def create_paper_sheet_icon() -> QIcon:
    """Render a crisp folded paper/sheet icon with text lines for the Text tool."""
    pixmap, painter = _new_icon_canvas()

    # Paper sheet outline with folded top-right corner
    sheet = QPainterPath()
    sheet.moveTo(5.0, 3.0)
    sheet.lineTo(14.5, 3.0)
    sheet.lineTo(19.0, 7.5)
    sheet.lineTo(19.0, 21.0)
    sheet.lineTo(5.0, 21.0)
    sheet.closeSubpath()

    outline_pen = QPen(
        _STROKE_COLOR,
        1.6,
        Qt.PenStyle.SolidLine,
        Qt.PenCapStyle.RoundCap,
        Qt.PenJoinStyle.RoundJoin,
    )
    painter.setPen(outline_pen)
    painter.setBrush(_PAPER_FILL)
    painter.drawPath(sheet)

    # Folded corner crease
    fold = QPainterPath()
    fold.moveTo(14.5, 3.0)
    fold.lineTo(14.5, 7.5)
    fold.lineTo(19.0, 7.5)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawPath(fold)

    # Horizontal text lines on the sheet
    line_pen = QPen(_STROKE_COLOR, 1.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
    painter.setPen(line_pen)
    painter.drawLine(QPointF(8.0, 11.0), QPointF(16.0, 11.0))
    painter.drawLine(QPointF(8.0, 14.5), QPointF(16.0, 14.5))
    painter.drawLine(QPointF(8.0, 18.0), QPointF(13.0, 18.0))

    painter.end()
    return QIcon(pixmap)
