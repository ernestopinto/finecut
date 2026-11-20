# [FC-008] Fix Text Creation Mechanics (Double-Click to Add, Single-Click Outside to Commit) & Independent Single-Object Movement Bug

| Field | Value |
| :--- | :--- |
| **Ticket ID** | `FC-008` |
| **Type** | Bugfix & UX Mechanics Refinement |
| **Epic / Phase** | Phase 3 — Blueprint Output & Essential Editing Polish |
| **Methodology** | Agile SCRUM (Sprint 3) |
| **Status** | `DONE` (Committed on `develop`; all automated checks passed) |
| **Target Branch** | `develop` |
| **Priority** | Highest (Blocker before Phase 4 Packaging) |

---

## 1. Objective

Address two critical interaction issues discovered during manual desktop testing:
1. **Text Creation & Validation Mechanics**:
   - After selecting the **Text** tool (`CanvasTool.TEXT`), the user must **double-click** on the canvas image to start adding a new text object.
   - **One single click outside** the active draft text object (or pressing `Enter`) validates and saves/commits the text object onto the image (without spawning a new draft text box on that single click).
   - Once committed, the user can still freely drag and move the text object anywhere on the canvas (no regression).
2. **Independent Single-Object Movement Bug**:
   - Each added object (whether a `TextObject` or a `StrokeObject`) **must be completely independent** so the user moves only **one object at a time**.
   - Fix the multi-selection bug where creating two objects and dragging the second caused Qt's `QGraphicsScene` to move both objects together.

---

## 2. Root Cause Analysis (Issue #2 — Multi-Object Movement Bug)

- In `TextGraphicsItem.mousePressEvent`, `self.setSelected(True)` was called **before** `super().mousePressEvent(event)`.
- In Qt's `QGraphicsItem::mousePressEvent`, when an item already has `isSelected() == True` upon entering the base handler, Qt assumes the user is dragging an existing **multi-selection group** and skips calling `scene->clearSelection()`.
- As a result, clicking Object 1 selected Object 1, and subsequently clicking Object 2 selected Object 2 *without* deselecting Object 1—causing `QGraphicsItem::mouseMoveEvent` to translate every item in `scene.selectedItems()` simultaneously.

---

## 3. Scope

### In Scope
1. **Text Tool Mechanics (`src/finecut/ui/canvas_scene.py`, `src/finecut/ui/items/text_item.py`)**:
   - **Double-Click to Start Text**:
     - In `CanvasTool.TEXT` mode, single-clicking empty canvas **does not** spawn a new `DraftTextGraphicsItem`.
     - **Double-clicking** on the canvas (when no existing stroke or text item is under the cursor) opens a new `DraftTextGraphicsItem` at the double-clicked coordinate with keyboard focus.
   - **Single-Click Outside to Validate & Save**:
     - When a `DraftTextGraphicsItem` is active, **one single click outside** the draft item calls `commit_or_cancel()` (validating non-empty text and saving it as a committed `TextObject` / `TextGraphicsItem` on the canvas, or discarding if blank) and consumes that click without opening another draft editor.
     - Pressing `Enter` continues to validate/commit the text as well, and pressing `Esc` cancels the draft.
   - **No Regression on Moving Committed Text**:
     - Pressing and dragging on any committed `TextGraphicsItem` moves it freely to any position on the canvas.
2. **Strict Single-Object Independence (`src/finecut/ui/canvas_scene.py`, `src/finecut/ui/items/text_item.py`, `src/finecut/ui/items/stroke_item.py`)**:
   - Enforce exclusive single-item selection across the entire `BlueprintCanvasScene`:
     - When pressing on a `TextGraphicsItem`, clear selection on all other scene items and deactivate move mode on all `StrokeGraphicsItem` instances (`deactivate_all_move_modes()`, `clearSelection()`) before selecting that single `TextGraphicsItem`.
     - When double-clicking a `StrokeGraphicsItem` to enable move mode, clear selection on all `TextGraphicsItem` instances and deactivate move mode on all other `StrokeGraphicsItem` instances so only that single stroke is selected and movable.
     - Clicking empty canvas deselects all objects and exits stroke move mode.
3. **Automated Regression Tests (`tests/ui/test_text_annotation.py`)**:
   - Verify that in **Text** mode:
     - A single click on empty canvas does **not** open a draft text editor.
     - A **double-click** on the canvas opens the `DraftTextGraphicsItem`.
     - A **single click outside** the draft text editor validates and saves the text object onto the canvas (without spawning a second draft editor).
   - Verify **single-object movement independence**:
     - Create 2+ text objects (and stroke objects), drag Object 1 to a new position, then drag Object 2 to a new position, and assert that moving Object 2 **never** alters Object 1's scene or domain position (and vice versa).

---

## 4. Planned Files to Create / Update

```text
finecut/
├── docs/
│   ├── 00-approach-and-architecture.md                                               (update text mechanics spec)
│   ├── 01-development-phases.md                                                      (update ticket numbering)
│   └── tickets/
│       └── FC-008-fix-text-creation-mechanics-and-independent-object-movement.md     (new)
├── src/
│   └── finecut/
│       └── ui/
│           ├── canvas_scene.py                                                       (update: double-click text creation, single-click outside commit, exclusive selection)
│           └── items/
│               ├── stroke_item.py                                                    (update: exclusive selection on press/move)
│               └── text_item.py                                                      (update: exclusive selection on press/move)
└── tests/
    └── ui/
        └── test_text_annotation.py                                                   (update & add multi-object independence regression tests)
```

---

## 5. Acceptance Criteria

- [x] In **Text** mode, **double-clicking** on the canvas starts a new `DraftTextGraphicsItem` at that position (a single click on empty canvas does not start a new draft).
- [x] While typing in a `DraftTextGraphicsItem`, **one single click outside** the draft object validates and saves the text as a committed `TextObject` / `TextGraphicsItem` on the image (and pressing `Enter` also commits).
- [x] Committed text objects remain freely draggable/movable anywhere on the canvas.
- [x] When 2 or more objects (texts and/or strokes) exist on the canvas, dragging any one object moves **only** that single object while all other objects remain at their exact coordinates.
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
   - Run `.venv\Scripts\finecut.exe`, capture a crop, select **Text**, double-click to type `"Text 1"`, single-click outside to save it, double-click elsewhere to type `"Text 2"`, single-click outside to save it, and drag `"Text 1"` and `"Text 2"` individually to confirm each moves completely independently.

---

## 7. Definition of Done

- All Acceptance Criteria verified and passing.
- Related untracked files staged on `develop`.
- Reviewed and approved by stakeholder before committing.
