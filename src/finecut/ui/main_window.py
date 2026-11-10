"""Primary application window shell for Finecut."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QLabel,
    QMainWindow,
    QPushButton,
    QToolBar,
    QVBoxLayout,
    QWidget,
)


class FinecutMainWindow(QMainWindow):
    """Minimal Recorte-inspired window shell hosting the capture toolbar and canvas area."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Finecut")
        self.setMinimumSize(540, 320)

        self.new_snip_button = QPushButton("+ Novo", self)
        self._build_toolbar()
        self._build_central_placeholder()

    def _build_toolbar(self) -> None:
        toolbar = QToolBar("Main Toolbar", self)
        toolbar.setMovable(False)
        self.new_snip_button.setToolTip("Capture a screen region to start blueprinting")
        self.new_snip_button.clicked.connect(self._on_new_snip_clicked)
        toolbar.addWidget(self.new_snip_button)
        self.addToolBar(toolbar)

    def _build_central_placeholder(self) -> None:
        container = QWidget(self)
        layout = QVBoxLayout(container)
        prompt = QLabel(
            "Click + Novo to capture a screen region and start blueprinting.",
            container,
        )
        prompt.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(prompt)
        self.setCentralWidget(container)

    def _on_new_snip_clicked(self) -> None:
        self.statusBar().showMessage("Screen capture will be implemented in FC-003.", 3000)
