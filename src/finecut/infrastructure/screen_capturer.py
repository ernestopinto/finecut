"""Qt-based screen capture adapter and BaseImage <-> QPixmap boundary conversions."""

from PySide6.QtCore import QBuffer, QByteArray, QIODevice, QRect, Qt
from PySide6.QtGui import QGuiApplication, QPixmap

from finecut.domain.models import BaseImage, Rect


def pixmap_to_base_image(pixmap: QPixmap) -> BaseImage:
    """Encode a QPixmap into an immutable domain BaseImage."""
    if pixmap.isNull() or pixmap.width() <= 0 or pixmap.height() <= 0:
        raise ValueError("Cannot convert a null or empty QPixmap to BaseImage.")

    byte_array = QByteArray()
    buffer = QBuffer(byte_array)
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    saved = pixmap.save(buffer, "PNG")
    buffer.close()

    if not saved or byte_array.isEmpty():
        raise RuntimeError("Failed to encode QPixmap as PNG bytes.")

    dpr = float(pixmap.devicePixelRatio()) if pixmap.devicePixelRatio() > 0 else 1.0
    return BaseImage(
        width=pixmap.width(),
        height=pixmap.height(),
        png_bytes=bytes(byte_array.data()),
        device_pixel_ratio=dpr,
    )


def base_image_to_pixmap(base_image: BaseImage) -> QPixmap:
    """Decode a domain BaseImage into a HiDPI-aware QPixmap."""
    pixmap = QPixmap()
    loaded = pixmap.loadFromData(base_image.png_bytes, "PNG")
    if not loaded or pixmap.isNull():
        raise ValueError("Failed to decode BaseImage png_bytes into QPixmap.")
    pixmap.setDevicePixelRatio(base_image.device_pixel_ratio)
    return pixmap


def crop_base_image(source: BaseImage, selection_rect: Rect) -> BaseImage:
    """Crop a logical selection rectangle from a source BaseImage respecting HiDPI scaling."""
    pixmap = base_image_to_pixmap(source)
    dpr = source.device_pixel_ratio

    px_x = max(0, round(selection_rect.x * dpr))
    px_y = max(0, round(selection_rect.y * dpr))
    px_w = max(1, round(selection_rect.width * dpr))
    px_h = max(1, round(selection_rect.height * dpr))

    bounded = QRect(px_x, px_y, px_w, px_h).intersected(
        QRect(0, 0, pixmap.width(), pixmap.height())
    )
    if bounded.isEmpty() or bounded.width() <= 0 or bounded.height() <= 0:
        raise ValueError("Selection rectangle is outside the source image bounds.")

    cropped = pixmap.copy(bounded)
    cropped.setDevicePixelRatio(dpr)
    return pixmap_to_base_image(cropped)


class QtScreenCapturer:
    """Infrastructure adapter capturing the Windows virtual desktop via PySide6 QScreen."""

    def capture_full_screen(self) -> BaseImage:
        """Capture the full virtual desktop across connected displays."""
        screen = QGuiApplication.primaryScreen()
        if screen is None:
            raise RuntimeError("No active display screen available for capture.")

        virtual_geo = screen.virtualGeometry()
        pixmap = screen.grabWindow(
            0,
            virtual_geo.x(),
            virtual_geo.y(),
            virtual_geo.width(),
            virtual_geo.height(),
        )
        if pixmap.isNull():
            fallback_w = max(1, virtual_geo.width())
            fallback_h = max(1, virtual_geo.height())
            pixmap = QPixmap(fallback_w, fallback_h)
            pixmap.fill(Qt.GlobalColor.white)

        return pixmap_to_base_image(pixmap)

    def capture_region(self, region: Rect) -> BaseImage:
        """Capture a specific rectangular screen region."""
        full_screen = self.capture_full_screen()
        return crop_base_image(full_screen, region)
