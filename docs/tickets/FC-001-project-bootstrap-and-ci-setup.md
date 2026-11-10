# [FC-001] Project Bootstrap, Git Flow Setup, Python Architecture Skeleton & CI Pipeline

| Field | Value |
| :--- | :--- |
| **Ticket ID** | `FC-001` |
| **Type** | Technical Task / Foundation |
| **Epic / Phase** | Phase 0 — Foundation, Repository & Quality Pipeline |
| **Methodology** | Agile SCRUM (Sprint 0) |
| **Status** | `IN REVIEW` (Updated with GitHub repo — awaiting approval) |
| **Target Branch** | `develop` (repo initialized with `main` + `develop`) |
| **Priority** | Highest (Blocker for all feature tickets) |

---

## 1. Objective

Bootstrap the **Finecut** Python repository cleanly following **SOLID**, **KIS**, and strict typing practices, establish the `main` / `develop` Git Flow structure, verify the local Python toolchain, and set up automated lint/type/test checks so every subsequent feature ticket (`FC-002+`) can be built, tested, and shipped safely.

---

## 2. Scope

### In Scope
1. **Git Repository & Branch Setup**:
   - Initialize local Git repository (`main` branch as initial clean baseline, `develop` branch created and checked out for active development).
   - Configure remote `origin` -> `https://github.com/ernestopinto/finecut.git` (pushing only after review/test approval).
   - Add standard `.gitignore` covering Python artifacts, `.venv/`, PyCharm `.idea/` (or project-specific ignores), `dist/`, `build/`, and test/lint caches.
2. **Python Project & Dependency Configuration**:
   - Create `pyproject.toml` (PEP 621) targeting Python `>=3.11` (matching verified local Python runtime).
   - Core runtime dependency: `PySide6`.
   - Dev/quality dependencies: `pytest`, `pytest-qt`, `ruff`, `mypy`.
   - Create `README.md` documenting setup, run, and test commands.
3. **SOLID Package Skeleton (`src/` layout)**:
   - Create minimal, well-bounded package modules under `src/finecut/`:
     - `src/finecut/__init__.py`
     - `src/finecut/main.py` — composition root launching the application
     - `src/finecut/domain/__init__.py`
     - `src/finecut/application/__init__.py`
     - `src/finecut/infrastructure/__init__.py`
     - `src/finecut/ui/__init__.py`
     - `src/finecut/ui/main_window.py` — minimal placeholder main window with `+ Novo` stub button and clean empty-state prompt (matching `docs/image1.jpg` simplicity)
4. **Test & Quality Gate Setup**:
   - Configure `ruff` (linting + formatting rules) and `mypy` (`strict = true` or equivalent strict settings) in `pyproject.toml`.
   - Add initial smoke test `tests/ui/test_main_window.py` verifying `MainWindow` instantiates cleanly without errors via `pytest-qt`.
5. **Baseline CI Pipeline Definition**:
   - Add `.github/workflows/ci.yml` for **GitHub Actions** (`windows-latest` runner) to run `ruff check`, `mypy`, and `pytest` (`QT_QPA_PLATFORM=offscreen`) on pushes/PRs to `develop` and `main`.

### Out of Scope (Deferred to Later Tickets)
- Screen capture implementation (`FC-003`).
- Drawing and text annotation tools (`FC-004`, `FC-005`).
- PyInstaller `.exe` & Inno Setup packaging (`FC-008`, `FC-009`).

---

## 3. Technical Design & Architecture Notes (KIS + SOLID)

- **KIS Principle**: Only build the thin walking skeleton and quality gates. Do not introduce speculative abstractions, plugin systems, or config frameworks before they are needed.
- **Dependency Direction**:
  - `ui` -> `application` -> `domain`
  - `infrastructure` -> `domain`
  - `main.py` wires dependencies at runtime.
  - `domain/` must contain zero `PySide6` imports.
- **Strict Typing**:
  - All functions and methods include explicit parameter and return type annotations.
  - Avoid `Any`; prefer `Protocol` and `dataclass(frozen=True)` for domain definitions.

---

## 4. Planned Files to Create

```text
finecut/
├── .gitignore
├── .github/
│   └── workflows/
│       └── ci.yml
├── pyproject.toml
├── README.md
├── src/
│   └── finecut/
│       ├── __init__.py
│       ├── main.py
│       ├── domain/
│       │   └── __init__.py
│       ├── application/
│       │   └── __init__.py
│       ├── infrastructure/
│       │   └── __init__.py
│       └── ui/
│           ├── __init__.py
│           └── main_window.py
└── tests/
    ├── __init__.py
    └── ui/
        └── test_main_window.py
```

---

## 5. Acceptance Criteria

- [ ] Git repository is initialized with `main` and `develop` branches, and `develop` is checked out as the active working branch.
- [ ] Virtual environment is created cleanly and dependencies install reproducibly from `pyproject.toml`.
- [ ] Running `python -m finecut.main` (or `finecut` console/gui script entry point) opens the minimal Finecut main window with a `+ Novo` stub button and no runtime errors.
- [ ] `ruff check src tests` exits with `0` errors.
- [ ] `mypy src tests` exits with `0` errors.
- [ ] `pytest` executes and passes the initial smoke test(s).
- [ ] CI configuration file is present and aligned with the project's Git hosting provider.
- [ ] Existing documentation in `docs/` (including `docs/image1.jpg`) remains intact.

---

## 6. Review Decisions Confirmed

1. **Git Hosting / CI Platform**: **GitHub** (`https://github.com/ernestopinto/finecut`) using **GitHub Actions** (`.github/workflows/ci.yml` on `windows-latest`, which also gives native Windows runners for Phase 4 PyInstaller `.exe` + Inno Setup packaging).
2. **Python Environment & Tooling**: Per-project `.venv` (`c:\Users\pinto\PyCharmProjects\finecut\.venv`) + `pip install -e ".[dev]"` using `pyproject.toml`.
3. **Approval Status**: Updated per stakeholder feedback; awaiting final approval to implement on `develop`.

---

## 7. Verification Plan (Post-Implementation)

1. Verify active branch: `git branch --show-current` -> `develop`.
2. Run static checks:
   - `ruff check src tests`
   - `mypy src`
3. Run automated tests:
   - `pytest -v`
4. Manual smoke launch:
   - Launch `finecut` locally on Windows to verify window title, DPI rendering, and clean close.

---

## 8. Definition of Done

- All Acceptance Criteria checked and verified.
- Code reviewed against SOLID, KIS, and Python typing standards.
- Approved by stakeholder before committing and pushing to `develop`.
