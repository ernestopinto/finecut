"""Generate multi-resolution Windows ICO icon for Finecut using PySide6."""

from __future__ import annotations

import os
import struct
import sys
from pathlib import Path

from PySide6.QtCore import QBuffer, QIODevice
from PySide6.QtGui import QGuiApplication

from finecut.ui.toolbar_icons import render_app_icon_pixmap

ICO_SIZES: tuple[int, ...] = (16, 32, 48, 64, 128, 256)
DEFAULT_OUTPUT_PATH = Path(__file__).resolve().parent / "assets" / "finecut.ico"


def _pixmap_to_png_bytes(size: int) -> bytes:
    pixmap = render_app_icon_pixmap(size)
    buf = QBuffer()
    buf.open(QIODevice.OpenModeFlag.WriteOnly)
    if not pixmap.save(buf, "PNG"):
        raise RuntimeError(f"Failed to encode {size}x{size} icon frame as PNG.")
    return bytes(buf.data().data())


def write_ico(output_path: Path = DEFAULT_OUTPUT_PATH) -> Path:
    """Render all ICO_SIZES frames and write a standard PNG-compressed Windows .ico file."""
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QGuiApplication.instance() or QGuiApplication(sys.argv)
    del app

    frames: list[tuple[int, bytes]] = [(size, _pixmap_to_png_bytes(size)) for size in ICO_SIZES]
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # ICONDIR header: reserved=0, type=1 (ICO), count=len(frames)
    header = struct.pack("<HHH", 0, 1, len(frames))
    offset = 6 + 16 * len(frames)
    directory_entries: list[bytes] = []

    for size, png_data in frames:
        dim_byte = 0 if size >= 256 else size
        entry = struct.pack(
            "<BBBBHHII",
            dim_byte,  # width (0 means 256)
            dim_byte,  # height (0 means 256)
            0,  # color count
            0,  # reserved
            1,  # color planes
            32,  # bits per pixel
            len(png_data),
            offset,
        )
        directory_entries.append(entry)
        offset += len(png_data)

    payload = b"".join([header, *directory_entries, *(png for _, png in frames)])
    output_path.write_bytes(payload)
    return output_path


if __name__ == "__main__":
    written = write_ico()
    print(f"Generated Finecut icon: {written}")
