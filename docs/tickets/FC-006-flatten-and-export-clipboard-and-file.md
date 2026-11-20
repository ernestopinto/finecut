# [FC-006] Flatten & Export (Clipboard Copy `Ctrl+C` + Save PNG/JPG `Ctrl+S`)

| Field | Value |
| :--- | :--- |
| **Ticket ID** | `FC-006` |
| **Type** | Feature / Story |
| **Epic / Phase** | Phase 3 — Blueprint Output & Essential Editing Polish |
| **Methodology** | Agile SCRUM (Sprint 3) |
| **Status** | `DONE` (Committed on `develop`; all automated checks passed) |
| **Target Branch** | `develop` |
| **Priority** | High |

---

## 1. Objective

Enable users to immediately share or archive their annotated interface blueprint by **copying the flattened canvas (base crop + `n` strokes + `n` texts) to the Windows Clipboard (`Copy` button / `Ctrl+C`)** or **saving it to disk as a PNG or JPEG image (`Save` button / `Ctrl+S`)**.

---

## 2. Scope

### In Scope
1. **Domain Port Protocols (`src/finecut/domain/ports.py`)**:
   - Add `ClipboardPort(Protocol)`:
     - `copy_image(image: BaseImage) -> None`
   - Add `ImageExporter(Protocol)`:
     - `save_image(image: BaseImage, file_path: Path) -> None`
2. **Infrastructure Export Adapters (`src/finecut/infrastructure/export_adapters.py`)**:
   - `QtClipboardAdapter`: implements `ClipboardPort` using `QGuiApplication.clipboard().setPixmap(...)`.
   - `QtFileImageExporter`: implements `ImageExporter` saving a `BaseImage` as `PNG` (`.png`) or `JPEG` (`.jpg` / `.jpeg`) on disk.
3. **Clean Canvas Flattening (`src/finecut/ui/canvas_scene.py`)**:
   - Add `render_flattened_image() -> BaseImage` on `BlueprintCanvasScene`:
     - Finalizes any open `DraftTextGraphicsItem` (`commit_or_cancel()`).
     - Clears selection and deactivates stroke move-mode dashed bounding boxes (`deactivate_all_move_modes()`, `clearSelection()`) so UI selection chrome never appears in exported images.
     - Renders the scene (`base_image` + all visible `StrokeGraphicsItem` and `TextGraphicsItem` objects) into a HiDPI-aware `QPixmap` and returns it as a `BaseImage`.
4. **Toolbar Buttons & Keyboard Shortcuts (`src/finecut/ui/main_window.py`, `src/finecut/main.py`)**:
   - Add **Copy** (`Ctrl+C`) and **Save** (`Ctrl+S`) buttons to the top toolbar.
   - Inject `ClipboardPort` and `ImageExporter` into `FinecutMainWindow` (defaulting to `QtClipboardAdapter()` and `QtFileImageExporter()`).
   - Provide clear status bar feedback when a blueprint is copied or saved (or when invoked before any screen crop is loaded).
5. **Automated Unit & UI Tests**:
   - `tests/ui/test_flatten_and_export.py`: `pytest-qt` tests verifying:
     - Flattening a canvas with a base crop, freehand strokes, and committed text objects produces a valid `BaseImage` of exact dimensions with selection borders stripped.
     - Clicking **Copy** (`Ctrl+C`) invokes `ClipboardPort.copy_image` and updates the Windows clipboard / status bar.
     - Saving via **Save** (`Ctrl+S` / `save_blueprint_to_file`) writes valid `.png` and `.jpg` files to disk via `QtFileImageExporter`.

### Out of Scope (Deferred to Next Ticket)
- Object deletion (`Del` / `Backspace`) and Undo/Redo command history (`Ctrl+Z` / `Ctrl+Y`) (`FC-007`).

---

## 3. Technical Design & Architecture Notes (KIS + SOLID)

- **Interface Segregation & Dependency Inversion (ISP / DIP)**:
  - `ClipboardPort` and `ImageExporter` are small, single-method protocols in `finecut.domain.ports`, allowing `FinecutMainWindow` to be tested with in-memory fakes or real temporary files without modal `QFileDialog` popups blocking CI.
- **KIS Principle**:
  - Use `QGraphicsScene.render(...)` directly onto a `QPixmap` matching the base image's pixel dimensions and `devicePixelRatio`—guaranteed 1:1 visual fidelity between what the user sees on canvas and what lands in the clipboard or file.

---

## 4. Planned Files to Create / Update

```text
finecut/
├── docs/
│   └── tickets/
│       └── FC-006-flatten-and-export-clipboard-and-file.md  (new)
├── src/
│   └── finecut/
│       ├── main.py                                          (update wiring)
│       ├── domain/
│       │   ├── __init__.py                                  (update exports)
│       │   └── ports.py                                     (update: ClipboardPort, ImageExporter)
│       ├── infrastructure/
│       │   ├── __init__.py                                  (update exports)
│       │   └── export_adapters.py                           (new)
│       └── ui/
│           ├── canvas_scene.py                              (update: render_flattened_image)
│           └── main_window.py                               (update: Copy/Save buttons & Ctrl+C/Ctrl+S)
└── tests/
    └── ui/
        └── test_flatten_and_export.py                       (new)
```

---

## 5. Acceptance Criteria

- [x] `BlueprintCanvasScene.render_flattened_image()` flattens the base crop and all `n` drawings/texts into a `BaseImage` while stripping active selection/move borders.
- [x] Clicking **Copy** (or pressing `Ctrl+C`) copies the flattened blueprint image to the clipboard and shows status bar confirmation.
- [x] Clicking **Save** (or pressing `Ctrl+S`) exports the flattened blueprint image to disk in `.png` or `.jpg`/`.jpeg` format and shows status bar confirmation.
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
3. Run automated test suite (desktop + offscreen CI mode):
   - `$env:QT_QPA_PLATFORM='offscreen'; .venv\Scripts\pytest.exe -v`
4. Manual desktop check:
   - Run `.venv\Scripts\finecut.exe`, capture a screen crop (`+ Novo`), draw strokes and add text, press `Ctrl+C` (or click **Copy**) and paste into Paint/Slack/Teams, and press `Ctrl+S` (or click **Save**) to save a `.png`.

---

## 7. Definition of Done

- All Acceptance Criteria verified and passing.
- Related untracked files staged on `develop`.
- Reviewed and approved by stakeholder before committing.
