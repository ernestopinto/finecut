"""Qt-based adapters for clipboard copy and PNG/JPEG file export."""

from pathlib import Path

from PySide6.QtGui import QGuiApplication

from finecut.domain.models import BaseImage
from finecut.infrastructure.screen_capturer import base_image_to_pixmap


class QtClipboardAdapter:
    """Infrastructure adapter that copies a BaseImage onto the system clipboard."""

    def copy_image(self, image: BaseImage) -> None:
        """Decode BaseImage to QPixmap and place it on the system clipboard."""
        pixmap = base_image_to_pixmap(image)
        clipboard = QGuiApplication.clipboard()
        clipboard.setPixmap(pixmap)


class QtFileImageExporter:
    """Infrastructure adapter that writes a BaseImage to disk as PNG or JPEG."""

    def save_image(self, image: BaseImage, file_path: Path) -> None:
        """Save BaseImage to file_path in PNG or JPG format based on file suffix."""
        pixmap = base_image_to_pixmap(image)
        suffix = file_path.suffix.lower()
        image_format = "JPG" if suffix in (".jpg", ".jpeg") else "PNG"

        file_path.parent.mkdir(parents=True, exist_ok=True)
        saved = pixmap.save(str(file_path), image_format)
        if not saved:
            raise RuntimeError(f"Failed to save blueprint image to '{file_path}'.")
