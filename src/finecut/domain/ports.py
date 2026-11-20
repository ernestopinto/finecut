"""Domain port protocols for external adapters (Dependency Inversion Principle)."""

from pathlib import Path
from typing import Protocol

from finecut.domain.models import BaseImage, Rect


class ScreenCapturer(Protocol):
    """Port interface for capturing full screen or a rectangular desktop crop."""

    def capture_full_screen(self) -> BaseImage:
        """Capture the full virtual desktop across connected displays."""

    def capture_region(self, region: Rect) -> BaseImage:
        """Capture a specific rectangular screen region."""


class ClipboardPort(Protocol):
    """Port interface for copying a flattened blueprint image to the system clipboard."""

    def copy_image(self, image: BaseImage) -> None:
        """Copy the flattened blueprint image to the system clipboard."""


class ImageExporter(Protocol):
    """Port interface for exporting a flattened blueprint image to disk."""

    def save_image(self, image: BaseImage, file_path: Path) -> None:
        """Write the flattened blueprint image to disk (PNG or JPEG)."""
