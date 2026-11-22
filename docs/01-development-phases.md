# Finecut — Development Phases & SCRUM Roadmap

Each phase delivers a testable, usable increment. Features are broken into JIRA-style `.md` tickets in `docs/tickets/` and implemented sequentially on `develop` following the `Plan -> Ticket -> Review -> Approval -> Implementation -> Test -> Commit & Push` cycle.

> **Current Status & Next Step:**
> - **Completed:** Phase 0 / `FC-001` (`a156bf5`), Phase 1 / `FC-002` (`59a23e3`), Phase 1 / `FC-003` (`56e909e`), Phase 2 / `FC-004` (`104d36b`), Phase 2 / `FC-005` (`ef27947`, `4f88e14`), Phase 3 / `FC-006` (`b5d959d`), Phase 3 / `FC-007` (`c6c0193`), Phase 3 / `FC-008` (`a3a5997`), Phase 3 / `FC-009` (`5430dfe`), Phase 3 / `FC-010` (`bd4393d`), Phase 3 / `FC-011` (`cbd49a7`), and Phase 4 / `FC-012` (Windows GUI Launcher `Finecut.exe`, Dev Launcher & Inno Setup Installer).
> - **Next Up (Phase 4):** Write ticket **`FC-013`** — *Automated Release Pipeline on Merge to `main`*.

---

## Phase 0 — Foundation, Repository & Quality Pipeline *(Completed)*
**Goal:** Establish a clean Python project skeleton, Git Flow branches (`main` and `develop`), quality gates, and automated CI checks.

- **Deliverables:**
  - Git repository initialized with `main` (release) and `develop` (active development) branches.
  - `pyproject.toml`, `.gitignore`, and `src/finecut/` SOLID package skeleton (`domain`, `application`, `infrastructure`, `ui`).
  - Minimal launchable PySide6 window (inspired by `docs/image1.jpg` simplicity).
  - Configured quality tools: `ruff` (lint/format), `mypy` (strict type checking), `pytest` + `pytest-qt`.
  - Baseline CI workflow running lint, typecheck, and tests on pushes/PRs to `develop` and `main`.
- **Planned Ticket(s):**
  - [x] `FC-001`: Project Bootstrap, Git Flow Setup, Python Architecture Skeleton & CI Pipeline (`DONE` — `a156bf5`).
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
  - [x] `FC-002`: Domain Core Models & `CanvasDocument` Foundation (`DONE` — `59a23e3`).
  - [x] `FC-003`: Windows Screen Crop Overlay (`+ Novo`) & Base Image Loading (`DONE`).
- **Exit Criteria:** User can crop any window/screen area on single or multi-monitor Windows setups and immediately see the crisp crop inside Finecut.

---

## Phase 2 — Core Annotation Objects (Freehand Draw & Text)
**Goal:** Enable quick UI blueprinting with movable freehand drawings and movable text objects over the base image.

- **Deliverables:**
  - **Freehand Draw Tool**:
    - Restricted to **3 colors only**: **Red**, **Blue**, and **Black**.
    - Completed stroke automatically becomes an independent `StrokeObject` on the scene.
    - **Double-click** behavior on a stroke object toggles/activates move mode so the user can drag and reposition that drawing anywhere over the base crop.
  - **Text Tool**:
    - Restricted to **4 fonts**: `Arial`, `Times New Roman`, `Book Antiqua`, and `Courier` (`Courier New` resolution on Windows).
    - Click canvas to type inline; pressing **`Enter`** commits the text as an independent `TextObject`.
    - Committed text objects can be dragged/moved freely over the base image.
  - Support for **`n` independent objects** (any mix of strokes and texts) over the single base crop.
- **Planned Ticket(s):**
  - [x] `FC-004`: Freehand Drawing Tool (Red/Blue/Black) & Double-Click-to-Move Stroke Objects (`DONE` — `104d36b`).
  - [x] `FC-005`: Text Annotation Tool (4 Fonts, Enter-to-Commit) & Movable Text Objects (`DONE`).
- **Exit Criteria:** User can capture an app screen, draw multiple Red/Blue/Black strokes, double-click any stroke to move it, add multiple text boxes in the 4 fonts, commit with `Enter`, and drag them into position.

---

## Phase 3 — Blueprint Output & Essential Editing Polish
**Goal:** Make Finecut immediately practical for daily engineering/design blueprinting.

