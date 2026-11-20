"""Primary application window shell for Finecut."""

from pathlib import Path

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QComboBox,
    QFileDialog,
    QLabel,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from finecut.application.document_controller import DocumentController
from finecut.domain.models import (
    BaseImage,
    CanvasDocument,
    CanvasTool,
    FontFamily,
    Point,
    StrokeColor,
)
from finecut.domain.ports import ClipboardPort, ImageExporter, ScreenCapturer
from finecut.infrastructure.export_adapters import QtClipboardAdapter, QtFileImageExporter
from finecut.infrastructure.screen_capturer import QtScreenCapturer
from finecut.ui.canvas_scene import BlueprintCanvasScene
from finecut.ui.canvas_view import BlueprintCanvasView
from finecut.ui.color_swatch_picker import ColorSwatchPicker
from finecut.ui.snip_overlay import SnipOverlay
from finecut.ui.toolbar_icons import create_brush_icon, create_paper_sheet_icon


class FinecutMainWindow(QMainWindow):
    """Minimal Recorte-inspired window shell hosting the capture toolbar and canvas area."""

    def __init__(
        self,
        document_controller: DocumentController | None = None,
        screen_capturer: ScreenCapturer | None = None,
        clipboard_port: ClipboardPort | None = None,
        image_exporter: ImageExporter | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Finecut")
        self.setMinimumSize(780, 420)

        self._document_controller = document_controller or DocumentController()
        self._screen_capturer: ScreenCapturer = screen_capturer or QtScreenCapturer()
        self._clipboard_port: ClipboardPort = clipboard_port or QtClipboardAdapter()
        self._image_exporter: ImageExporter = image_exporter or QtFileImageExporter()
        self._active_overlay: SnipOverlay | None = None

        self.new_snip_button = QPushButton("+ Novo", self)
        self.draw_tool_button = QPushButton(self)
        self.text_tool_button = QPushButton(self)
        self._tool_button_group = QButtonGroup(self)

        self.color_swatch_picker = ColorSwatchPicker(
            initial_color=self._document_controller.active_color,
            parent=self,
        )

        self.font_combo_box = QComboBox(self)
        self.undo_button = QPushButton("Undo", self)
        self.redo_button = QPushButton("Redo", self)
        self.delete_button = QPushButton("Delete", self)
        self.copy_button = QPushButton("Copy", self)
        self.save_button = QPushButton("Save", self)

        self.canvas_scene = BlueprintCanvasScene(self)
        self.canvas_view = BlueprintCanvasView(self.canvas_scene, self)
        self._central_stack = QStackedWidget(self)
        self._placeholder_widget = QWidget(self)

        self._build_toolbar()
        self._build_central_stack()
        self._wire_canvas_signals()
        self._register_shortcuts()
        self._sync_history_buttons()

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

        self._tool_button_group.setExclusive(True)
        tool_buttons: tuple[tuple[QPushButton, CanvasTool, QIcon, str, str], ...] = (
            (
                self.draw_tool_button,
                CanvasTool.DRAW,
                create_brush_icon(),
                "Draw",
                "Freehand Draw tool",
            ),
            (
                self.text_tool_button,
                CanvasTool.TEXT,
                create_paper_sheet_icon(),
                "Text",
                "Text tool (double-click image to add text, click outside or Enter to save)",
            ),
        )
        for button, tool, icon, accessible_name, tooltip in tool_buttons:
            button.setCheckable(True)
            button.setIcon(icon)
            button.setIconSize(QSize(20, 20))
            button.setFixedSize(QSize(34, 34))
            button.setAccessibleName(accessible_name)
            button.setToolTip(tooltip)
            self._tool_button_group.addButton(button)
            toolbar.addWidget(button)
            button.clicked.connect(lambda checked=False, t=tool: self.set_active_tool(t))

        self.draw_tool_button.setChecked(True)
        toolbar.addSeparator()

        self.color_swatch_picker.color_selected.connect(self.set_stroke_color)
        toolbar.addWidget(self.color_swatch_picker)
        toolbar.addSeparator()

        self.font_combo_box.setToolTip("Select text font family")
        for font_family in FontFamily:
            self.font_combo_box.addItem(font_family.value)
        self.font_combo_box.currentTextChanged.connect(self._on_font_combo_text_changed)
        toolbar.addWidget(self.font_combo_box)
        toolbar.addSeparator()

        self.undo_button.setToolTip("Undo last action (Ctrl+Z)")
        self.undo_button.clicked.connect(self.undo_action)
        toolbar.addWidget(self.undo_button)

        self.redo_button.setToolTip("Redo action (Ctrl+Y)")
        self.redo_button.clicked.connect(self.redo_action)
        toolbar.addWidget(self.redo_button)

        self.delete_button.setToolTip("Delete selected drawing or text object (Del)")
        self.delete_button.clicked.connect(self.delete_selected_objects)
        toolbar.addWidget(self.delete_button)
        toolbar.addSeparator()

        self.copy_button.setToolTip("Copy flattened blueprint to clipboard (Ctrl+C)")
        self.copy_button.clicked.connect(self.copy_blueprint_to_clipboard)
        toolbar.addWidget(self.copy_button)

        self.save_button.setToolTip("Save flattened blueprint to file (Ctrl+S)")
        self.save_button.clicked.connect(lambda checked=False: self.save_blueprint_to_file())
        toolbar.addWidget(self.save_button)

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
        self.canvas_scene.text_committed.connect(self._on_text_committed)
        self.canvas_scene.object_moved.connect(self._on_object_moved)

    def _register_shortcuts(self) -> None:
        self._new_snip_shortcut = QShortcut(QKeySequence("Ctrl+N"), self)
        self._new_snip_shortcut.activated.connect(self.start_screen_snip)

        self._undo_shortcut = QShortcut(QKeySequence("Ctrl+Z"), self)
        self._undo_shortcut.activated.connect(self.undo_action)

        self._redo_shortcut = QShortcut(QKeySequence("Ctrl+Y"), self)
        self._redo_shortcut.activated.connect(self.redo_action)

        self._delete_shortcut = QShortcut(QKeySequence("Del"), self)
        self._delete_shortcut.activated.connect(self.delete_selected_objects)

        self._escape_shortcut = QShortcut(QKeySequence("Esc"), self)
        self._escape_shortcut.activated.connect(self.canvas_scene.clear_active_interaction)

        self._copy_shortcut = QShortcut(QKeySequence("Ctrl+C"), self)
        self._copy_shortcut.activated.connect(self.copy_blueprint_to_clipboard)

        self._save_shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        self._save_shortcut.activated.connect(lambda: self.save_blueprint_to_file())

    def _sync_history_buttons(self) -> None:
        self.undo_button.setEnabled(self._document_controller.can_undo)
        self.redo_button.setEnabled(self._document_controller.can_redo)

    def set_active_tool(self, tool: CanvasTool) -> None:
        """Switch the active canvas tool between Draw and Text across controller, scene, and UI."""
        self._document_controller.set_active_tool(tool)
        self.canvas_scene.set_active_tool(tool)

        button_by_tool = {
            CanvasTool.DRAW: self.draw_tool_button,
            CanvasTool.TEXT: self.text_tool_button,
        }
        target_button = button_by_tool[tool]
        if not target_button.isChecked():
            target_button.setChecked(True)

    def set_stroke_color(self, color: StrokeColor) -> None:
        """Switch the active drawing/text color across controller, scene, and swatch picker."""
        self._document_controller.set_active_color(color)
        self.canvas_scene.set_active_color(color)
        if self.color_swatch_picker.active_color != color:
            self.color_swatch_picker.set_color(color)

    def set_font_family(self, font: FontFamily) -> None:
        """Switch the active text font family across controller, scene, and toolbar."""
        self._document_controller.set_active_font(font)
        self.canvas_scene.set_active_font(font)

        idx = self.font_combo_box.findText(font.value)
        if idx >= 0 and self.font_combo_box.currentIndex() != idx:
            self.font_combo_box.setCurrentIndex(idx)

    def _on_font_combo_text_changed(self, text: str) -> None:
        for font_family in FontFamily:
            if font_family.value == text:
                self.set_font_family(font_family)
                return

    def undo_action(self) -> bool:
        """Undo the last annotation action and refresh the canvas scene."""
        if self.canvas_scene.draft_text_item is not None:
            self.canvas_scene.draft_text_item.cancel()

        doc = self._document_controller.undo()
        self._sync_history_buttons()
        if doc is None:
            return False

        self.canvas_scene.set_document(doc)
        self.statusBar().showMessage("Undid last action.", 2500)
        return True

    def redo_action(self) -> bool:
        """Redo the most recently undone annotation action and refresh the canvas scene."""
        if self.canvas_scene.draft_text_item is not None:
            self.canvas_scene.draft_text_item.cancel()

        doc = self._document_controller.redo()
        self._sync_history_buttons()
        if doc is None:
            return False

        self.canvas_scene.set_document(doc)
        self.statusBar().showMessage("Redid action.", 2500)
        return True

    def delete_selected_objects(self) -> int:
        """Delete currently selected stroke or text objects from the document and scene."""
        if not self._document_controller.has_document:
            return 0
        if self.canvas_scene.draft_text_item is not None:
            return 0

        selected_ids = self.canvas_scene.selected_object_ids()
        if not selected_ids:
            self.statusBar().showMessage(
                "Select a drawing (double-click) or text object to delete.",
                3000,
            )
            return 0

        updated_doc: CanvasDocument | None = None
        for obj_id in selected_ids:
            updated_doc = self._document_controller.remove_object(obj_id)

        if updated_doc is not None:
            self.canvas_scene.set_document(updated_doc)

        self._sync_history_buttons()
        self.statusBar().showMessage(f"Deleted {len(selected_ids)} object(s).", 2500)
        return len(selected_ids)

    def copy_blueprint_to_clipboard(self) -> bool:
        """Flatten the active blueprint canvas and copy it onto the system clipboard."""
        if not self._document_controller.has_document or not self.canvas_scene.has_base_image:
            self.statusBar().showMessage("Capture a screen crop before copying.", 3000)
            return False

        flattened = self.canvas_scene.render_flattened_image()
        self._clipboard_port.copy_image(flattened)
        self.statusBar().showMessage("Copied blueprint to clipboard.", 3000)
        return True

    def save_blueprint_to_file(self, target_path: Path | None = None) -> Path | None:
        """Flatten the active blueprint canvas and save it as a PNG or JPEG file."""
        if not self._document_controller.has_document or not self.canvas_scene.has_base_image:
            self.statusBar().showMessage("Capture a screen crop before saving.", 3000)
            return None

        resolved_path = target_path
        if resolved_path is None:
            selected_file, _ = QFileDialog.getSaveFileName(
                self,
                "Save Blueprint",
                "blueprint.png",
                "PNG Image (*.png);;JPEG Image (*.jpg *.jpeg)",
            )
            if not selected_file:
                return None
            resolved_path = Path(selected_file)

        flattened = self.canvas_scene.render_flattened_image()
        self._image_exporter.save_image(flattened, resolved_path)
        self.statusBar().showMessage(f"Saved blueprint to {resolved_path.name}", 4000)
        return resolved_path

    def start_screen_snip(self) -> None:
        """Completely hide the main window, freeze the screen, and launch the SnipOverlay."""
        self.setWindowOpacity(0.0)
        self.showMinimized()
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
        self._sync_history_buttons()

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
        self._sync_history_buttons()

    def _on_text_committed(self, text: str, position: Point) -> None:
        if not self._document_controller.has_document:
            return
        text_obj = self._document_controller.add_text(text=text, position=position)
        self.canvas_scene.add_text_item(text_obj)
        self._sync_history_buttons()

    def _on_object_moved(self, object_id: str, new_position: Point) -> None:
        if not self._document_controller.has_document:
            return
        self._document_controller.move_object(object_id, new_position)
        self._sync_history_buttons()

    def _restore_window(self) -> None:
        self.setWindowOpacity(1.0)
        self.showNormal()
        self.raise_()
        self.activateWindow()
