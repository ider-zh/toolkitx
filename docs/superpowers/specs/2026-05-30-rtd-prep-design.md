# Read the Docs Deployment Preparation Design

**Goal:** Configure the project to support automated, high-performance documentation builds on Read the Docs (RTD) using their native `uv` integration.

**Architecture:**
- **Configuration File:** `.readthedocs.yaml` (v2)
- **Dependency Management:** `uv` with `pyproject.toml` and `uv.lock`.
- **Build Tool:** MkDocs (as configured in `mkdocs.yml`).

---

## 1. Build Environment

### 1.1 Operating System
We will use **Ubuntu 24.04** (the latest stable LTS supported by RTD) to ensure compatibility with modern Python tooling.

### 1.2 Python Version
We will stick to **Python 3.12** to match the project's requirements.

### 1.3 Native `uv` Integration
Read the Docs now supports `uv` as an installation method. This is faster and more deterministic than `pip`.
We will use the following installation strategy:
- `method: uv`
- `command: sync`
- `extras: [docs]`

---

## 2. Configuration Details

### 2.1 `.readthedocs.yaml` Structure
```yaml
version: 2

build:
  os: ubuntu-24.04
  tools:
    python: "3.12"

mkdocs:
  configuration: mkdocs.yml

python:
  install:
    - method: uv
      command: sync
      extra:
        - docs
```

### 2.2 Why `uv sync --extra docs`?
- **Full Environment:** `mkdocstrings` requires the actual `toolkitx` package and its dependencies to be installed in the environment to perform static/dynamic analysis of the docstrings.
- **Speed:** `uv` caches layers effectively and installs pre-built wheels whenever possible.

---

## 3. Integration Workflow

1.  **Local Preparation:**
    - Create `.readthedocs.yaml`.
    - Ensure `uv.lock` is up-to-date.
2.  **Commit & Push:**
    - Push changes to GitHub.
3.  **RTD Setup (External):**
    - The user must manually import the project on the Read the Docs dashboard.
    - RTD will automatically use the `.readthedocs.yaml` file for all subsequent builds.

---

## Success Criteria
- [ ] `.readthedocs.yaml` is present in the repository root.
- [ ] The configuration correctly specifies the `docs` extra.
- [ ] Local build via `make docs-build` remains successful.