- **Deliverables:**
  - **Copy to Clipboard** (`Ctrl+C` / toolbar button): flattens base image + all annotation objects into a crisp bitmap on the Windows clipboard.
  - **Export / Save Image** (`Ctrl+S` / toolbar button): export flattened PNG/JPEG to disk.
  - **Essential Editing**: Delete selected object (`Del` / `Backspace`), Undo/Redo stack (`Ctrl+Z` / `Ctrl+Y`), clear tool mode (`Esc`), clean visual selection indicator when moving objects.
  - Toolbar visual polish matching the clean, distraction-free Windows 11 *Ferramenta de Recorte* aesthetic (`docs/image1.jpg`).
- **Planned Ticket(s):**
  - [x] `FC-006`: Flatten & Export (Clipboard Copy + Save PNG/JPG) (`DONE` — `b5d959d`).
  - [x] `FC-007`: Object Deletion & Undo/Redo Command History (`DONE` — `c6c0193`).
  - [x] `FC-008`: Fix Text Creation Mechanics (Double-Click to Add, Single-Click Outside to Commit) & Independent Single-Object Movement Bug (`DONE` — `a3a5997`).
  - [x] `FC-009`: Minimize App to Top Floating Action Strip with "Cancel Selection" Button During Screen Capture (`DONE` — `5430dfe`).
  - [x] `FC-010`: Square Color Swatch Picker (20-Color Palette) & Icon-Based Draw/Text Toolbar Buttons (`DONE` — `bd4393d`).
  - [x] `FC-011`: Smooth Freehand Brush Tracing, Uniform Toolbar Icons & Auto-Fit Canvas Sizing (`DONE`).
- **Exit Criteria:** Full end-to-end daily workflow (`+ Novo` -> floating top action strip / drag crop -> draw/text/move -> `Ctrl+C` paste into Jira/Slack/Teams or `Ctrl+S` to PNG) works smoothly with independent single-object movement.

---

## Phase 4 — Windows Launcher, Installer & Automated Release Pipeline
**Goal:** Deliver Finecut as a standalone Windows GUI launcher (`Finecut.exe`) with a proper Windows setup installer (`FinecutSetup.exe`), automated on merges to `main`.

- **Deliverables:**
  - **Windows Launcher (`Finecut.exe` & Dev Launcher)**:
    - Windowed GUI executable (`console=False`, no terminal popup) with custom Finecut `.ico` icon and Windows version metadata via PyInstaller `--onedir`.
    - Local one-click launcher script (`run_finecut.bat`) for launching Finecut directly from Windows Explorer during development without opening a terminal.
  - **Windows Installer (`FinecutSetup-<version>.exe`)**:
    - Inno Setup (`packaging/installer.iss`) wizard installing Finecut, creating the **Start Menu launcher**, optional **Desktop shortcut launcher**, **"Launch Finecut"** finish action, and standard Windows Settings uninstaller.
  - **Automated Release CI/CD Pipeline**:
    - Triggered when `develop` is merged into `main`: runs full test suite -> builds `Finecut.exe` launcher bundle -> compiles `FinecutSetup-<version>.exe` installer -> attaches installer to tagged GitHub release/artifact.
- **Planned Ticket(s):**
  - [x] `FC-012`: Windows GUI Launcher (`Finecut.exe`), Dev Launcher & Inno Setup Windows Installer (`FinecutSetup.exe`) (`DONE`).
  - `FC-013`: Automated Release Pipeline on Merge to `main`.
- **Exit Criteria:** Clean Windows machine can run `FinecutSetup.exe`, launch Finecut directly from the Desktop or Start Menu launcher icon without Python installed, annotate a crop, and uninstall cleanly.

---

## Phase 5 — Photoshop-like Layer System & Future Enhancements
**Goal:** Evolve Finecut from flat object stacking into an explicit layer-managed blueprinting tool without breaking MVP simplicity.

- **Deliverables:**
  - Collapsible **Layers Panel** (Background/Base Crop layer + named annotation layers).
  - Create, rename, reorder (z-index), toggle visibility (show/hide), and lock/unlock layers.
  - Assign new strokes/texts to the active layer or move objects across layers.
  - Optional future backlog (prioritized post-MVP): global Windows capture shortcut, basic geometric blueprint primitives (box/arrow), save/reopen editable `.finecut` project files.
- **Planned Ticket(s):**
  - `FC-014`: Layer Panel UI, Visibility/Lock Controls & Z-Order Reordering.
