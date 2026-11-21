"""Vector-rendered QIcon factories for Finecut toolbar buttons."""

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap

_ICON_LOGICAL_SIZE = 24
_ICON_SCALE = 2
_STROKE_COLOR = QColor("#1F2937")
_ACCENT_FILL = QColor("#3B82F6")
_PAPER_FILL = QColor("#FFFFFF")
_SOFT_SURFACE_FILL = QColor("#E5E7EB")
_FLOPPY_BODY_FILL = QColor("#4B5563")


def _new_icon_canvas() -> tuple[QPixmap, QPainter]:
    pixmap = QPixmap(_ICON_LOGICAL_SIZE * _ICON_SCALE, _ICON_LOGICAL_SIZE * _ICON_SCALE)
    pixmap.setDevicePixelRatio(_ICON_SCALE)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    return pixmap, painter


def _round_pen(color: QColor, width: float = 1.6) -> QPen:
    return QPen(
        color,
        width,
        Qt.PenStyle.SolidLine,
        Qt.PenCapStyle.RoundCap,
        Qt.PenJoinStyle.RoundJoin,
    )


def create_new_icon() -> QIcon:
    """Render a crisp dashed rectangular marquee icon for New Snip."""
    pixmap, painter = _new_icon_canvas()

    pen = QPen(
        _STROKE_COLOR,
        1.8,
        Qt.PenStyle.SolidLine,
        Qt.PenCapStyle.SquareCap,
        Qt.PenJoinStyle.MiterJoin,
    )
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)

    left, top, right, bottom = 4.0, 4.0, 20.0, 20.0
    corner = 2.6

    # Four L-shaped corners
    corners = (
        (QPointF(left, top + corner), QPointF(left, top), QPointF(left + corner, top)),
        (QPointF(right - corner, top), QPointF(right, top), QPointF(right, top + corner)),
        (QPointF(right, bottom - corner), QPointF(right, bottom), QPointF(right - corner, bottom)),
        (QPointF(left + corner, bottom), QPointF(left, bottom), QPointF(left, bottom - corner)),
    )
    for p1, p2, p3 in corners:
        path = QPainterPath()
        path.moveTo(p1)
        path.lineTo(p2)
        path.lineTo(p3)
        painter.drawPath(path)

    # Two evenly spaced dashes along each of the four sides
    for d1, d2 in ((9.2, 10.8), (13.2, 14.8)):
        painter.drawLine(QPointF(d1, top), QPointF(d2, top))
        painter.drawLine(QPointF(d1, bottom), QPointF(d2, bottom))
        painter.drawLine(QPointF(left, d1), QPointF(left, d2))
        painter.drawLine(QPointF(right, d1), QPointF(right, d2))

    painter.end()
    return QIcon(pixmap)


def create_brush_icon() -> QIcon:
    """Render a crisp diagonal paintbrush icon for the Freehand Draw tool."""
    pixmap, painter = _new_icon_canvas()

    handle = QPainterPath()
    handle.moveTo(18.5, 3.0)
    handle.lineTo(21.0, 5.5)
    handle.lineTo(12.2, 14.3)
    handle.lineTo(9.7, 11.8)
    handle.closeSubpath()

    painter.setPen(_round_pen(_STROKE_COLOR, 1.5))
    painter.setBrush(_ACCENT_FILL)
    painter.drawPath(handle)

    painter.setPen(_round_pen(_STROKE_COLOR, 1.6))
    painter.drawLine(QPointF(9.4, 12.1), QPointF(11.9, 14.6))

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

    sheet = QPainterPath()
    sheet.moveTo(5.0, 3.0)
    sheet.lineTo(14.5, 3.0)
    sheet.lineTo(19.0, 7.5)
    sheet.lineTo(19.0, 21.0)
    sheet.lineTo(5.0, 21.0)
    sheet.closeSubpath()

    painter.setPen(_round_pen(_STROKE_COLOR, 1.6))
    painter.setBrush(_PAPER_FILL)
    painter.drawPath(sheet)

    fold = QPainterPath()
    fold.moveTo(14.5, 3.0)
    fold.lineTo(14.5, 7.5)
    fold.lineTo(19.0, 7.5)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawPath(fold)

    painter.setPen(_round_pen(_STROKE_COLOR, 1.5))
    painter.drawLine(QPointF(8.0, 11.0), QPointF(16.0, 11.0))
    painter.drawLine(QPointF(8.0, 14.5), QPointF(16.0, 14.5))
    painter.drawLine(QPointF(8.0, 18.0), QPointF(13.0, 18.0))

    painter.end()
    return QIcon(pixmap)


def create_undo_icon() -> QIcon:
    """Render a classic curved counter-clockwise Undo arrow."""
    pixmap, painter = _new_icon_canvas()

    arc = QPainterPath()
    arc.moveTo(6.0, 9.5)
    arc.lineTo(13.5, 9.5)
    arc.cubicTo(18.5, 9.5, 19.5, 13.5, 18.5, 16.5)
    arc.cubicTo(17.7, 18.8, 15.2, 19.5, 11.5, 19.5)

    painter.setPen(_round_pen(_STROKE_COLOR, 2.2))
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawPath(arc)

    head = QPainterPath()
    head.moveTo(9.5, 5.5)
    head.lineTo(5.0, 9.5)
    head.lineTo(9.5, 13.5)
    painter.drawPath(head)

    painter.end()
    return QIcon(pixmap)


