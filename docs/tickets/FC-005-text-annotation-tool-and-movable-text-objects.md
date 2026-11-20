# [FC-005] Text Annotation Tool (4 Fonts, Enter-to-Commit) & Movable Text Objects

| Field | Value |
| :--- | :--- |
| **Ticket ID** | `FC-005` |
| **Type** | Feature / Story |
| **Epic / Phase** | Phase 2 — Core Annotation Objects (Freehand Draw & Text) |
| **Methodology** | Agile SCRUM (Sprint 2) |
| **Status** | `DONE` (Committed on `develop`; all automated checks passed) |
| **Target Branch** | `develop` |
| **Priority** | High (Completes Phase 2 Core Annotation Objects) |

---

## 1. Objective

Enable users to switch to a **Text Tool**, click anywhere on a captured base crop to type text in **strictly 4 popular fonts (`Arial`, `Times New Roman`, `Book Antiqua`, `Courier`)**, commit the text by pressing **`Enter`** so it becomes an independent `TextObject`, and freely drag/move committed text objects anywhere over the base image (supporting `n` drawings and texts on the same crop).

---

## 2. Scope

### In Scope
1. **Domain & Application Layer Extensions (`src/finecut/domain/models.py`, `src/finecut/application/document_controller.py`)**:
   - Add `CanvasTool(StrEnum)` (`DRAW = "draw"`, `TEXT = "text"`) to `finecut.domain.models`.
   - Track `active_tool: CanvasTool` (default `CanvasTool.DRAW`) and `active_font: FontFamily` (default `FontFamily.ARIAL`) in `DocumentController`.
   - Add `add_text(text: str, position: Point, font_family: FontFamily | None = None, color: StrokeColor | None = None, font_size: int = 16) -> TextObject`:
     - Validates an active `CanvasDocument` exists, creates a `TextObject` with a unique ID (`f"text-{uuid4().hex[:8]}"`), appends it to the active layer in `CanvasDocument` with auto-incremented `z_index`, and returns the stored `TextObject`.
2. **Movable Text Scene Item & Inline Editor (`src/finecut/ui/items/text_item.py`)**:
   - Create `TextGraphicsItem(QGraphicsTextItem)`:
     - Renders a committed `TextObject` using its `FontFamily` (`Arial`, `Times New Roman`, `Book Antiqua`, or `Courier` resolved cleanly on Windows) and `StrokeColor` (`Red`, `Blue`, or `Black`).
     - Committed `TextGraphicsItem` is immediately movable (`ItemIsMovable`, `ItemIsSelectable`, `SizeAllCursor`) after creation with `Enter`; dragging and releasing updates its position in `DocumentController.move_object(...)`.
   - Create `DraftTextGraphicsItem(QGraphicsTextItem)` (or editing mode on `TextGraphicsItem`):
     - Opened when the user clicks the canvas in `CanvasTool.TEXT` mode.
     - Receives keyboard focus (`TextEditorInteraction`) with a visible dashed input border.
     - Pressing **`Enter` / `Return`** commits non-empty text (emitting the committed string and `Point` position) and replaces the draft editor with a committed movable `TextGraphicsItem`.
     - Pressing **`Esc`** (or pressing `Enter` on blank/whitespace text) cancels and removes the draft editor cleanly.
3. **Canvas Scene Integration (`src/finecut/ui/canvas_scene.py`)**:
   - Support switching between `CanvasTool.DRAW` and `CanvasTool.TEXT`, and updating `active_font: FontFamily`.
   - In `CanvasTool.TEXT` mode:
     - Clicking an existing committed `TextGraphicsItem` drags/moves that text object directly.
     - Clicking empty/background canvas spawns the inline draft text editor at that position.
   - Maintain `text_items: dict[str, TextGraphicsItem]` alongside `stroke_items`, supporting `n` mixed drawings and text objects over the base image.
   - Rebuild both `StrokeObject` and `TextObject` items in `z_index` order on `set_document(document)`.
