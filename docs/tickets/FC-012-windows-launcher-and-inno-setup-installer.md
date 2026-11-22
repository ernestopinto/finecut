# [FC-012] Windows GUI Launcher (`Finecut.exe`), Dev Launcher & Inno Setup Installer (`FinecutSetup.exe`)

| Field | Value |
| :--- | :--- |
| **Ticket ID** | `FC-012` |
| **Type** | Feature / Packaging & Distribution |
| **Epic / Phase** | Phase 4 — Windows Launcher, Installer & Automated Release Pipeline |
| **Methodology** | Agile SCRUM (Sprint 4) |
| **Status** | `DONE` (Committed on `develop`) |
| **Target Branch** | `develop` |
| **Priority** | High (Enables standalone Windows `.exe` & installer distribution) |

---

## 1. Objective

Package **Finecut** as a native, standalone Windows desktop application (`Finecut.exe`) with zero Python prerequisite for end users, a one-click local developer launcher (`run_finecut.bat`), and a standard Windows installation wizard (`FinecutSetup-<version>.exe` via **Inno Setup**) with Start Menu launcher, optional Desktop shortcut, post-install launch checkbox, and clean Windows Settings uninstaller.

---

## 2. Scope

### In Scope
1. **Custom Finecut Application Icon & Window/Taskbar Branding**:
   - Create `packaging/generate_icon.py` to generate a crisp multi-resolution Windows `.ico` file (`packaging/assets/finecut.ico` containing 16, 32, 48, 64, 128, and 256 px PNG-encoded frames) matching Finecut's dashed crop marquee + annotation accent aesthetic.
   - Add `create_app_icon()` in `src/finecut/ui/toolbar_icons.py` and wire `app.setWindowIcon(...)` + `app.setApplicationVersion(__version__)` in `src/finecut/main.py` so the Windows title bar and taskbar display the Finecut icon both from source and from `Finecut.exe`.
2. **PyInstaller `--onedir` Windowed Build Configuration (`packaging/finecut.spec`, `packaging/version_info.txt`)**:
   - Add an optional `[project.optional-dependencies] build = ["pyinstaller>=6.11"]` group to `pyproject.toml` (keeping runtime dependencies untouched).
   - Create `packaging/finecut.spec` configured with:
     - `console=False` (windowed GUI app — zero console terminal window flash).
     - `--onedir` bundle outputting `dist/Finecut/Finecut.exe` (fast startup compared to `--onefile` self-extraction).
     - Embedded `packaging/assets/finecut.ico` and Windows file version metadata (`packaging/version_info.txt` populated with product name, version `0.0.1`, description).
     - Excludes unnecessary heavy Qt modules (e.g., `QtWebEngine`, `Qt3D`, `QtQml`, `QtQuick`) to keep installer size lean.
3. **One-Click Local Dev Launcher (`run_finecut.bat`)**:
   - Add `run_finecut.bat` at the repository root using `.venv\Scripts\pythonw.exe -m finecut.main` (detached via `start ""`) so developers can double-click it from Windows Explorer without leaving an open console window.
4. **Inno Setup Windows Installer Script (`packaging/installer.iss`) & Build Helper (`packaging/build_windows.ps1`)**:
   - Create `packaging/installer.iss`:
     - Installs `dist/Finecut/*` to `{autopf}\Finecut` (supporting per-user or admin install cleanly via `PrivilegesRequiredOverridesAllowed=dialog`).
     - Creates **Start Menu** shortcut (`Finecut`) and optional **Desktop** shortcut (unchecked or checked by user choice in wizard).
     - Adds **"Launch Finecut"** checkbox on the installer Finish page.
     - Registers clean uninstall metadata in Windows Settings -> Installed Apps.
     - Outputs `dist/installer/FinecutSetup-<AppVersion>.exe` using `/DAppVersion=<version>` (defaulting to `0.0.1`).
   - Create `packaging/build_windows.ps1`:
     - Reproducible local & CI build script: regenerates icon if missing -> runs PyInstaller -> runs Inno Setup (`ISCC.exe`) if installed (with clear guidance if `ISCC.exe` is not yet installed locally).
5. **Documentation & Automated Packaging Tests**:
   - Update `README.md` with local dev launcher (`run_finecut.bat`) and Windows build/installer instructions.
   - Add `tests/unit/test_packaging_config.py` verifying:
     - `packaging/assets/finecut.ico` exists and has a valid ICO header with multiple resolutions.
     - `packaging/finecut.spec`, `packaging/installer.iss`, `packaging/version_info.txt`, and `run_finecut.bat` exist and match `finecut.__version__`.
     - `create_app_icon()` returns a non-null `QIcon`.

### Out of Scope (Deferred to Next Ticket)
- Automated GitHub Actions release pipeline triggered on merges to `main` (`FC-013`).
- Code signing certificate / EV Authenticode signing (future post-MVP consideration).

