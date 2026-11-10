# Finecut

Lightweight Windows desktop tool for quick screen cropping and interface blueprinting.

See [docs/](docs/) for architecture, roadmap, and SCRUM tickets:
- [Approach & Architecture](docs/00-approach-and-architecture.md)
- [Development Phases](docs/01-development-phases.md)

## Local Setup (Windows + PyCharm `.venv`)

1. Ensure your project virtual environment exists at `.venv` (Python 3.12+ / 3.14).
2. Install Finecut in editable mode with development tools:

```powershell
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

## Running the App

```powershell
.venv\Scripts\python.exe -m finecut.main
```

Or via the installed GUI script:

```powershell
.venv\Scripts\finecut.exe
```

## Quality Checks

```powershell
.venv\Scripts\ruff.exe check src tests
.venv\Scripts\mypy.exe src tests
.venv\Scripts\pytest.exe -v
```

## Git Workflow

- Active development happens on `develop` via approved tickets in `docs/tickets/`.
- Stable releases merge `develop` into `main`.
