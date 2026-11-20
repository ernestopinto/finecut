# [FC-003] Windows Screen Crop Overlay (`+ Novo`) & Base Image Loading

| Field | Value |
| :--- | :--- |
| **Ticket ID** | `FC-003` |
| **Type** | Feature / Story |
| **Epic / Phase** | Phase 1 — Screen Capture ("Novo Recorte") |
| **Methodology** | Agile SCRUM (Sprint 1) |
| **Status** | `DONE` (Committed on `develop`; all automated checks passed) |
| **Target Branch** | `develop` |
| **Priority** | High (Completes Phase 1 screen capture workflow) |

---

## 1. Objective

Implement the end-to-end **Screen Capture (`+ Novo`)** workflow so the user can click `+ Novo` (or press `Ctrl+N`), drag-select any rectangular region on a frozen full-screen overlay (just like Windows *Ferramenta de Recorte*), and immediately see the cropped region loaded as the immutable `BaseImage` inside Finecut's interactive `QGraphicsScene` canvas.

---

## 2. Scope

### In Scope
1. **Qt Screen Capture Adapter (`src/finecut/infrastructure/screen_capturer.py`)**:
   - Implement `QtScreenCapturer` conforming to the domain `ScreenCapturer` protocol (`capture_full_screen() -> BaseImage`, `capture_region(region: Rect) -> BaseImage`).
   - Support Windows HiDPI scaling (`devicePixelRatio`) and virtual desktop geometry across connected screens.
   - Provide helper conversion between `BaseImage` (`png_bytes`) and `QPixmap` at the infrastructure/UI boundary so `domain/` remains 100% free of `PySide6`.
2. **Application Document Controller (`src/finecut/application/document_controller.py`)**:
   - Create `DocumentController` to orchestrate document lifecycle (`current_document: CanvasDocument | None`, `start_new_document(base_image: BaseImage) -> CanvasDocument`).
   - Keeps domain state orchestration out of `QMainWindow` (SOLID Single Responsibility).
3. **Full-Screen Snipping Overlay (`src/finecut/ui/snip_overlay.py`)**:
   - Create `SnipOverlay(QWidget)`:
     - Frameless, top-most (`Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool`), crosshair cursor (`Qt.CursorShape.CrossCursor`).
     - Displays the frozen desktop screenshot with a dimmed backdrop outside the active drag selection rectangle.
     - Normalizes selection coordinates in any drag direction (top-left to bottom-right or reverse).
     - Displays a crisp selection border and live pixel dimension indicator (`W × H`).
     - On mouse release with a valid region (`width >= 5` and `height >= 5`): crops the frozen image to a `BaseImage` (respecting `device_pixel_ratio`), emits `snip_captured(BaseImage)`, and closes.
     - On `Esc` key press (or too-small selection): emits `snip_cancelled` and closes cleanly.
4. **Blueprint Canvas Scene & View (`src/finecut/ui/canvas_scene.py`, `src/finecut/ui/canvas_view.py`)**:
   - `BlueprintCanvasScene(QGraphicsScene)`:
     - Renders the `BaseImage` as the background `QGraphicsPixmapItem` (`zValue = -1000`, non-movable/non-selectable) ready for Phase 2 drawing and text objects on top.
   - `BlueprintCanvasView(QGraphicsView)`:
     - Displays `BlueprintCanvasScene` with smooth pixmap transformation and centered scrollbars when the crop exceeds window bounds.
5. **Main Window Integration (`src/finecut/ui/main_window.py`, `src/finecut/main.py`)**:
   - Wire `+ Novo` button and `Ctrl+N` shortcut in `FinecutMainWindow`.
   - Hide `FinecutMainWindow` briefly before capturing the full screen so Finecut itself does not obscure the target application behind it, then show `SnipOverlay`.
   - When `snip_captured(BaseImage)` fires: load the `BaseImage` into `DocumentController`, switch from the empty-state prompt to `BlueprintCanvasView`, restore `FinecutMainWindow`, and update the status bar with captured crop dimensions (`e.g., "Captured crop: 640 × 400 px"`).
   - When `snip_cancelled` fires: restore `FinecutMainWindow` without losing any existing canvas document.
