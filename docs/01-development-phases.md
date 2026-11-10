# Finecut — Development Phases & SCRUM Roadmap

Each phase delivers a testable, usable increment. Features are broken into JIRA-style `.md` tickets in `docs/tickets/` and implemented sequentially on `develop` following the `Plan -> Ticket -> Review -> Approval -> Implementation -> Test -> Commit & Push` cycle.

---

## Phase 0 — Foundation, Repository & Quality Pipeline
**Goal:** Establish a clean Python project skeleton, Git Flow branches (`main` and `develop`), quality gates, and automated CI checks.

- **Deliverables:**
  - Git repository initialized with `main` (release) and `develop` (active development) branches.
  - `pyproject.toml`, `.gitignore`, and `src/finecut/` SOLID package skeleton (`domain`, `application`, `infrastructure`, `ui`).
  - Minimal launchable PySide6 window (inspired by `docs/image1.jpg` simplicity).
  - Configured quality tools: `ruff` (lint/format), `mypy` (strict type checking), `pytest` + `pytest-qt`.
  - Baseline CI workflow running lint, typecheck, and tests on pushes/PRs to `develop` and `main`.
- **Planned Ticket(s):**
  - `FC-001`: Project Bootstrap, Git Flow Setup, Python Architecture Skeleton & CI Pipeline.
- **Exit Criteria:** Application launches cleanly from source; `ruff`, `mypy`, and `pytest` pass locally and in CI.

---

## Phase 1 — Screen Capture ("Novo Recorte")
**Goal:** Capture any rectangular region of the Windows desktop quickly and load it as the canvas base image.

- **Deliverables:**
  - Domain models (`BaseImage`, `Rect`, `CanvasDocument`) and `ScreenCapturer` protocol.
  - `+ Novo` action in toolbar (`Ctrl+N`) that hides/minimizes Finecut briefly, captures the screen, and opens a full-screen selection overlay.
  - Drag-and-release rectangular crop with live dimension/selection feedback and `Esc` to cancel.
  - Multi-monitor & Windows HiDPI scaling support.
  - Cropped image immediately renders as the base image on the editing canvas.
- **Planned Ticket(s):**
  - `FC-002`: Domain Core Models & `CanvasDocument` Foundation.
  - `FC-003`: Windows Screen Crop Overlay (`+ Novo`) & Base Image Loading.
- **Exit Criteria:** User can crop any window/screen area on single or multi-monitor Windows setups and immediately see the crisp crop inside Finecut.

---

## Phase 2 — Core Annotation Objects (Freehand Draw & Text)
**Goal:** Enable quick UI blueprinting with movable freehand drawings and movable text objects over the base image.

- **Deliverables:**
  - **Freehand Draw Tool**:
    - Restricted to **2 colors only**: **Red** and **Blue**.
    - Completed stroke automatically becomes an independent `StrokeObject` on the scene.
    - **Double-click** behavior on a stroke object toggles/activates move mode so the user can drag and reposition that drawing anywhere over the base crop.
  - **Text Tool**:
    - Restricted to **4 fonts**: `Arial`, `Times New Roman`, `Book Antiqua`, and `Courier` (`Courier New` resolution on Windows).
    - Click canvas to type inline; pressing **`Enter`** commits the text as an independent `TextObject`.
    - Committed text objects can be dragged/moved freely over the base image.
  - Support for **`n` independent objects** (any mix of strokes and texts) over the single base crop.
- **Planned Ticket(s):**
  - `FC-004`: Freehand Drawing Tool (Red/Blue) & Double-Click-to-Move Stroke Objects.
  - `FC-005`: Text Annotation Tool (4 Fonts, Enter-to-Commit) & Movable Text Objects.
- **Exit Criteria:** User can capture an app screen, draw multiple Red/Blue strokes, double-click any stroke to move it, add multiple text boxes in the 4 fonts, commit with `Enter`, and drag them into position.

---

## Phase 3 — Blueprint Output & Essential Editing Polish
**Goal:** Make Finecut immediately practical for daily engineering/design blueprinting.

- **Deliverables:**
  - **Copy to Clipboard** (`Ctrl+C` / toolbar button): flattens base image + all annotation objects into a crisp bitmap on the Windows clipboard.
  - **Export / Save Image** (`Ctrl+S` / toolbar button): export flattened PNG/JPEG to disk.
  - **Essential Editing**: Delete selected object (`Del` / `Backspace`), Undo/Redo stack (`Ctrl+Z` / `Ctrl+Y`), clear tool mode (`Esc`), clean visual selection indicator when moving objects.
  - Toolbar visual polish matching the clean, distraction-free Windows 11 *Ferramenta de Recorte* aesthetic (`docs/image1.jpg`).
- **Planned Ticket(s):**
  - `FC-006`: Flatten & Export (Clipboard Copy + Save PNG/JPG).
  - `FC-007`: Object Deletion & Undo/Redo Command History.
- **Exit Criteria:** Full end-to-end daily workflow (`+ Novo` -> draw/text/move -> `Ctrl+C` paste into Jira/Slack/Teams or `Ctrl+S` to PNG) works smoothly.

---

## Phase 4 — Windows Packaging & Automated Release Pipeline
**Goal:** Deliver Finecut as a standalone Windows `.exe` with a proper installer, automated on merges to `main`.

- **Deliverables:**
  - Application icon, Windows version metadata, and PyInstaller `--onedir` spec producing `Finecut.exe`.
  - Inno Setup (`.iss`) script generating `FinecutSetup-<version>.exe` (Start Menu entry, optional desktop shortcut, proper uninstaller in Windows Settings).
  - Automated deploy CI/CD pipeline triggered when `develop` is merged into `main`: runs full test suite -> builds `Finecut.exe` -> builds `FinecutSetup.exe` -> attaches installer to tagged release/artifact.
- **Planned Ticket(s):**
  - `FC-008`: PyInstaller `.exe` Build & Inno Setup Windows Installer.
  - `FC-009`: Automated Release Pipeline on Merge to `main`.
- **Exit Criteria:** Clean Windows machine can run `FinecutSetup.exe`, launch Finecut from Start Menu without Python installed, annotate a crop, and uninstall cleanly.

---

## Phase 5 — Photoshop-like Layer System & Future Enhancements
**Goal:** Evolve Finecut from flat object stacking into an explicit layer-managed blueprinting tool without breaking MVP simplicity.

- **Deliverables:**
  - Collapsible **Layers Panel** (Background/Base Crop layer + named annotation layers).
  - Create, rename, reorder (z-index), toggle visibility (show/hide), and lock/unlock layers.
  - Assign new strokes/texts to the active layer or move objects across layers.
  - Optional future backlog (prioritized post-MVP): global Windows capture shortcut, basic geometric blueprint primitives (box/arrow), save/reopen editable `.finecut` project files.
- **Planned Ticket(s):**
  - `FC-010`: Layer Panel UI, Visibility/Lock Controls & Z-Order Reordering.
