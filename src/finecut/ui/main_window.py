"""Primary application window shell for Finecut."""

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from finecut.application.document_controller import DocumentController
from finecut.domain.models import BaseImage
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
        self.canvas_scene = BlueprintCanvasScene(self)
        self.canvas_view = BlueprintCanvasView(self.canvas_scene, self)
        self._central_stack = QStackedWidget(self)
        self._placeholder_widget = QWidget(self)

        self._build_toolbar()
        self._build_central_stack()
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

    def _register_shortcuts(self) -> None:
        self._new_snip_shortcut = QShortcut(QKeySequence("Ctrl+N"), self)
        self._new_snip_shortcut.activated.connect(self.start_screen_snip)

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

    def _restore_window(self) -> None:
        self.showNormal()
        self.raise_()
        self.activateWindow()
