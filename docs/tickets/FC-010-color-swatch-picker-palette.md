# [FC-010] Square Color Swatch Picker (20-Color Palette) & Icon-Based Draw/Text Toolbar Buttons

| Field | Value |
| :--- | :--- |
| **Ticket ID** | `FC-010` |
| **Type** | Feature / UX Enhancement |
| **Epic / Phase** | Phase 3 — Blueprint Output & Essential Editing Polish |
| **Methodology** | Agile SCRUM (Sprint 3) |
| **Status** | `DONE` (Committed on `develop`; all automated checks passed) |
| **Target Branch** | `develop` |
| **Priority** | High (Pre-Phase 4 UX Polish) |

---

## 1. Objective

Polish the annotation toolbar before Phase 4 packaging:
1. Replace the three text-based color buttons (`Red`, `Blue`, `Black`) with a **traditional square color swatch picker**:
   - Display a **square active-color indicator button** (with an outer selection frame) directly in the top toolbar so the toolbar stays compact and distraction-free.
   - Clicking the active-color swatch opens a **popover grid of 20 classic square color swatches** (2 rows × 10 columns).
   - Selecting any swatch immediately updates the active drawing & text color, updates the toolbar's active-color square, and closes the popover.
2. Replace the text labels on the **Draw** and **Text** tool buttons with crisp vector icons:
   - **Brush icon** for **Draw** (`create_brush_icon()`).
   - **Paper / Sheet icon** for **Text** (`create_paper_sheet_icon()`).

---

## 2. Scope

### In Scope
1. **Expand `StrokeColor(StrEnum)` to Classic 20-Color Palette (`src/finecut/domain/models.py`)**:
   - Preserve existing enum members `RED = "#E53935"`, `BLUE = "#1E88E5"`, and `BLACK = "#000000"` for full backwards compatibility.
   - Define the 20 classic Paint-style colors in 2×10 visual order:
     - **Row 1 (Primary / Vivid):** `BLACK` (`#000000`), `GRAY` (`#7F7F7F`), `DARK_RED` (`#880015`), `RED` (`#E53935`), `ORANGE` (`#FF7F27`), `YELLOW` (`#FFF200`), `GREEN` (`#22B14C`), `TURQUOISE` (`#00A2E8`), `BLUE` (`#1E88E5`), `PURPLE` (`#A349A4`).
     - **Row 2 (Light / Pastel):** `WHITE` (`#FFFFFF`), `LIGHT_GRAY` (`#C3C3C3`), `BROWN` (`#B97A57`), `ROSE` (`#FFAEC9`), `GOLD` (`#FFC90E`), `LIGHT_YELLOW` (`#EFE4B0`), `LIME` (`#B5E61D`), `LIGHT_TURQUOISE` (`#99D9EA`), `BLUE_GRAY` (`#7092BE`), `LAVENDER` (`#C8BFE7`).
   - Add a `display_name` property on `StrokeColor` (e.g., `"Dark Red"`, `"Light Yellow"`) for clean tooltips.
2. **Circular Color Swatch Picker Widget (`src/finecut/ui/color_swatch_picker.py`)**:
   - `ColorSwatchButton(QPushButton)`:
     - Custom `paintEvent` drawing a crisp anti-aliased circular color fill with a subtle gray outline (ensuring `White` and light pastels stay clearly visible).
     - When checked/active, renders a distinct outer blue selection ring matching the reference design.
     - Displays a readable tooltip (`"<Color Name> (<#HEX>)"`).
   - `ColorSwatchPopover(QFrame)`:
     - Lightweight `Qt.WindowType.Popup` frame displaying all 20 `ColorSwatchButton` items in a clean **2 rows × 10 columns** `QGridLayout`.
     - Highlights the currently selected `StrokeColor`.
     - Emits `color_selected(StrokeColor)` and automatically closes when a swatch is clicked (or when clicking outside / pressing `Esc`).
   - `ColorSwatchPicker(QPushButton)`:
     - Circular active-color trigger button placed directly in the top toolbar with an outer blue ring and inner filled circle reflecting the active `StrokeColor`.
     - Clicking opens `ColorSwatchPopover` anchored neatly beneath the button.
     - Exposes `active_color`, `set_color(color: StrokeColor)`, `popover`, and `swatch_buttons` for clean programmatic control and testing.
