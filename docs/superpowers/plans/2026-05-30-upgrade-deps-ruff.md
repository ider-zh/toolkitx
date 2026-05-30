# Upgrade Dependencies and Add Ruff Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade project dependencies, integrate Ruff for linting and formatting, and fix all existing linting issues.

**Architecture:** Use `uv` for dependency management, `ruff` for linting and formatting, and update `makefile` to provide a consistent interface for these tasks.

**Tech Stack:** Python, uv, ruff, make

---

### Task 1: Add and Configure Ruff

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: Add ruff to dev dependencies in pyproject.toml**

```toml
[project.optional-dependencies]
dev = [
    "pytest>=9.0.2",
    "pytest-dotenv>=0.5.2",
    "ruff>=0.9.0",
]
```

- [ ] **Step 2: Add ruff configuration to pyproject.toml**

```toml
[tool.ruff]
# Target Python version
target-version = "py312"
line-length = 88

[tool.ruff.lint]
# Enable Pyflakes (`F`) and a subset of the pycodestyle (`E`)  codes by default.
# Also enable isort (`I`) and some others.
select = ["E4", "E7", "E9", "F", "I", "N", "B", "UP", "PL"]
ignore = []

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
```

- [ ] **Step 3: Update lockfile**

Run: `uv lock`

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "chore: add and configure ruff"
```

### Task 2: Update Makefile

**Files:**
- Modify: `makefile`

- [ ] **Step 1: Add lint and fix targets to makefile**

```makefile
update:
	uv lock

test_translator:
	uv run --env-file .env  python toolkitx/lab/translator.py 

lint:
	uv run ruff check .

format:
	uv run ruff format .

fix:
	uv run ruff check . --fix
```

- [ ] **Step 2: Commit**

```bash
git add makefile
git commit -m "chore: add lint and format targets to makefile"
```

### Task 3: Fix Linting Warnings

**Files:**
- Modify: All files identified by `ruff check`

- [ ] **Step 1: Run ruff check to identify warnings**

Run: `uv run ruff check .`

- [ ] **Step 2: Apply automatic fixes**

Run: `uv run ruff check . --fix`

- [ ] **Step 3: Manually fix remaining warnings**

Review output of `uv run ruff check .` and fix each file.

- [ ] **Step 4: Verify all warnings are resolved**

Run: `uv run ruff check .`
Expected: "All checks passed!"

- [ ] **Step 5: Run formatting**

Run: `uv run ruff format .`

- [ ] **Step 6: Commit**

```bash
git add .
git commit -m "style: fix linting warnings and format code"
```