def create_redo_icon() -> QIcon:
    """Render a classic curved clockwise Redo arrow."""
    pixmap, painter = _new_icon_canvas()

    arc = QPainterPath()
    arc.moveTo(18.0, 9.5)
    arc.lineTo(10.5, 9.5)
    arc.cubicTo(5.5, 9.5, 4.5, 13.5, 5.5, 16.5)
    arc.cubicTo(6.3, 18.8, 8.8, 19.5, 12.5, 19.5)

    painter.setPen(_round_pen(_STROKE_COLOR, 2.2))
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawPath(arc)

    head = QPainterPath()
    head.moveTo(14.5, 5.5)
    head.lineTo(19.0, 9.5)
    head.lineTo(14.5, 13.5)
    painter.drawPath(head)

    painter.end()
    return QIcon(pixmap)


def create_delete_icon() -> QIcon:
    """Render a classic Trash Can icon for deleting selected objects."""
    pixmap, painter = _new_icon_canvas()

    painter.setPen(_round_pen(_STROKE_COLOR, 1.6))

    # Top handle and lid bar
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawRoundedRect(QRectF(9.0, 3.2, 6.0, 2.6), 1.0, 1.0)
    painter.drawLine(QPointF(4.5, 6.2), QPointF(19.5, 6.2))

    # Tapered bin body
    bin_body = QPainterPath()
    bin_body.moveTo(6.2, 6.5)
    bin_body.lineTo(7.4, 20.2)
    bin_body.lineTo(16.6, 20.2)
    bin_body.lineTo(17.8, 6.5)
    bin_body.closeSubpath()

    painter.setBrush(_PAPER_FILL)
    painter.drawPath(bin_body)

    # Vertical bin ribs
    painter.setPen(_round_pen(_STROKE_COLOR, 1.3))
    painter.drawLine(QPointF(10.0, 9.5), QPointF(10.3, 17.2))
    painter.drawLine(QPointF(14.0, 9.5), QPointF(13.7, 17.2))

    painter.end()
    return QIcon(pixmap)


def create_copy_icon() -> QIcon:
    """Render a classic overlapping two-page Copy icon."""
    pixmap, painter = _new_icon_canvas()

    painter.setPen(_round_pen(_STROKE_COLOR, 1.5))

    # Back sheet
    painter.setBrush(_SOFT_SURFACE_FILL)
    painter.drawRoundedRect(QRectF(4.2, 3.5, 10.8, 13.5), 1.4, 1.4)

    # Front sheet
    painter.setBrush(_PAPER_FILL)
    painter.drawRoundedRect(QRectF(8.8, 7.0, 10.8, 13.5), 1.4, 1.4)

    # Subtle lines on front sheet
    painter.setPen(_round_pen(_ACCENT_FILL, 1.3))
    painter.drawLine(QPointF(11.2, 11.2), QPointF(17.2, 11.2))
    painter.drawLine(QPointF(11.2, 14.2), QPointF(17.2, 14.2))
    painter.drawLine(QPointF(11.2, 17.2), QPointF(15.2, 17.2))

    painter.end()
    return QIcon(pixmap)


def create_save_icon() -> QIcon:
    """Render a classic Floppy Disk icon for Save."""
    pixmap, painter = _new_icon_canvas()

    # Outer floppy body with chamfered top-right corner
    body = QPainterPath()
    body.moveTo(4.0, 3.5)
    body.lineTo(16.5, 3.5)
    body.lineTo(20.0, 7.0)
    body.lineTo(20.0, 20.0)
    body.lineTo(4.0, 20.0)
    body.closeSubpath()

    painter.setPen(_round_pen(_STROKE_COLOR, 1.5))
    painter.setBrush(_FLOPPY_BODY_FILL)
    painter.drawPath(body)

    # Top metal shutter
    painter.setPen(_round_pen(_STROKE_COLOR, 1.1))
    painter.setBrush(_SOFT_SURFACE_FILL)
    painter.drawRect(QRectF(7.2, 3.6, 8.6, 5.4))

    # Shutter notch
    painter.setBrush(_FLOPPY_BODY_FILL)
    painter.drawRect(QRectF(12.8, 4.6, 1.9, 3.4))

    # Bottom white label area
    painter.setBrush(_PAPER_FILL)
    painter.drawRect(QRectF(6.8, 12.2, 10.4, 7.7))

    painter.setPen(_round_pen(_STROKE_COLOR, 1.1))
    painter.drawLine(QPointF(8.6, 15.0), QPointF(15.4, 15.0))
    painter.drawLine(QPointF(8.6, 17.4), QPointF(13.8, 17.4))

    painter.end()
    return QIcon(pixmap)
