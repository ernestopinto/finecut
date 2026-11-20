# [FC-007] Object Deletion (`Del`) & Undo/Redo Command History (`Ctrl+Z` / `Ctrl+Y`)

| Field | Value |
| :--- | :--- |
| **Ticket ID** | `FC-007` |
| **Type** | Feature / Story |
| **Epic / Phase** | Phase 3 — Blueprint Output & Essential Editing Polish |
| **Methodology** | Agile SCRUM (Sprint 3) |
| **Status** | `DONE` (Committed on `develop`; all automated checks passed) |
| **Target Branch** | `develop` |
| **Priority** | High (Completes Phase 3 Editing Polish) |

---

## 1. Objective

Complete Phase 3 usability by allowing users to **undo and redo** any annotation action (adding strokes, adding texts, moving objects, or deleting objects) via **`Undo` (`Ctrl+Z`)** and **`Redo` (`Ctrl+Y`)**, **delete selected drawing or text objects** via **`Delete` (`Del` / `Backspace`)**, and **clear active object selection/move mode** with **`Esc`**.

---

## 2. Scope

### In Scope
1. **Immutable Snapshot Undo/Redo & Deletion in `DocumentController` (`src/finecut/application/document_controller.py`)**:
   - Maintain `_undo_stack: list[CanvasDocument]` and `_redo_stack: list[CanvasDocument]` (reset whenever `start_new_document(...)` is called).
   - Record a snapshot before each state change in `add_stroke`, `add_text`, `move_object` (when position actually changes), and `remove_object`, clearing `_redo_stack`.
   - Expose `can_undo: bool`, `can_redo: bool`, `undo() -> CanvasDocument | None`, `redo() -> CanvasDocument | None`, and `remove_object(object_id: str) -> CanvasDocument`.
2. **Scene Selection, Deletion & `Esc` Handling (`src/finecut/ui/canvas_scene.py`, `src/finecut/ui/items/text_item.py`)**:
   - Add `selected_object_ids() -> tuple[str, ...]` on `BlueprintCanvasScene` returning the domain ID(s) of any selected/move-enabled `StrokeGraphicsItem` or selected `TextGraphicsItem`.
   - Visual selection feedback on `TextGraphicsItem` (when selected, Qt's selection indicator or a subtle dashed border shows clearly which text object is selected for moving or deleting).
   - Handle `Esc` key in `BlueprintCanvasScene`: cancels any active draft text editor, or deactivates stroke move mode and clears selection.
3. **Main Window Toolbar Buttons & Shortcuts (`src/finecut/ui/main_window.py`)**:
   - Add **Undo** (`Ctrl+Z`), **Redo** (`Ctrl+Y`), and **Delete** (`Del`) buttons to the top toolbar.
   - Keep **Undo** and **Redo** button enabled states synchronized with `document_controller.can_undo` and `document_controller.can_redo`.
   - When `Delete` (`Del`) is triggered (and no draft text editor is actively being typed into), remove the selected object(s) via `DocumentController.remove_object(...)` and refresh the scene.
4. **Automated Unit & UI Tests**:
   - `tests/unit/test_document_controller.py`: unit tests for `undo()`, `redo()`, `can_undo`, `can_redo`, and `remove_object(...)` across stroke addition, text addition, object movement, and deletion.
   - `tests/ui/test_undo_redo_and_delete.py`: `pytest-qt` tests verifying:
     - Undo and Redo of strokes, text annotations, object movements, and deletions via toolbar buttons and methods.
     - Deleting a selected stroke or text object removes it from both `BlueprintCanvasScene` and `CanvasDocument`.
     - Pressing `Esc` exits stroke move mode and clears selection.

### Out of Scope (Deferred to Phase 4)
- Windows GUI Launcher (`Finecut.exe`), dev launcher (`run_finecut.bat`), and Inno Setup installer (`FinecutSetup.exe`) (`FC-008`, `FC-009`).

---

## 3. Technical Design & Architecture Notes (KIS + SOLID)

- **KIS Snapshot History**:
  - Because `CanvasDocument`, `Layer`, `StrokeObject`, and `TextObject` were designed as immutable `@dataclass(frozen=True, slots=True)` value objects in `FC-002`, Undo/Redo requires zero complex command-pattern boilerplate—just pushing/popping immutable `CanvasDocument` snapshots in `DocumentController`.
- **Single Responsibility (SRP)**:
  - `DocumentController` owns the undo/redo history stacks and document transitions.
  - `BlueprintCanvasScene` & `FinecutMainWindow` render the active `CanvasDocument` snapshot and dispatch user triggers.

---

## 4. Planned Files to Create / Update

```text
finecut/
├── docs/
│   └── tickets/
│       └── FC-007-object-deletion-and-undo-redo-history.md  (new)
├── src/
│   └── finecut/
│       ├── application/
│       │   └── document_controller.py                       (update: undo, redo, remove_object)
│       └── ui/
│           ├── canvas_scene.py                              (update: selected_object_ids, Esc handling)
│           └── main_window.py                               (update: Undo, Redo, Delete buttons & shortcuts)
└── tests/
    ├── ui/
    │   └── test_undo_redo_and_delete.py                     (new)
    └── unit/
        └── test_document_controller.py                      (update)
```

---

## 5. Acceptance Criteria

- [x] `DocumentController` supports `undo()`, `redo()`, `can_undo`, `can_redo`, and `remove_object(object_id)` across adding strokes, adding texts, moving objects, and deleting objects.
- [x] Toolbar provides **Undo** (`Ctrl+Z`), **Redo** (`Ctrl+Y`), and **Delete** (`Del`) actions, with Undo/Redo enabled states reflecting history availability.
- [x] Selecting a stroke (via double-click) or text object (via click) and triggering **Delete** removes that object from the canvas and can be restored via **Undo**.
- [x] Pressing `Esc` deactivates move mode and clears active object selection.
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
   - Run `.venv\Scripts\finecut.exe`, capture a crop, draw strokes, add text, move objects, delete an object with `Del`, and test `Ctrl+Z` / `Ctrl+Y`.

---

## 7. Definition of Done

- All Acceptance Criteria verified and passing.
- Related untracked files staged on `develop`.
- Reviewed and approved by stakeholder before committing.
