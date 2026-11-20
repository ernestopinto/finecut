# [FC-002] Domain Core Models, `CanvasDocument` Foundation & Capture Ports

| Field | Value |
| :--- | :--- |
| **Ticket ID** | `FC-002` |
| **Type** | Feature / Domain Foundation |
| **Epic / Phase** | Phase 1 — Screen Capture ("Novo Recorte") |
| **Methodology** | Agile SCRUM (Sprint 1) |
| **Status** | `DONE` (Committed on `develop`; all automated checks passed) |
| **Target Branch** | `develop` |
| **Priority** | High (Foundation for `FC-003` capture and `FC-004`/`FC-005` annotation tools) |

---

## 1. Objective

Implement the pure-Python **Domain Layer** (`src/finecut/domain/`) defining Finecut's core value objects, strict constraints (2 drawing colors, 4 text fonts), movable annotation objects (`StrokeObject`, `TextObject`), Photoshop-ready `Layer` and `CanvasDocument` aggregates, and the `ScreenCapturer` port protocol—completely decoupled from `PySide6` and Windows OS APIs.

---

## 2. Scope

### In Scope
1. **Strict Enumerations & Value Objects (`src/finecut/domain/models.py`)**:
   - `StrokeColor(StrEnum)`: Restricted strictly to **2 colors**:
     - `RED = "#E53935"`
     - `BLUE = "#1E88E5"`
   - `FontFamily(StrEnum)`: Restricted strictly to **4 fonts**:
     - `ARIAL = "Arial"`
     - `TIMES_NEW_ROMAN = "Times New Roman"`
     - `BOOK_ANTIQUA = "Book Antiqua"`
     - `COURIER = "Courier"`
   - `Point`: Immutable `(x: float, y: float)` coordinate pair with `translated(dx, dy)` helper.
   - `Rect`: Immutable `(x: int, y: int, width: int, height: int)` screen region with validation (`width > 0` and `height > 0`).
   - `BaseImage`: Immutable cropped base image representation (`width: int`, `height: int`, `png_bytes: bytes`, `device_pixel_ratio: float = 1.0`) validating positive dimensions and non-empty payload.
2. **Movable Canvas Objects (`src/finecut/domain/models.py`)**:
   - `StrokeObject`: Independent freehand drawing object (`id: str`, `points: tuple[Point, ...]`, `color: StrokeColor`, `stroke_width: float = 3.0`, `position: Point = Point(0.0, 0.0)`, `z_index: int = 0`) with `moved_to(new_position: Point) -> StrokeObject` and validation requiring at least 1 point.
   - `TextObject`: Independent committed text object (`id: str`, `text: str`, `font_family: FontFamily`, `position: Point`, `color: StrokeColor = StrokeColor.RED`, `font_size: int = 16`, `z_index: int = 0`) with `moved_to(new_position: Point) -> TextObject` and validation rejecting empty/whitespace-only text.
   - Type alias `CanvasObject = StrokeObject | TextObject`.
3. **Layer & `CanvasDocument` Aggregate (`src/finecut/domain/models.py`)**:
   - `Layer`: Immutable layer container (`id: str`, `name: str`, `objects: tuple[CanvasObject, ...] = ()`, `visible: bool = True`, `locked: bool = False`).
   - `CanvasDocument`: Holds the immutable `base_image: BaseImage`, `layers: tuple[Layer, ...]`, and `active_layer_id: str`, with pure state-transition methods:
     - `CanvasDocument.from_base_image(base_image: BaseImage) -> CanvasDocument` (creates document with a default `"Layer 1"` annotation layer).
     - `add_object(obj: CanvasObject) -> CanvasDocument` (appends object with auto-assigned next `z_index` onto the active layer; supports `n` drawings/texts).
     - `move_object(object_id: str, new_position: Point) -> CanvasDocument` (updates position of any existing stroke or text object by ID).
     - `remove_object(object_id: str) -> CanvasDocument`.
     - `visible_objects() -> tuple[CanvasObject, ...]` (returns all objects across visible layers ordered by layer stack and `z_index`).
4. **Domain Port Protocols (`src/finecut/domain/ports.py`)**:
   - `ScreenCapturer(Protocol)`:
     - `capture_full_screen() -> BaseImage`
     - `capture_region(region: Rect) -> BaseImage`
5. **Unit Test Suite (`tests/unit/test_domain_models.py`)**:
   - Pure unit tests covering all domain invariants, color/font constraints, adding `n` stroke/text objects, moving objects after creation, removing objects, and verifying zero `PySide6` dependency in `finecut.domain`.

### Out of Scope (Deferred to Next Tickets)
- Actual Windows screen capture adapter & `+ Novo` snipping overlay UI (`FC-003`).
- `QGraphicsScene` interactive drawing and text editing items (`FC-004`, `FC-005`).

---

## 3. Technical Design & Architecture Notes (KIS + SOLID)

- **Single Responsibility & Dependency Inversion**:
  - `src/finecut/domain/` imports only from Python's standard library (`dataclasses`, `enum`, `typing`, `uuid`).
  - No `PySide6` widgets or Windows capture libraries are imported in `domain/`.
- **Immutability (`@dataclass(frozen=True, slots=True)`)**:
  - Domain value objects and entities are immutable. Operations like `add_object` and `move_object` return a new `CanvasDocument` snapshot, which will also make Undo/Redo (`FC-007`) trivial to implement later.
- **KIS Principle**:
  - MVP operates transparently on the default active layer created by `CanvasDocument.from_base_image(...)`, while the `layers: tuple[Layer, ...]` structure already supports Phase 5's Photoshop-style Layer Panel without any breaking model changes.

---

## 4. Planned Files to Create / Update

```text
finecut/
├── docs/
│   └── tickets/
│       └── FC-002-domain-core-models-and-canvas-document.md  (new)
├── src/
│   └── finecut/
│       └── domain/
│           ├── __init__.py                                   (update exports)
│           ├── models.py                                     (new)
│           └── ports.py                                      (new)
└── tests/
    └── unit/
        ├── __init__.py                                       (new)
        └── test_domain_models.py                             (new)
```

---

## 5. Acceptance Criteria

- [x] `StrokeColor` exposes strictly 2 colors (`RED`, `BLUE`) and `FontFamily` exposes strictly 4 fonts (`ARIAL`, `TIMES_NEW_ROMAN`, `BOOK_ANTIQUA`, `COURIER`).
- [x] `Rect`, `BaseImage`, `StrokeObject`, and `TextObject` validate their invariants on construction (rejecting non-positive dimensions, empty stroke point tuples, or blank text).
- [x] `CanvasDocument.from_base_image(...)` supports adding `n` `StrokeObject` and `TextObject` instances, moving any object by ID (`move_object`), and removing objects by ID (`remove_object`).
- [x] `src/finecut/domain/` contains zero `PySide6` imports.
- [x] `ruff check src tests` and `ruff format --check src tests` pass with `0` errors.
- [x] `mypy src tests` passes with `0` errors under `strict = true`.
- [x] `pytest -v` passes all unit and UI tests.

---

## 6. Verification Plan (Post-Implementation)

1. Verify active branch: `git branch --show-current` -> `develop`.
2. Run static quality gates:
   - `.venv\Scripts\ruff.exe check src tests`
   - `.venv\Scripts\ruff.exe format --check src tests`
   - `.venv\Scripts\mypy.exe src tests`
3. Run automated test suite:
   - `.venv\Scripts\pytest.exe -v`

---

## 7. Definition of Done

- All Acceptance Criteria verified and passing.
- Related untracked files staged on `develop`.
- Reviewed and approved by stakeholder before committing.
