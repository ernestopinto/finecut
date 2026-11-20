# [FC-009] Minimize App to Top Floating Action Strip with "Cancel Selection" Button During Screen Capture

| Field | Value |
| :--- | :--- |
| **Ticket ID** | `FC-009` |
| **Type** | Feature / UX Enhancement |
| **Epic / Phase** | Phase 3 — Blueprint Output & Essential Editing Polish |
| **Methodology** | Agile SCRUM (Sprint 3) |
| **Status** | `DONE` (Committed on `develop`; all automated checks passed) |
| **Target Branch** | `develop` |
| **Priority** | High |

---

## 1. Objective

Match the screen-selection behavior of Windows Snipping Tool (*Ferramenta de Recorte*):
1. When clicking **`+ Novo`** (or pressing `Ctrl+N`), completely minimize/hide the **Finecut** main window before grabbing the desktop frame so the main window never appears in the frozen background screenshot.
2. During screen area selection on `SnipOverlay`, display a **floating top-center toolbox / action strip** containing a **`Cancel Selection` (`✕`) button** so the user can cancel the selection with a single mouse click (in addition to `Esc` or right-click) and return cleanly to the main window.

---

## 2. Scope

### In Scope
1. **Clean Main Window Minimization Before Capture (`src/finecut/ui/main_window.py`)**:
   - In `FinecutMainWindow.start_screen_snip()`:
     - Set window opacity to `0.0` (`setWindowOpacity(0.0)`), hide/minimize the window (`hide()`), and flush the Qt event loop (`QApplication.processEvents()`) before calling `capture_full_screen()` so Windows 11 DWM fade animations never leave a ghost of the main window on screen.
     - Restore window opacity (`setWindowOpacity(1.0)`) in `_restore_window()` when capture completes or is cancelled.
2. **Floating Top Toolbox / Action Strip on `SnipOverlay` (`src/finecut/ui/snip_overlay.py`)**:
   - Add a rounded floating **Action Strip** widget (`action_strip: QFrame`) anchored horizontally centered near the top of **Screen 1 (the primary monitor, `QGuiApplication.primaryScreen().geometry()`)** (`y = 16 px`) so it is never split across monitor bezels on dual/extended displays:
     - Displays a mode indicator label (`"Rectangular Snip"`) and a clickable **`Cancel Selection` (`✕ Cancel Selection`) button** (`cancel_button: QPushButton`).
     - Uses standard `Qt.CursorShape.ArrowCursor` on the floating action strip while keeping `Qt.CursorShape.CrossCursor` across the snipping canvas.
     - Clicking **`Cancel Selection`** calls `cancel_snip()`, closing the overlay, emitting `snip_cancelled`, and restoring `FinecutMainWindow`.
     - Re-centers automatically on `resizeEvent` / `showEvent`.
     - Because the action strip is a child overlay widget above `_frozen_screen`, cropping any region of `_frozen_screen` never includes the action strip in the captured `BaseImage`.
3. **Automated UI Tests (`tests/ui/test_snip_overlay_and_canvas.py`)**:
   - Verify `SnipOverlay` renders the visible top floating `action_strip` and `cancel_button`.
   - Verify clicking `cancel_button` on the floating action strip cancels the snipping session (`snip_cancelled`), closes `SnipOverlay`, restores `FinecutMainWindow` with full opacity (`1.0`), and preserves any previously loaded document.

---

## 3. Technical Design & Architecture Notes (KIS + SOLID)

- **Single Responsibility (SRP)**:
  - `SnipOverlay` owns the floating action strip and its `cancel_button`, delegating directly to the existing `cancel_snip()` lifecycle.
  - `FinecutMainWindow` manages its own visibility/opacity transitions around the capture session.
- **Zero DWM Ghosting on Windows 11**:
  - Setting `setWindowOpacity(0.0)` prior to `hide()` guarantees the window is immediately transparent to the Windows Desktop Window Manager without needing artificial blocking `sleep()` delays that would slow down tests or feel sluggish.

---

## 4. Planned Files to Create / Update

```text
finecut/
├── docs/
│   ├── 01-development-phases.md                                             (update ticket list)
│   └── tickets/
│       └── FC-009-snip-overlay-top-action-strip-and-cancel-button.md        (new)
├── src/
│   └── finecut/
│       └── ui/
│           ├── main_window.py                                               (update: zero-opacity hide & restore)
│           └── snip_overlay.py                                              (update: floating top action strip & cancel_button)
└── tests/
    └── ui/
        └── test_snip_overlay_and_canvas.py                                  (update: test action strip & cancel_button click)
```

---

## 5. Acceptance Criteria

- [x] Clicking **`+ Novo`** (or pressing `Ctrl+N`) completely hides `FinecutMainWindow` (`windowOpacity == 0.0` before capture) so only the snipping overlay and its top floating action strip are visible.
- [x] `SnipOverlay` displays a top-centered floating toolbox / action strip containing a **`Cancel Selection`** button.
- [x] Clicking the **`Cancel Selection`** button on the floating action strip cancels the selection, closes the overlay, and restores `FinecutMainWindow` (`windowOpacity == 1.0`).
- [x] `ruff check src tests` and `ruff format --check src tests` pass with `0` errors.
- [x] `mypy src tests` passes with `0` errors under `strict = true`.
- [x] `pytest -v` passes all unit and UI tests (including under `QT_QPA_PLATFORM=offscreen`).

---

## 6. Verification Plan (Post-Implementation)

1. Verify active branch: `git branch --show-current` -> `develop`.
2. Run static checks:
   - `.venv\Scripts\ruff.exe check src tests`
   - `.venv\Scripts\ruff.exe format --check src tests`
   - `.venv\Scripts\mypy.exe src tests`
3. Run automated test suite (offscreen CI mode):
   - `$env:QT_QPA_PLATFORM='offscreen'; .venv\Scripts\pytest.exe -v`
4. Manual desktop check:
   - Run `.venv\Scripts\finecut.exe`, click **`+ Novo`**, verify the main window disappears completely and the floating top action strip appears with the **`Cancel Selection`** button, and test both clicking **`Cancel Selection`** and dragging a crop.

---

## 7. Definition of Done

- All Acceptance Criteria verified and passing.
- Related untracked files staged on `develop`.
- Reviewed and approved by stakeholder before committing.
