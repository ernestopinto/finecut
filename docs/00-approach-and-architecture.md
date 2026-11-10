# Finecut — Technical Approach & Architecture

## 1. Product Vision

**Finecut** is a lightweight Windows desktop application inspired by Windows Snipping Tool (*Ferramenta de Recorte*, reference: `docs/image1.jpg`), purpose-built for **rapid interface blueprinting**.

Instead of a full-blown image editor, Finecut optimizes the shortest path from screen capture to annotated UI sketch:
1. Crop a rectangular region of any running application on screen.
2. Immediately annotate directly over that crop using minimal, purposeful tools.
3. Copy to clipboard or save cleanly for sharing in specs, tickets, or chats.

---

## 2. Core Functional Requirements (MVP + Evolution)

### MVP Scope
- **Screen Crop**: Trigger a new crop (`+ Novo`), select a rectangular region on screen, and immediately open it as the base canvas image.
- **Freehand Drawing Tool**:
  - Draw freely on top of the cropped base image.
  - Restricted by design to **2 colors only**: **Red** and **Blue** (KIS).
  - Each completed stroke is stored as an **independent movable object**: after creation, the user **double-clicks** the stroke to enter move/drag state and reposition it.
- **Text Tool**:
  - Add text annotations directly on the canvas.
  - Restricted by design to **4 classic fonts**: `Arial`, `Times New Roman`, `Book Antiqua`, and `Courier` (resolved cleanly on Windows via `Courier New` / `Courier`).
  - Pressing **`Enter`** commits the text as an **independent movable object** that can be freely dragged/repositioned afterward.
- **Multi-Object Composition**:
  - The base cropped screenshot supports `n` independent drawing and text objects layered on top of it.

### Future Evolution (Layer System)
- **Photoshop-like Layers**: Named layers, layer panel UI, visibility toggles, lock toggles, z-order rearrangement, and layer grouping.
- To support this **without rewriting the MVP**, the internal document model will separate the immutable base crop from an ordered stack of annotation objects/layers from Phase 0 onward.

---

## 3. Technology Stack (Python + Windows `.exe`)

| Concern | Choice | Rationale (KIS + Maintainability) |
| :--- | :--- | :--- |
| **Language** | Python 3.14 (3.11+ compatible) | Requested core language; strong typing support (`typing`, `dataclasses`, `Protocol`). |
| **GUI & Interactive Canvas** | **PySide6** (Qt 6 for Python) | Native `QGraphicsScene` / `QGraphicsView` provides object hit-testing, selection, z-ordering, double-click handling, drag-to-move, crisp font rendering, clipboard export, and HiDPI support out of the box. LGPL licensing is clean for commercial/closed/open `.exe` distribution. |
| **Screen Capture** | Qt `QScreen` + `mss` / `Pillow` (validated in Phase 1) | Reliable multi-monitor and mixed-DPI capture on Windows. |
| **Testing** | `pytest` + `pytest-qt` | Standard Python testing with headless/widget testing for Qt scenes and pure unit testing for domain logic. |
| **Linting & Typing** | `ruff` + `mypy` | Fast linting/formatting and strict static type checking. |
| **Executable Bundling** | **PyInstaller** (`--onedir`) | Bundles Python + PySide6 into `Finecut.exe` with fast startup (avoids `--onefile` temp extraction delay). |
| **Windows Installer** | **Inno Setup** (`ISCC.exe`) | Produces a standard Windows `FinecutSetup-x.y.z.exe` installer with Start Menu entry, optional desktop shortcut, and clean uninstaller. |

---

## 4. Software Architecture (SOLID + KIS)

Finecut follows a clean layered architecture using a `src/` layout so domain rules stay completely decoupled from Qt widgets and Windows OS APIs:

```text
src/finecut/
├── main.py               # Composition root & application bootstrap
├── domain/               # Pure Python models, value objects, and port interfaces (no Qt imports)
│   ├── models.py         # StrokeColor, FontChoice, Point, StrokeObject, TextObject, Layer, CanvasDocument
│   └── ports.py          # Protocols: ScreenCapturer, ImageExporter, ClipboardPort
├── application/          # Use cases & orchestration (document state, object creation, undo/redo)
├── infrastructure/       # Concrete adapters (Windows screen capture, Qt clipboard, PNG file exporter)
└── ui/                   # PySide6 presentation only (MainWindow, Toolbar, SnipOverlay, CanvasScene, QGraphicsItems)
```

### How SOLID Principles Apply
- **Single Responsibility (SRP)**:
  - `domain/` holds data structures and invariants (colors, allowed fonts, object coordinates, layer ordering).
  - `ui/` handles rendering, mouse/keyboard events, and visual feedback only.
  - `infrastructure/` talks to OS screen capture, filesystem, and clipboard.
- **Open/Closed (OCP)**:
  - Canvas objects implement a common abstraction (`CanvasObject` / `BaseCanvasItem`), making future tools (e.g., arrows, rectangles, layer groups) additive rather than requiring edits to existing stroke/text behavior.
- **Liskov Substitution & Interface Segregation (LSP / ISP)**:
  - Small focused `Protocol` interfaces in `ports.py` (`ScreenCapturer`, `ClipboardPort`, `ImageExporter`) keep adapters minimal and easily mockable in tests.
- **Dependency Inversion (DIP)**:
  - `application/` depends on `domain/` protocols, not concrete Qt/Windows implementations. `main.py` wires concrete implementations at startup.

### Photoshop-Ready Data Model (KIS Now, Extensible Later)
Even though MVP displays a single canvas without a Layer sidebar, the domain models a `CanvasDocument` as:
- `base_image`: immutable background screenshot (`BaseImage`)
- `layers`: ordered list of `Layer` objects (MVP uses a default active annotation layer holding `n` `CanvasObject` items with explicit `z_index`).
When Phase 5 introduces a Layer Panel UI, the underlying document model already supports multiple layers, visibility, locking, and z-order stacking.

---

## 5. Agile SCRUM & CI/CD Workflow

Every feature or technical task follows this strict lifecycle:

1. **Plan the Approach**: Clarify scope, architecture impact, and risks.
2. **JIRA Ticket (`.md`)**: Create a structured ticket under `docs/tickets/FC-XXX-<slug>.md`.
3. **Review**: Developer/stakeholder reviews the ticket, acceptance criteria, and file plan.
4. **Approval**: Explicit approval before writing implementation code.
5. **Implementation**: Work exclusively on the **`develop`** branch using small, focused changes.
6. **Test**: Run automated checks (`ruff`, `mypy`, `pytest`) plus manual Windows GUI verification where applicable.
7. **Commit & Push**: Commit with clear reference to `FC-XXX` and push to `develop`.
8. **Release / Deploy**: Merge `develop` -> `main` to trigger automated CI build, PyInstaller `.exe` packaging, Inno Setup installer generation, and release artifact publishing.
