"""UI and adapter tests for flattening the canvas, copying to clipboard, and saving PNG/JPG."""

from pathlib import Path

from PySide6.QtGui import QColor, QPixmap
from pytestqt.qtbot import QtBot

from finecut.domain.models import BaseImage, FontFamily, Point, StrokeColor
from finecut.infrastructure.export_adapters import QtClipboardAdapter, QtFileImageExporter
from finecut.infrastructure.screen_capturer import (
    base_image_to_pixmap,
    pixmap_to_base_image,
)
from finecut.ui.main_window import FinecutMainWindow
from tests.ui.test_main_window import FakeScreenCapturer


class RecordingClipboardAdapter:
    """In-memory ClipboardPort spy that also delegates to QtClipboardAdapter."""

    def __init__(self) -> None:
        self.copied_images: list[BaseImage] = []
        self._qt_adapter = QtClipboardAdapter()

    def copy_image(self, image: BaseImage) -> None:
        self.copied_images.append(image)
        self._qt_adapter.copy_image(image)


def _sample_base_image(width: int = 360, height: int = 240) -> BaseImage:
    pixmap = QPixmap(width, height)
    pixmap.fill(QColor("#FFFFFF"))
    return pixmap_to_base_image(pixmap)


def test_copy_and_save_before_crop_show_guidance_message(
    qtbot: QtBot,
    tmp_path: Path,
) -> None:
    """Verify Copy and Save gracefully inform the user when no crop is loaded yet."""
    clipboard_spy = RecordingClipboardAdapter()
    window = FinecutMainWindow(
        screen_capturer=FakeScreenCapturer(),
        clipboard_port=clipboard_spy,
    )
    qtbot.addWidget(window)

    assert window.copy_blueprint_to_clipboard() is False
    assert "before copying" in window.statusBar().currentMessage()
    assert len(clipboard_spy.copied_images) == 0

    target = tmp_path / "unused.png"
    assert window.save_blueprint_to_file(target) is None
    assert "before saving" in window.statusBar().currentMessage()
    assert not target.exists()


def test_flatten_copy_to_clipboard_and_save_png_and_jpg(
    qtbot: QtBot,
    tmp_path: Path,
) -> None:
    """Verify flattening a crop with strokes and text, copying to clipboard, and saving files."""
    clipboard_spy = RecordingClipboardAdapter()
    exporter = QtFileImageExporter()
    window = FinecutMainWindow(
        screen_capturer=FakeScreenCapturer(360, 240),
        clipboard_port=clipboard_spy,
        image_exporter=exporter,
    )
    qtbot.addWidget(window)
    window.show()

    base = _sample_base_image(360, 240)
    window._on_snip_captured(base)

    stroke = window.document_controller.add_stroke(
        points=(Point(20.0, 20.0), Point(180.0, 120.0)),
        color=StrokeColor.RED,
        stroke_width=4.0,
    )
    stroke_item = window.canvas_scene.add_stroke_item(stroke)
    stroke_item.enable_move_mode()
    assert stroke_item.is_move_enabled is True

    text_obj = window.document_controller.add_text(
        text="Submit Form",
        position=Point(50.0, 140.0),
        font_family=FontFamily.ARIAL,
        color=StrokeColor.BLUE,
    )
    window.canvas_scene.add_text_item(text_obj)

    window.copy_button.click()
    assert stroke_item.is_move_enabled is False
    assert len(clipboard_spy.copied_images) == 1

    flattened = clipboard_spy.copied_images[0]
    assert flattened.width == 360
    assert flattened.height == 240
    assert flattened.png_bytes != base.png_bytes
    assert "Copied blueprint to clipboard" in window.statusBar().currentMessage()

    png_path = tmp_path / "blueprint.png"
    saved_png = window.save_blueprint_to_file(png_path)
    assert saved_png == png_path
    assert png_path.exists()
    assert png_path.stat().st_size > 0
    assert "Saved blueprint to blueprint.png" in window.statusBar().currentMessage()

    loaded_png = QPixmap(str(png_path))
    assert not loaded_png.isNull()
    assert loaded_png.width() == 360
    assert loaded_png.height() == 240

    jpg_path = tmp_path / "blueprint.jpg"
    saved_jpg = window.save_blueprint_to_file(jpg_path)
    assert saved_jpg == jpg_path
    assert jpg_path.exists()
    assert jpg_path.stat().st_size > 0

    decoded_flattened = base_image_to_pixmap(flattened)
    assert not decoded_flattened.isNull()