6. **Automated Unit & UI Tests**:
   - `tests/unit/test_document_controller.py`: unit tests for `DocumentController`.
   - `tests/ui/test_snip_overlay_and_canvas.py`: `pytest-qt` tests verifying `SnipOverlay` drag-selection crop, `Esc` cancellation, `BlueprintCanvasScene` base image loading, and `FinecutMainWindow` transition from empty placeholder to loaded crop canvas.

### Out of Scope (Deferred to Phase 2)
- Freehand drawing tool in Red/Blue and double-click-to-move stroke objects (`FC-004`).
- Text annotation tool in 4 fonts and `Enter`-to-commit movable text objects (`FC-005`).

---

## 3. Technical Design & Architecture Notes (KIS + SOLID)

- **Single Responsibility (SRP)**:
  - `QtScreenCapturer`: OS/Qt screen grab and `QPixmap` <-> `BaseImage` encoding only.
  - `DocumentController`: pure application state transitions on `CanvasDocument`.
  - `SnipOverlay`: interactive region selection over a frozen frame only.
  - `BlueprintCanvasScene` / `BlueprintCanvasView`: displaying the document's `BaseImage` (and later `CanvasObject` items).
- **HiDPI Accuracy on Windows**:
  - When cropping a `QPixmap` with `devicePixelRatio() > 1.0`, logical selection coordinates `(x, y, w, h)` are scaled by the pixmap's `devicePixelRatio` for the pixel crop, while preserving `device_pixel_ratio` on the resulting `QPixmap` / `BaseImage` so text and strokes align 1:1 on high-DPI monitors.
- **KIS Principle**:
  - Crop directly from the frozen full-screen snapshot taken when `+ Novo` is clicked—this guarantees what the user sees under their crosshair is the exact pixels cropped, even if background windows animate or change during drag selection.

---

## 4. Planned Files to Create / Update

```text
finecut/
├── docs/
│   └── tickets/
│       └── FC-003-windows-screen-crop-overlay-and-base-image-loading.md  (new)
├── src/
│   └── finecut/
│       ├── main.py                                                       (update wiring)
│       ├── application/
│       │   ├── __init__.py                                               (update exports)
│       │   └── document_controller.py                                    (new)
│       ├── infrastructure/
│       │   ├── __init__.py                                               (update exports)
│       │   └── screen_capturer.py                                        (new)
│       └── ui/
│           ├── __init__.py                                               (update exports)
│           ├── canvas_scene.py                                           (new)
│           ├── canvas_view.py                                            (new)
│           ├── main_window.py                                            (update)
│           └── snip_overlay.py                                           (new)
└── tests/
    ├── ui/
    │   ├── test_main_window.py                                           (update)
    │   └── test_snip_overlay_and_canvas.py                               (new)
    └── unit/
        └── test_document_controller.py                                   (new)
```

---

## 5. Acceptance Criteria

- [x] Clicking `+ Novo` (or pressing `Ctrl+N`) hides the main window, captures the frozen desktop, and opens `SnipOverlay`.
- [x] Dragging a valid rectangle (`>= 5 × 5` px) in any direction and releasing crops the selected region into a `BaseImage`, loads a new `CanvasDocument` in `DocumentController`, and displays it in `BlueprintCanvasView`.
- [x] Pressing `Esc` during snipping cancels the overlay and restores `FinecutMainWindow` without overwriting any previously loaded document.
- [x] `BlueprintCanvasScene` places the cropped `BaseImage` as a background pixmap item (`zValue = -1000`) ready for `n` foreground objects in Phase 2.
- [x] `ruff check src tests` and `ruff format --check src tests` pass with `0` errors.
- [x] `mypy src tests` passes with `0` errors under `strict = true`.
- [x] `pytest -v` passes all unit and UI tests.

---

## 6. Verification Plan (Post-Implementation)

1. Verify active branch: `git branch --show-current` -> `develop`.
2. Run static checks:
   - `.venv\Scripts\ruff.exe check src tests`
   - `.venv\Scripts\ruff.exe format --check src tests`
   - `.venv\Scripts\mypy.exe src tests`
3. Run automated test suite:
   - `.venv\Scripts\pytest.exe -v`
4. Manual desktop check:
   - Run `.venv\Scripts\finecut.exe`, click `+ Novo`, drag-select a region of the screen, and confirm the cropped screenshot renders crisply inside the canvas window.

---

## 7. Definition of Done

- All Acceptance Criteria verified and passing.
- Related untracked files staged on `develop`.
- Reviewed and approved by stakeholder before committing.
