"""QGraphicsView viewport displaying the BlueprintCanvasScene."""

from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QColor, QPainter, QResizeEvent
from PySide6.QtWidgets import QGraphicsView, QWidget

from finecut.ui.canvas_scene import BlueprintCanvasScene


class BlueprintCanvasView(QGraphicsView):
    """Viewport for viewing and annotating the captured screen blueprint without scrollbars."""

    def __init__(self, scene: BlueprintCanvasScene, parent: QWidget | None = None) -> None:
        super().__init__(scene, parent)
        self.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setBackgroundBrush(QBrush(QColor("#F3F4F6")))
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

    def fit_canvas_to_viewport(self) -> None:
        """Display the scene at 1:1 when it fits, or scale down cleanly to prevent scrolling."""
        scene = self.scene()
        if scene is None:
            return
        scene_rect = scene.sceneRect()
        if scene_rect.isEmpty():
            return

        self.resetTransform()
        viewport_size = self.viewport().size()
        if (
            scene_rect.width() > viewport_size.width()
            or scene_rect.height() > viewport_size.height()
        ):
            self.fitInView(scene_rect, Qt.AspectRatioMode.KeepAspectRatio)

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self.fit_canvas_to_viewport()
