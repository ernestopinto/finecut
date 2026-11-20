"""Composition root and desktop entry point for Finecut."""

import sys
from collections.abc import Sequence

from PySide6.QtWidgets import QApplication

from finecut.application.document_controller import DocumentController
from finecut.infrastructure.screen_capturer import QtScreenCapturer
from finecut.ui.main_window import FinecutMainWindow


def create_main_window() -> FinecutMainWindow:
    """Instantiate the main window with wired application dependencies."""
    controller = DocumentController()
    capturer = QtScreenCapturer()
    return FinecutMainWindow(
        document_controller=controller,
        screen_capturer=capturer,
    )


def main(argv: Sequence[str] | None = None) -> int:
    """Run the Finecut desktop application."""
    args = list(argv) if argv is not None else sys.argv
    app = QApplication(args)
    app.setApplicationName("Finecut")

    window = create_main_window()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
