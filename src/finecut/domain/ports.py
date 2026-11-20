"""Domain port protocols for external adapters (Dependency Inversion Principle)."""

from typing import Protocol

from finecut.domain.models import BaseImage, Rect


class ScreenCapturer(Protocol):
    """Port interface for capturing full screen or a rectangular desktop crop."""

    def capture_full_screen(self) -> BaseImage:
        """Capture the full virtual desktop across connected displays."""

    def capture_region(self, region: Rect) -> BaseImage:
        """Capture a specific rectangular screen region."""
