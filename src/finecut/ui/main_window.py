"""Primary application window shell for Finecut."""

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QLabel,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from finecut.application.document_controller import DocumentController
from finecut.domain.models import BaseImage, Point, StrokeColor
from finecut.domain.ports import ScreenCapturer
from finecut.infrastructure.screen_capturer import QtScreenCapturer
from finecut.ui.canvas_scene import BlueprintCanvasScene
from finecut.ui.canvas_view import BlueprintCanvasView
from finecut.ui.snip_overlay import SnipOverlay


class FinecutMainWindow(QMainWindow):
    """Minimal Recorte-inspired window shell hosting the capture toolbar and canvas area."""

    def __init__(
        self,
        document_controller: DocumentController | None = None,
        screen_capturer: ScreenCapturer | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Finecut")
        self.setMinimumSize(540, 320)

        self._document_controller = document_controller or DocumentController()
        self._screen_capturer: ScreenCapturer = screen_capturer or QtScreenCapturer()
        self._active_overlay: SnipOverlay | None = None

        self.new_snip_button = QPushButton("+ Novo", self)
        self.red_color_button = QPushButton("Red", self)
        self.blue_color_button = QPushButton("Blue", self)
        self.black_color_button = QPushButton("Black", self)
        self._color_button_group = QButtonGroup(self)

        self.canvas_scene = BlueprintCanvasScene(self)
        self.canvas_view = BlueprintCanvasView(self.canvas_scene, self)
        self._central_stack = QStackedWidget(self)
        self._placeholder_widget = QWidget(self)

        self._build_toolbar()
        self._build_central_stack()
        self._wire_canvas_signals()
        self._register_shortcuts()

    @property
    def document_controller(self) -> DocumentController:
        """Return the window's DocumentController instance."""
        return self._document_controller

    @property
    def active_overlay(self) -> SnipOverlay | None:
        """Return the currently open SnipOverlay if a snip is in progress."""
        return self._active_overlay

    @property
    def is_showing_canvas(self) -> bool:
        """Return True when the central stack is displaying the BlueprintCanvasView."""
        return self._central_stack.currentWidget() is self.canvas_view

    def _build_toolbar(self) -> None:
        toolbar = QToolBar("Main Toolbar", self)
        toolbar.setMovable(False)

        self.new_snip_button.setToolTip("Capture a screen region to start blueprinting (Ctrl+N)")
        self.new_snip_button.clicked.connect(self.start_screen_snip)
        toolbar.addWidget(self.new_snip_button)
        toolbar.addSeparator()

        self._color_button_group.setExclusive(True)
        color_buttons: tuple[tuple[QPushButton, StrokeColor, str], ...] = (
            (self.red_color_button, StrokeColor.RED, "Draw in Red (#E53935)"),
            (self.blue_color_button, StrokeColor.BLUE, "Draw in Blue (#1E88E5)"),
            (self.black_color_button, StrokeColor.BLACK, "Draw in Black (#000000)"),
        )
        for button, color, tooltip in color_buttons:
            button.setCheckable(True)
            button.setToolTip(tooltip)
            self._color_button_group.addButton(button)
            toolbar.addWidget(button)
            button.clicked.connect(lambda checked=False, c=color: self.set_stroke_color(c))

        self.red_color_button.setChecked(True)
        self.addToolBar(toolbar)

    def _build_central_stack(self) -> None:
        layout = QVBoxLayout(self._placeholder_widget)
        prompt = QLabel(
            "Click + Novo (or press Ctrl+N) to capture a screen region and start blueprinting.",
            self._placeholder_widget,
        )
        prompt.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(prompt)

        self._central_stack.addWidget(self._placeholder_widget)
        self._central_stack.addWidget(self.canvas_view)
        self._central_stack.setCurrentWidget(self._placeholder_widget)
        self.setCentralWidget(self._central_stack)

    def _wire_canvas_signals(self) -> None:
        self.canvas_scene.stroke_completed.connect(self._on_stroke_completed)
        self.canvas_scene.object_moved.connect(self._on_object_moved)

    def _register_shortcuts(self) -> None:
        self._new_snip_shortcut = QShortcut(QKeySequence("Ctrl+N"), self)
        self._new_snip_shortcut.activated.connect(self.start_screen_snip)

    def set_stroke_color(self, color: StrokeColor) -> None:
        """Switch the active freehand drawing color across controller, scene, and toolbar."""
        self._document_controller.set_active_color(color)
        self.canvas_scene.set_active_color(color)

        button_by_color = {
            StrokeColor.RED: self.red_color_button,
            StrokeColor.BLUE: self.blue_color_button,
            StrokeColor.BLACK: self.black_color_button,
        }
        target_button = button_by_color[color]
        if not target_button.isChecked():
            target_button.setChecked(True)

    def start_screen_snip(self) -> None:
        """Hide the main window, freeze the screen, and launch the SnipOverlay."""
        self.hide()
        QApplication.processEvents()

        frozen_screen = self._screen_capturer.capture_full_screen()
        overlay = SnipOverlay(frozen_screen)
        overlay.snip_captured.connect(self._on_snip_captured)
        overlay.snip_cancelled.connect(self._on_snip_cancelled)
        self._active_overlay = overlay
        overlay.show()
        overlay.raise_()
        overlay.activateWindow()

    def _on_snip_captured(self, base_image: BaseImage) -> None:
        self._active_overlay = None
        document = self._document_controller.start_new_document(base_image)
        self.canvas_scene.set_document(document)
        self._central_stack.setCurrentWidget(self.canvas_view)

        self._restore_window()
        self.statusBar().showMessage(
            f"Captured crop: {base_image.width} x {base_image.height} px",
            4000,
        )

    def _on_snip_cancelled(self) -> None:
        self._active_overlay = None
        self._restore_window()
        self.statusBar().showMessage("Screen capture cancelled.", 3000)

    def _on_stroke_completed(self, points: tuple[Point, ...]) -> None:
        if not self._document_controller.has_document:
            return
        stroke = self._document_controller.add_stroke(points)
        self.canvas_scene.add_stroke_item(stroke)

    def _on_object_moved(self, object_id: str, new_position: Point) -> None:
        if not self._document_controller.has_document:
            return
        self._document_controller.move_object(object_id, new_position)

    def _restore_window(self) -> None:
        self.showNormal()
        self.raise_()
        self.activateWindow()