3. **Main Window Toolbar Integration (`src/finecut/ui/main_window.py`)**:
   - Replace `red_color_button`, `blue_color_button`, `black_color_button`, and `_color_button_group` with `self.color_swatch_picker = ColorSwatchPicker(initial_color=StrokeColor.RED, parent=self)`.
   - Connect `color_swatch_picker.color_selected` to `self.set_stroke_color`.
   - Keep `set_stroke_color(color: StrokeColor)` synchronizing `DocumentController`, `BlueprintCanvasScene`, and `ColorSwatchPicker`.
4. **Documentation & Automated Tests**:
   - Update `docs/00-approach-and-architecture.md` and `docs/01-development-phases.md` to reflect the 20-color swatch palette and updated Phase 4 ticket numbering (`FC-011`, `FC-012`, Phase 5 `FC-013`).
   - Update `tests/unit/test_domain_models.py` for the 20 `StrokeColor` values and `display_name`.
   - Update `tests/ui/test_freehand_drawing.py` and `tests/ui/test_text_annotation.py` to select colors via `color_swatch_picker`.
   - Add `tests/ui/test_color_swatch_picker.py` testing:
     - Active swatch button displays the default color (`StrokeColor.RED`) and updates when changed.
     - Clicking the toolbar swatch button opens the 2×10 popover containing all 20 `StrokeColor` swatches.
     - Clicking any swatch in the popover updates `DocumentController.active_color`, `BlueprintCanvasScene.active_color`, and `color_swatch_picker.active_color`, and closes the popover.
     - Newly drawn strokes and committed text objects use the newly selected swatch color (e.g., `StrokeColor.GREEN`, `StrokeColor.PURPLE`, `StrokeColor.ORANGE`).

### Out of Scope
- Custom RGB/HSV color wheel or user-defined custom swatch slots (empty third row from Paint is intentionally omitted to stay KIS).
- Secondary/background color slot (Finecut only annotates with a single active foreground color).

---

## 3. Technical Design & Architecture Notes (KIS + SOLID)

- **Single Responsibility (SRP)**:
  - `src/finecut/ui/color_swatch_picker.py` owns all circular swatch painting, popover positioning, and swatch grid interaction, keeping `FinecutMainWindow` focused on top-level toolbar wiring.
- **Open/Closed Principle (OCP)**:
  - `ColorSwatchPopover` iterates dynamically over `StrokeColor` enum members rather than hardcoding button attributes per color.
- **Domain Purity**:
  - `StrokeColor` remains a pure-Python `StrEnum` in `src/finecut/domain/models.py` with zero `PySide6` imports.

---

## 4. Planned Files to Create / Update

```text
finecut/
├── docs/
│   ├── 00-approach-and-architecture.md                 (update color spec)
│   ├── 01-development-phases.md                        (add FC-010, renumber Phase 4/5)
│   └── tickets/
│       └── FC-010-color-swatch-picker-palette.md       (new)
├── src/
│   └── finecut/
│       ├── domain/
│       │   └── models.py                               (update: expand StrokeColor to 20 colors + display_name)
│       └── ui/
│           ├── __init__.py                             (update exports)
│           ├── color_swatch_picker.py                  (new: ColorSwatchButton, ColorSwatchPopover, ColorSwatchPicker)
│           └── main_window.py                          (update: replace Red/Blue/Black buttons with ColorSwatchPicker)
└── tests/
    ├── unit/
    │   └── test_domain_models.py                       (update: 20 colors + display_name)
    └── ui/
        ├── test_color_swatch_picker.py                 (new)
        ├── test_freehand_drawing.py                    (update: use color_swatch_picker)
        └── test_text_annotation.py                     (update: use color_swatch_picker)
```

---

## 5. Acceptance Criteria

- [x] `StrokeColor` defines all 20 classic swatch colors (preserving `RED`, `BLUE`, `BLACK`) with `display_name` and zero `PySide6` imports.
- [x] Top toolbar displays a single circular active-color swatch button with an outer selection ring instead of text buttons (`Red`, `Blue`, `Black`).
- [x] Clicking the toolbar swatch button opens a popover displaying all 20 circular color swatches in a 2×10 grid with the active color clearly indicated.
- [x] Selecting any color in the popover closes the popover, updates the toolbar active-color circle, and applies that color to subsequent freehand strokes and text annotations.
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
   - Run `.venv\Scripts\finecut.exe`, click the circular active color swatch in the toolbar, verify the 2×10 popover renders crisply (including light colors like White/Yellow with subtle borders), pick several colors, and verify both Draw strokes and Text annotations render in the chosen colors.

---

## 7. Definition of Done

- All Acceptance Criteria verified and passing.
- Related untracked files staged on `develop`.
- Reviewed and approved by stakeholder before committing.