4. **Toolbar Tool Mode & Font Selector (`src/finecut/ui/main_window.py`)**:
   - Add mutually exclusive **Draw** and **Text** tool mode buttons in the top toolbar (`Draw` selected by default).
   - Add a **Font selector dropdown (`QComboBox`)** with strictly the **4 fonts**:
     - `Arial`
     - `Times New Roman`
     - `Book Antiqua`
     - `Courier`
   - Wire tool mode, font selector, and existing color buttons (`Red`, `Blue`, `Black`) across `DocumentController` and `BlueprintCanvasScene`.
5. **Automated Unit & UI Tests**:
   - `tests/unit/test_document_controller.py`: unit tests for `active_tool`, `active_font`, `add_text` across the 4 fonts, mixed `n` strokes + texts, and moving text objects.
   - `tests/ui/test_text_annotation.py`: `pytest-qt` tests verifying:
     - Switching between **Draw** and **Text** tools and selecting any of the **4 fonts** (`Arial`, `Times New Roman`, `Book Antiqua`, `Courier`).
     - Clicking the canvas in `Text` mode, typing text, and pressing **`Enter`** creates an independent committed `TextGraphicsItem` and `TextObject`.
     - Dragging a committed `TextGraphicsItem` moves it and updates `TextObject.position` in `CanvasDocument`.
     - Creating `n` mixed drawings and text objects on top of the same base crop.

### Out of Scope (Deferred to Phase 3)
- Flatten & export to Windows Clipboard (`Ctrl+C`) and Save PNG/JPG (`Ctrl+S`) (`FC-006`).
- Object deletion (`Del`) and Undo/Redo command history (`FC-007`).

---

## 3. Technical Design & Architecture Notes (KIS + SOLID)

- **Single Responsibility (SRP)**:
  - `TextObject` (in `domain/`) holds immutable text content, `FontFamily`, `StrokeColor`, `Point` position, and `z_index`.
  - `TextGraphicsItem` / `DraftTextGraphicsItem` (in `ui/items/text_item.py`) handles Qt font resolution, `Enter`-key interception, and drag-move position callbacks.
- **Open/Closed Principle (OCP)**:
  - Adding `text_item.py` under `src/finecut/ui/items/` extends scene items without modifying `StrokeGraphicsItem`.
- **KIS Principle**:
  - Pressing `Enter` immediately commits the text object so it is ready to drag/reposition—no modal text dialog popups.

---

## 4. Planned Files to Create / Update

```text
finecut/
├── docs/
│   └── tickets/
│       └── FC-005-text-annotation-tool-and-movable-text-objects.md  (new)
├── src/
│   └── finecut/
│       ├── domain/
│       │   ├── __init__.py                                          (update exports)
│       │   └── models.py                                            (update: add CanvasTool)
│       ├── application/
│       │   └── document_controller.py                               (update: active_tool, active_font, add_text)
│       └── ui/
│           ├── __init__.py                                          (update exports)
│           ├── canvas_scene.py                                      (update: text tool & text_items)
│           ├── main_window.py                                       (update: Draw/Text toggle & 4-font QComboBox)
│           └── items/
│               ├── __init__.py                                      (update exports)
│               └── text_item.py                                     (new)
└── tests/
    ├── ui/
    │   └── test_text_annotation.py                                  (new)
    └── unit/
        └── test_document_controller.py                              (update)
```

---

## 5. Acceptance Criteria

- [x] Toolbar provides a **Draw / Text** tool toggle and a font selector restricted strictly to the **4 fonts**: `Arial`, `Times New Roman`, `Book Antiqua`, and `Courier`.
- [x] In **Text** mode, clicking on the loaded crop opens an inline text input at the clicked coordinate; typing and pressing **`Enter`** commits it as an independent `TextObject` / `TextGraphicsItem`.
- [x] Once created with **`Enter`**, each text object can be dragged/moved freely across the canvas and updates its `Point` position in `CanvasDocument`.
- [x] The canvas supports `n` mixed drawings (`StrokeObject`) and texts (`TextObject`) layered on top of the base image.
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
   - Run `.venv\Scripts\finecut.exe`, capture a screen crop (`+ Novo`), switch to **Text**, test all 4 fonts, press **`Enter`** to commit each text, and drag the text objects around the canvas alongside freehand drawings.

---

## 7. Definition of Done

- All Acceptance Criteria verified and passing.
- Related untracked files staged on `develop`.
- Reviewed and approved by stakeholder before committing.
