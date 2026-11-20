"""QGraphicsScene hosting the immutable cropped base image and annotation objects."""

from PySide6.QtCore import QObject
from PySide6.QtWidgets import QGraphicsItem, QGraphicsPixmapItem, QGraphicsScene

from finecut.domain.models import CanvasDocument
from finecut.infrastructure.screen_capturer import base_image_to_pixmap

BASE_IMAGE_Z_VALUE = -1000.0


class BlueprintCanvasScene(QGraphicsScene):
    """Interactive graphics scene displaying the base crop and foreground objects."""

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._base_pixmap_item: QGraphicsPixmapItem | None = None

    @property
    def has_base_image(self) -> bool:
        """Return True if a base image pixmap is currently loaded in the scene."""
        return self._base_pixmap_item is not None

    @property
    def base_pixmap_item(self) -> QGraphicsPixmapItem | None:
        """Return the background QGraphicsPixmapItem if loaded."""
        return self._base_pixmap_item

    def set_document(self, document: CanvasDocument) -> None:
        """Load the document's BaseImage onto the scene background."""
        self.clear()
        pixmap = base_image_to_pixmap(document.base_image)
        item = self.addPixmap(pixmap)
        item.setZValue(BASE_IMAGE_Z_VALUE)
        item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
        item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)
        self._base_pixmap_item = item

        logical_size = pixmap.deviceIndependentSize()
        self.setSceneRect(0.0, 0.0, logical_size.width(), logical_size.height())
