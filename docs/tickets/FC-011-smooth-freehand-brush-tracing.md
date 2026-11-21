# [FC-011] Smooth Freehand Brush Tracing (Anti-Jitter Filtering & Quadratic Bezier Curve Rendering)

| Field | Value |
| :--- | :--- |
| **Ticket ID** | `FC-011` |
| **Type** | Polish / UX Enhancement |
| **Epic / Phase** | Phase 3 — Blueprint Output & Essential Editing Polish |
| **Methodology** | Agile SCRUM (Sprint 3) |
| **Status** | `DONE` (Committed on `develop`; all automated checks passed) |
| **Target Branch** | `develop` |
| **Priority** | High (Pre-Phase 4 UX Polish) |

---

## 1. Objective

Eliminate the jagged, pixelated/staircase appearance of freehand brush strokes so both live drawing previews and committed `StrokeGraphicsItem` objects render as crisp, fluid, anti-aliased curves (matching modern Windows ink / Paint / Snipping Tool brush feel).

---

## 2. Root Cause Analysis

Inspecting `src/finecut/ui/canvas_scene.py` and `src/finecut/ui/items/stroke_item.py` revealed three causes of the jagged/staircase trace:
1. **Unfiltered 1 px integer mouse jitter**: `BlueprintCanvasScene.mouseMoveEvent` records every raw mouse event coordinate without minimum-distance sampling, capturing 1 px horizontal/vertical pixel-grid steps on diagonal drags.
2. **Sharp polyline rendering (`lineTo`)**: `build_painter_path()` connects consecutive points with straight `QPainterPath.lineTo(...)` segments, faithfully amplifying every 1 px mouse step into visible sawtooth edges.
3. **No curve/point smoothing**: Neither the live preview nor committed stroke points apply midpoint quadratic Bezier interpolation or lightweight neighbor smoothing.

---

## 3. Scope

### In Scope
1. **Minimum-Distance Input Sampling (`src/finecut/ui/canvas_scene.py`)**:
   - Add `MIN_POINT_SAMPLE_DISTANCE_PX = 3.0` so `mouseMoveEvent` ignores sub-threshold 1 px staircase jitter while still capturing tight curves accurately.
   - Always retain the exact start point (`mousePressEvent`) and end point (`mouseReleaseEvent`) so short or fast strokes never lose their endpoints.
2. **Smooth Curve Path Builder (`src/finecut/ui/items/stroke_item.py`)**:
   - Add a pure helper `smooth_points(points: tuple[Point, ...]) -> tuple[Point, ...]` applying a gentle weighted neighbor pass (`0.25 * prev + 0.5 * curr + 0.25 * next`, keeping the exact first and last points intact) when `len(points) >= 3`.
   - Upgrade `build_painter_path(points: tuple[Point, ...]) -> QPainterPath` to render smooth **midpoint quadratic Bezier curves** (`path.quadTo(control_point, midpoint)`) instead of raw straight `lineTo` polylines:
     - `1` point: tiny dot segment so single-point paths remain valid.
     - `2` points: single crisp `lineTo`.
     - `3+` points: `moveTo(p0)`, quadratic Bezier segments through consecutive midpoints (`quadTo(p[i], mid(p[i], p[i+1]))`), finishing smoothly at `p[-1]`.
   - Explicitly set `painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)` in `StrokeGraphicsItem.paint(...)` for consistent sub-pixel quality across live canvas and flattened exports.
3. **Unit & UI Tests (`tests/ui/test_freehand_drawing.py`)**:
   - Verify `build_painter_path` generates quadratic Bezier curve elements (`QPainterPath.ElementType.CurveToElement`) for multi-point strokes (3+ points) while preserving exact start and end coordinates.
   - Verify `smooth_points` reduces diagonal staircase jitter while keeping endpoints unchanged.
   - Verify existing freehand drawing, double-click-to-move, undo/redo, and flatten/export tests continue to pass without regressions.

### Out of Scope
- Variable-width pressure-sensitive calligraphy brushes or brush thickness sliders (KIS).

---

## 4. Technical Design & Architecture Notes (KIS + SOLID)

- **Single Responsibility (SRP)**:
  - Curve smoothing and `QPainterPath` generation stay encapsulated in `src/finecut/ui/items/stroke_item.py` (`smooth_points`, `build_painter_path`), shared by both the live preview stroke and committed `StrokeGraphicsItem`.
- **Zero Domain Breaking Changes**:
  - `StrokeObject` still stores `points: tuple[Point, ...]` in pure Python; smoothing happens cleanly at capture/path-building time without changing the domain contract.

---

## 5. Planned Files to Create / Update

```text
finecut/
├── docs/
│   ├── 01-development-phases.md                        (add FC-011, renumber Phase 4/5)
│   └── tickets/
│       └── FC-011-smooth-freehand-brush-tracing.md     (new)
├── src/
│   └── finecut/
│       └── ui/
│           ├── canvas_scene.py                         (update: min-distance point sampling)
│           └── items/
│               └── stroke_item.py                      (update: smooth_points, quadTo Bezier path, antialiasing)
└── tests/
    └── ui/
        └── test_freehand_drawing.py                    (update: add curve smoothing & Bezier path tests)
```

---

## 6. Acceptance Criteria

- [x] Diagonal and curved freehand strokes render as smooth, anti-aliased Bezier curves without visible 1 px staircase/sawtooth jitter during both live preview and committed display.
- [x] Start and end points of every stroke remain accurate and unchanged.
- [x] Double-click-to-move, hit-testing, Undo/Redo, Clipboard Copy, and PNG/JPG Export continue to work seamlessly with smoothed strokes.
- [x] `ruff check src tests` and `ruff format --check src tests` pass with `0` errors.
- [x] `mypy src tests` passes with `0` errors under `strict = true`.
- [x] `pytest -v` passes all unit and UI tests (including under `QT_QPA_PLATFORM=offscreen`).

---

## 7. Verification Plan (Post-Implementation)

1. Verify active branch: `git branch --show-current` -> `develop`.
2. Run static checks:
   - `.venv\Scripts\ruff.exe check src tests`
   - `.venv\Scripts\ruff.exe format --check src tests`
   - `.venv\Scripts\mypy.exe src tests`
3. Run automated test suite (offscreen CI mode):
   - `$env:QT_QPA_PLATFORM='offscreen'; .venv\Scripts\pytest.exe -v`
4. Manual desktop check:
   - Launch `.venv\Scripts\finecut.exe`, capture a crop, draw diagonal and curved freehand lines with the Brush tool, and confirm the trace is smooth like the reference image both on canvas and after `Ctrl+C` / `Ctrl+S`.

---

## 8. Definition of Done

- All Acceptance Criteria verified and passing.
- Related untracked files staged on `develop`.
- Reviewed and approved by stakeholder before committing.
