"""Application controller managing CanvasDocument lifecycle and state transitions."""

from finecut.domain.models import BaseImage, CanvasDocument


class DocumentController:
    """Orchestrates active CanvasDocument creation and state transitions."""

    def __init__(self) -> None:
        self._current_document: CanvasDocument | None = None

    @property
    def current_document(self) -> CanvasDocument | None:
        """Return the currently loaded CanvasDocument, or None if no snip is loaded."""
        return self._current_document

    @property
    def has_document(self) -> bool:
        """Return True when a captured base image document is loaded."""
        return self._current_document is not None

    def start_new_document(self, base_image: BaseImage) -> CanvasDocument:
        """Initialize and activate a new CanvasDocument from a captured BaseImage."""
        document = CanvasDocument.from_base_image(base_image)
        self._current_document = document
        return document
