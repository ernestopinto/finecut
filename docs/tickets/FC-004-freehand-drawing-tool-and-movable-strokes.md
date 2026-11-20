# [FC-004] Freehand Drawing Tool (Red/Blue/Black) & Double-Click-to-Move Stroke Objects

| Field | Value |
| :--- | :--- |
| **Ticket ID** | `FC-004` |
| **Type** | Feature / Story |
| **Epic / Phase** | Phase 2 — Core Annotation Objects (Freehand Draw & Text) |
| **Methodology** | Agile SCRUM (Sprint 2) |
| **Status** | `DONE` (Committed on `develop`; all automated checks passed) |
| **Target Branch** | `develop` |
| **Priority** | High |

---

## 1. Objective

Enable users to draw freely on top of a captured base image in **strictly 3 colors (`Red`, `Blue`, and `Black`)**, store each completed drawing as an independent `StrokeObject` (supporting `n` drawings on the canvas), and allow the user to **double-click** any completed drawing object to activate move mode and drag/reposition it anywhere over the crop.

---

## 2. Scope

### In Scope
1. **Domain & Application Layer Extensions (`src/finecut/domain/models.py`, `src/finecut/application/document_controller.py`)**:
   - Extend `StrokeColor(StrEnum)` to support **3 colors**: `RED = "#E53935"`, `BLUE = "#1E88E5"`, and `BLACK = "#000000"`.
   - Track `active_color: StrokeColor` in `DocumentController` (default `StrokeColor.RED`, switchable between `StrokeColor.RED`, `StrokeColor.BLUE`, and `StrokeColor.BLACK`).
   - `add_stroke(points: Sequence[Point], color: StrokeColor | None = None, stroke_width: float = 3.0) -> StrokeObject`:
     - Validates an active `CanvasDocument` exists, creates a `StrokeObject` with a unique ID, appends it to the active layer in `CanvasDocument` with auto-incremented `z_index`, and returns the stored `StrokeObject`.
   - `move_object(object_id: str, new_position: Point) -> CanvasDocument`:
     - Updates the stored position of the target object in `CanvasDocument`.
2. **Movable Stroke Scene Item (`src/finecut/ui/items/stroke_item.py`)**:
   - Create `StrokeGraphicsItem(QGraphicsPathItem)`:
     - Renders a `StrokeObject` using a smooth rounded `QPen` in `StrokeColor.RED` (`#E53935`), `StrokeColor.BLUE` (`#1E88E5`), or `StrokeColor.BLACK` (`#000000`).
     - Uses a forgiving hit-test stroke width (`12px` via `QPainterPathStroker` in `shape()`) so thin freehand lines are easy to double-click and grab.
     - **Double-Click-to-Move Lifecycle**:
       - Starts with `is_move_enabled == False` after creation so drawing new overlapping strokes does not accidentally drag existing strokes.
       - On **`mouseDoubleClickEvent`**: enables move mode (`ItemIsMovable`, `ItemIsSelectable`), selects the item, changes cursor to `Qt.CursorShape.SizeAllCursor`, and shows a dashed selection bounding box.
       - While in move mode, dragging the item moves it across the canvas; releasing the mouse emits/notifies the new `Point(x, y)` offset so `DocumentController.move_object(...)` stays synchronized.
       - Clicking empty canvas or starting a new stroke deselects the item and exits move mode (`is_move_enabled = False`) until double-clicked again.
3. **Interactive Freehand Drawing in `BlueprintCanvasScene` (`src/finecut/ui/canvas_scene.py`)**:
   - Support drawing `n` freehand strokes when a base image is loaded and the user left-drags on the canvas (outside of an active move-enabled item).
   - Render a live preview stroke while dragging; on mouse release, commit the collected `Point` sequence into a `StrokeObject` and add its `StrokeGraphicsItem` at the assigned `z_index`.
   - Rebuild/render existing `StrokeObject` items whenever `set_document(document)` is called.
