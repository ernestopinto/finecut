"""Unit tests for DocumentController."""

from finecut.application.document_controller import DocumentController
from finecut.domain.models import BaseImage


def test_document_controller_lifecycle() -> None:
    """Verify DocumentController starts empty and initializes a CanvasDocument on snip."""
    controller = DocumentController()
    assert controller.current_document is None
    assert controller.has_document is False

    sample_image = BaseImage(
        width=640,
        height=400,
        png_bytes=b"\x89PNG\r\n\x1a\n",
        device_pixel_ratio=1.0,
    )
    document = controller.start_new_document(sample_image)

    assert controller.has_document is True
    assert controller.current_document == document
    assert document.base_image == sample_image
    assert len(document.layers) == 1
    assert document.layers[0].name == "Layer 1"
