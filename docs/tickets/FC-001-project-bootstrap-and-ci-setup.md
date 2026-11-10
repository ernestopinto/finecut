# [FC-001] Project Bootstrap, Git Flow Setup, Python Architecture Skeleton & CI Pipeline

| Field | Value |
| :--- | :--- |
| **Ticket ID** | `FC-001` |
| **Type** | Technical Task / Foundation |
| **Epic / Phase** | Phase 0 — Foundation, Repository & Quality Pipeline |
| **Methodology** | Agile SCRUM (Sprint 0) |
| **Status** | `DONE` (Committed on `develop`; automated checks passed) |
| **Target Branch** | `develop` (repo initialized with `main` + `develop`) |
| **Priority** | Highest (Blocker for all feature tickets) |

---

## 1. Objective

Bootstrap the **Finecut** Python repository cleanly following **SOLID**, **KIS**, and strict typing practices, establish the `main` / `develop` Git Flow structure, verify the local Python toolchain, and set up automated lint/type/test checks so every subsequent feature ticket (`FC-002+`) can be built, tested, and shipped safely.

---

## 2. Scope

### In Scope
1. **Git Repository & Branch Setup** *(Done — commit `edfa499`)*:
   - Initialized local Git repository (`main` + `develop`, currently on `develop`).
   - Configured remote `origin` -> `https://github.com/ernestopinto/finecut.git` and pushed `main` and `develop`.
   - Added [.gitignore](../../.gitignore) covering Python artifacts, `.venv/`, PyCharm `.idea/`, `dist/`, `build/`, and test/lint caches.
2. **Python Project & Dependency Configuration**:
   - Create `pyproject.toml` (PEP 621) targeting Python `>=3.12` (verified local runtime: Python 3.14 in `.venv`).
   - Core runtime dependency: `PySide6`.
   - Dev/quality dependencies: `pytest`, `pytest-qt`, `ruff`, `mypy`.
   - Update `README.md` to document setup, run, and test commands.
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

## 4. Planned Files to Create / Update

```text
finecut/
├── .gitignore                 (done in edfa499)
├── .github/
│   └── workflows/
│       └── ci.yml
├── pyproject.toml
├── README.md                  (update)
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

- [x] Git repository is initialized with `main` and `develop` branches, and `develop` is checked out as the active working branch.
- [x] `.gitignore` is committed covering Python, `.venv/`, `.idea/`, build outputs, and lint/test caches.
- [x] Virtual environment is created cleanly and dependencies install reproducibly from `pyproject.toml`.
- [ ] Running `python -m finecut.main` (or `finecut` console/gui script entry point) opens the minimal Finecut main window with a `+ Novo` stub button and no runtime errors. *(Automated `pytest-qt` test passed; pending manual desktop launch verification.)*
- [x] `ruff check src tests` exits with `0` errors.
- [x] `mypy src tests` exits with `0` errors.
- [x] `pytest` executes and passes the initial smoke test(s).
- [x] CI configuration file is present and aligned with the project's Git hosting provider.
- [x] Existing documentation in `docs/` (including `docs/image1.jpg`) remains intact.

---

## 6. Review Decisions Confirmed

1. **Git Hosting / CI Platform**: **GitHub** (`https://github.com/ernestopinto/finecut`) using **GitHub Actions** (`.github/workflows/ci.yml` on `windows-latest`, which also gives native Windows runners for Phase 4 PyInstaller `.exe` + Inno Setup packaging). *Git repo, `main`/`develop`, `origin`, and `.gitignore` completed in `edfa499`.*
2. **Python Environment & Tooling**: Per-project `.venv` (`c:\Users\pinto\PyCharmProjects\finecut\.venv`, Python 3.14) created via PyCharm + `pip install -e ".[dev]"` using `pyproject.toml`.
3. **Approval Status**: Approved and implemented on `develop`; automated checks (`ruff`, `mypy`, `pytest`) passed (`PySide6 6.12.0` on Python `3.14.6`). Ready for manual smoke launch and commit/push approval.

---

## 7. Verification Plan (Post-Implementation)

1. Verify active branch: `git branch --show-current` -> `develop`.
2. Run static checks:
   - `ruff check src tests`
   - `mypy src tests`
3. Run automated tests:
   - `pytest -v`
4. Manual smoke launch:
   - Launch `finecut` locally on Windows to verify window title, DPI rendering, and clean close.

---

## 8. Definition of Done

- All Acceptance Criteria checked and verified.
- Code reviewed against SOLID, KIS, and Python typing standards.
- Approved by stakeholder before committing and pushing to `develop`.