4. **Toolbar Color & Draw Controls (`src/finecut/ui/main_window.py`)**:
   - Add checkable **Red**, **Blue**, and **Black** color buttons in the top toolbar (`Red` selected by default) wired to `DocumentController.set_active_color(...)` and `BlueprintCanvasScene`.
5. **Automated Unit & UI Tests**:
   - `tests/unit/test_domain_models.py` & `tests/unit/test_document_controller.py`: unit tests for 3 `StrokeColor` options (`RED`, `BLUE`, `BLACK`), `active_color`, `add_stroke` (`n` strokes), and `move_object`.
   - `tests/ui/test_freehand_drawing.py`: `pytest-qt` tests verifying:
     - Toolbar Red/Blue/Black color switching.
     - Freehand mouse drag on the canvas creates independent `StrokeGraphicsItem` instances (`n` drawings over the base image).
     - Single-clicking/dragging over an unselected stroke draws a new stroke without moving the old one.
     - **Double-clicking** a `StrokeGraphicsItem` activates move mode and dragging it updates both its scene position and its `StrokeObject.position` in `CanvasDocument`.

### Out of Scope (Deferred to Next Tickets)
- Text annotation tool in 4 fonts and `Enter`-to-commit movable text objects (`FC-005`).
- Clipboard copy / PNG file export (`FC-006`) and Undo/Redo / Delete (`FC-007`).

---

## 3. Technical Design & Architecture Notes (KIS + SOLID)

- **Single Responsibility (SRP)**:
  - `StrokeObject` (in `domain/`) stores pure geometry, color, offset position, and `z_index`.
  - `DocumentController` (in `application/`) manages document state mutations.
  - `StrokeGraphicsItem` (in `ui/items/`) encapsulates Qt path rendering, hit-testing padding, double-click move activation, and drag-release notifications.
- **Open/Closed Principle (OCP)**:
  - Placing scene items under `src/finecut/ui/items/` prepares a clean home for `TextGraphicsItem` in `FC-005` without bloating `canvas_scene.py`.
- **KIS Principle**:
  - Strictly three toolbar color buttons (**Red**, **Blue**, and **Black**) with clear active state; no color picker dialogs or brush sliders.

---

## 4. Planned Files to Create / Update

```text
finecut/
├── docs/
│   └── tickets/
│       └── FC-004-freehand-drawing-tool-and-movable-strokes.md  (new)
├── src/
│   └── finecut/
│       ├── domain/
│       │   └── models.py                                        (update: add StrokeColor.BLACK)
│       ├── application/
│       │   └── document_controller.py                           (update: active_color, add_stroke, move_object)
│       └── ui/
│           ├── __init__.py                                      (update exports)
│           ├── canvas_scene.py                                  (update: freehand drawing & item sync)
│           ├── main_window.py                                   (update: Red/Blue/Black toolbar buttons & wiring)
│           └── items/
│               ├── __init__.py                                  (new)
│               └── stroke_item.py                               (new)
└── tests/
    ├── ui/
    │   └── test_freehand_drawing.py                             (new)
    └── unit/
        ├── test_document_controller.py                          (update)
        └── test_domain_models.py                                (update)
```

---

## 5. Acceptance Criteria

- [x] Toolbar provides strictly **3 drawing colors**: **Red** (`#E53935`, default), **Blue** (`#1E88E5`), and **Black** (`#000000`).
- [x] Dragging with the left mouse button on a loaded base crop draws a live freehand stroke and commits an independent `StrokeObject` / `StrokeGraphicsItem` on mouse release.
- [x] The canvas supports `n` independent freehand drawings layered on top of the base image.
- [x] Double-clicking a completed drawing activates move mode on that `StrokeGraphicsItem`, allowing the user to drag it to a new position and persisting the new `Point` offset in `CanvasDocument`.
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
   - Run `.venv\Scripts\finecut.exe`, capture a screen crop (`+ Novo`), draw multiple Red, Blue, and Black strokes, double-click a stroke, and drag it to a new position.

---

## 7. Definition of Done

- All Acceptance Criteria verified and passing.
- Related untracked files staged on `develop`.
- Reviewed and approved by stakeholder before committing.
