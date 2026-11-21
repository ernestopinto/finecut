"""UI tests for SnipOverlay, BlueprintCanvasScene, and end-to-end base image loading."""

from PySide6.QtCore import QPoint, QRect, Qt
from PySide6.QtGui import QColor, QPixmap
from PySide6.QtTest import QTest
from pytestqt.qtbot import QtBot

from finecut.domain.models import BaseImage, CanvasDocument, Rect
from finecut.infrastructure.screen_capturer import (
    base_image_to_pixmap,
    crop_base_image,
    pixmap_to_base_image,
)
from finecut.ui.canvas_scene import BASE_IMAGE_Z_VALUE, BlueprintCanvasScene
from finecut.ui.main_window import FinecutMainWindow
from finecut.ui.snip_overlay import SnipOverlay
from tests.ui.test_main_window import FakeScreenCapturer


def _make_base_image(width: int = 500, height: int = 400, dpr: float = 1.0) -> BaseImage:
    pixmap = QPixmap(width, height)
    pixmap.fill(QColor("#264653"))
    pixmap.setDevicePixelRatio(dpr)
    return pixmap_to_base_image(pixmap)


def test_pixmap_roundtrip_and_hidpi_crop(qtbot: QtBot) -> None:
    """Verify BaseImage <-> QPixmap conversion and HiDPI logical rectangle cropping."""
    del qtbot
    source = _make_base_image(width=400, height=300, dpr=2.0)
    decoded = base_image_to_pixmap(source)
    assert decoded.width() == 400
    assert decoded.height() == 300
    assert decoded.devicePixelRatio() == 2.0

    cropped = crop_base_image(source, Rect(x=10, y=15, width=80, height=60))
    assert cropped.width == 160
    assert cropped.height == 120
    assert cropped.device_pixel_ratio == 2.0


def test_snip_overlay_drag_captures_region(qtbot: QtBot) -> None:
    """Verify dragging a valid rectangle in SnipOverlay emits snip_captured with the crop."""
    frozen = _make_base_image(width=500, height=400)
    overlay = SnipOverlay(frozen, virtual_geometry=QRect(0, 0, 500, 400))
    qtbot.addWidget(overlay)
    overlay.show()

    captured_images: list[BaseImage] = []
    overlay.snip_captured.connect(captured_images.append)

    QTest.mousePress(
        overlay,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(150, 120),
    )
    QTest.mouseMove(overlay, QPoint(50, 40))
    QTest.mouseRelease(
        overlay,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(50, 40),
    )

    assert len(captured_images) == 1
    assert captured_images[0].width == 100
    assert captured_images[0].height == 80


def test_snip_overlay_escape_and_tiny_selection_cancel(qtbot: QtBot) -> None:
    """Verify pressing Escape or releasing a <5px selection cancels the snip."""
    frozen = _make_base_image(width=300, height=200)
    overlay = SnipOverlay(frozen, virtual_geometry=QRect(0, 0, 300, 200))
    qtbot.addWidget(overlay)
    overlay.show()

    cancelled_count = 0

    def _on_cancel() -> None:
        nonlocal cancelled_count
        cancelled_count += 1

    overlay.snip_cancelled.connect(_on_cancel)

    QTest.keyClick(overlay, Qt.Key.Key_Escape)
    assert cancelled_count == 1

    overlay.show()
    QTest.mousePress(
        overlay,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(20, 20),
    )
    QTest.mouseRelease(
        overlay,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(22, 22),
    )
    assert cancelled_count == 2


def test_canvas_scene_loads_locked_background_pixmap(qtbot: QtBot) -> None:
    """Verify BlueprintCanvasScene places the base crop at z=-1000 and locks it."""
    del qtbot
    scene = BlueprintCanvasScene()
    assert scene.has_base_image is False

    doc = CanvasDocument.from_base_image(_make_base_image(width=320, height=240))
    scene.set_document(doc)

    assert scene.has_base_image is True
    assert scene.base_pixmap_item is not None
    assert scene.base_pixmap_item.zValue() == BASE_IMAGE_Z_VALUE
    assert scene.sceneRect() == QRect(0, 0, 320, 240)


def test_main_window_end_to_end_snip_loads_canvas_and_preserves_on_cancel(qtbot: QtBot) -> None:
    """Verify completing a snip loads the canvas view and cancelling keeps existing crop."""
    window = FinecutMainWindow(screen_capturer=FakeScreenCapturer(500, 400))
    qtbot.addWidget(window)
    window.show()

    window.start_screen_snip()
    assert window.active_overlay is not None

    overlay = window.active_overlay
    QTest.mousePress(
        overlay,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(10, 10),
    )
    QTest.mouseMove(overlay, QPoint(210, 160))
    QTest.mouseRelease(
        overlay,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(210, 160),
    )

    assert window.active_overlay is None
    assert window.is_showing_canvas is True
    assert window.canvas_scene.has_base_image is True
    assert window.document_controller.current_document is not None
    assert window.document_controller.current_document.base_image.width == 200
    assert window.document_controller.current_document.base_image.height == 150
    assert "200 x 150 px" in window.statusBar().currentMessage()

    window.start_screen_snip()
    assert window.active_overlay is not None
    assert window.windowOpacity() == 0.0
    assert window.active_overlay.action_strip.isVisible() is True
    assert window.active_overlay.cancel_button.text() == "Cancel Selection"

    window.active_overlay.cancel_button.click()

    assert window.active_overlay is None
    assert window.windowOpacity() == 1.0
    assert window.is_showing_canvas is True
    assert window.document_controller.current_document.base_image.width == 200


def test_snip_overlay_centers_action_strip_on_primary_screen_in_extended_displays(
    qtbot: QtBot,
) -> None:
    """Verify on dual/extended screens the action strip centers on Screen 1, not the bezel."""
    frozen = _make_base_image(width=3840, height=1080)
    virtual_geo = QRect(0, 0, 3840, 1080)
    primary_geo = QRect(0, 0, 1920, 1080)

    overlay = SnipOverlay(
        frozen,
        virtual_geometry=virtual_geo,
        primary_screen_geometry=primary_geo,
    )
    qtbot.addWidget(overlay)
    overlay.show()

    strip_center_x = overlay.action_strip.x() + overlay.action_strip.width() // 2
    assert abs(strip_center_x - 960) <= 2
    assert overlay.action_strip.geometry().right() < 1920


def test_large_crop_adapts_window_and_fits_canvas_without_scrollbars(qtbot: QtBot) -> None:
    """Verify big crops disable scrollbars, grow the window, and scale down if oversized."""
    window = FinecutMainWindow(screen_capturer=FakeScreenCapturer(1200, 800))
    qtbot.addWidget(window)
    window.show()

    assert window.canvas_view.horizontalScrollBarPolicy() == Qt.ScrollBarPolicy.ScrollBarAlwaysOff
    assert window.canvas_view.verticalScrollBarPolicy() == Qt.ScrollBarPolicy.ScrollBarAlwaysOff

    large_crop = _make_base_image(width=2400, height=1600)
    window._on_snip_captured(large_crop)

    assert window.width() >= window.minimumWidth()
    assert window.height() >= window.minimumHeight()
    # Oversized crop must be scaled down cleanly inside the viewport (< 1.0 transform scale)
    assert window.canvas_view.transform().m11() < 1.0
    assert window.canvas_view.transform().m22() < 1.0