---

## 3. Technical Design & Architecture Notes (KIS + SOLID)

- **Zero Runtime Dependency Bloat**:
  - `pyinstaller` lives strictly under `[project.optional-dependencies].build` in `pyproject.toml`, keeping production runtime dependencies limited to `PySide6`.
- **`--onedir` + Inno Setup over `--onefile`**:
  - `--onedir` launches near-instantly (no temp-folder extraction delay on every launch) and triggers far fewer false-positive antivirus flags on Windows, while Inno Setup wraps the folder cleanly into a single `FinecutSetup-<version>.exe` installer for end users.
- **Single Source of Truth for Version**:
  - `packaging/build_windows.ps1` reads `__version__` from `src/finecut/__init__.py` and passes it to Inno Setup (`/DAppVersion=...`), keeping `pyproject.toml`, `__init__.py`, and installer filenames aligned.

---

## 4. Planned Files to Create / Update

```text
finecut/
├── docs/
│   ├── 01-development-phases.md                             (update status)
│   └── tickets/
│       └── FC-012-windows-launcher-and-inno-setup-installer.md (new)
├── packaging/
│   ├── assets/
│   │   └── finecut.ico                                      (new: multi-res icon)
│   ├── build_windows.ps1                                    (new: reproducible Windows build script)
│   ├── finecut.spec                                         (new: PyInstaller --onedir spec)
│   ├── generate_icon.py                                     (new: deterministic .ico generator)
│   ├── installer.iss                                        (new: Inno Setup wizard script)
│   └── version_info.txt                                     (new: Windows EXE version metadata)
├── pyproject.toml                                           (update: add optional [build] extra with pyinstaller)
├── README.md                                                (update: document launcher & build commands)
├── run_finecut.bat                                          (new: one-click Explorer dev launcher)
├── src/
│   └── finecut/
│       ├── main.py                                          (update: set app icon & version)
│       └── ui/
│           └── toolbar_icons.py                             (update: add create_app_icon)
└── tests/
    └── unit/
        └── test_packaging_config.py                         (new: packaging & icon verification tests)
```

---

## 5. Risks & Dependencies to Approve

- **New Optional Build Dependency:** Adds `pyinstaller>=6.11` under `[project.optional-dependencies].build` in `pyproject.toml` (not installed by default runtime users; installed locally via `.venv\Scripts\pip install -e ".[dev,build]"`).
- **Local Inno Setup (`ISCC.exe`):** Not currently detected on this machine (`C:\Program Files (x86)\Inno Setup 6\ISCC.exe` absent). We can either install it locally (`winget install JRSoftware.InnoSetup`) to build & test `FinecutSetup-0.1.0.exe` right now, or verify `Finecut.exe` locally and let GitHub Actions `windows-latest` (which has Inno Setup preinstalled) compile `FinecutSetup.exe` in `FC-013`.

---

## 6. Acceptance Criteria

- [x] `packaging/assets/finecut.ico` exists with multi-resolution frames, and `FinecutMainWindow` displays the Finecut icon in the title bar and Windows taskbar.
- [x] Double-clicking `run_finecut.bat` launches Finecut directly without leaving an open console window.
- [x] Running PyInstaller with `packaging/finecut.spec` produces a working windowed `dist/Finecut/Finecut.exe` that launches cleanly with no terminal flash and captures/annotates/exports screenshots.
- [x] `packaging/installer.iss` compiles cleanly with Inno Setup (`ISCC.exe`) into `dist/installer/FinecutSetup-0.0.1.exe` with Start Menu shortcut, optional Desktop shortcut, post-install launch option, and clean uninstaller.
- [x] `ruff check src tests` and `ruff format --check src tests` pass with `0` errors.
- [x] `mypy src tests` passes with `0` errors under `strict = true`.
- [x] `pytest -v` passes all unit and UI tests (including `test_packaging_config.py`).

---

## 7. Verification Plan (Post-Implementation)

1. Verify active branch: `git branch --show-current` -> `develop`.
2. Run static checks & test suite:
   - `.venv\Scripts\ruff.exe check src tests`
   - `.venv\Scripts\ruff.exe format --check src tests`
   - `.venv\Scripts\mypy.exe src tests`
   - `$env:QT_QPA_PLATFORM='offscreen'; .venv\Scripts\pytest.exe -v`
3. Build & test `Finecut.exe` locally:
   - `.\packaging\build_windows.ps1`
   - Launch `dist\Finecut\Finecut.exe` and verify icon, no console window, screen capture, brush/text, and copy/save.
4. Test `run_finecut.bat` from Windows Explorer.

---

## 8. Definition of Done

- All Acceptance Criteria verified and passing.
- Related untracked files staged on `develop`.
- Reviewed and approved by stakeholder before committing.
