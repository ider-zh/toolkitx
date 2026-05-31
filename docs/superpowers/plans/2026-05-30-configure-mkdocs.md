# Configure MkDocs Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Configure MkDocs with Material theme and essential plugins, and create the documentation landing page.

**Architecture:** Standard MkDocs setup with `mkdocs-material`, `mkdocstrings` for API documentation, and `mkdocs-gen-files`/`mkdocs-literate-nav` for automated reference pages.

**Tech Stack:** MkDocs, MkDocs Material, mkdocstrings (python handler), pymdown-extensions.

---

### Task 1: Create `mkdocs.yml`

**Files:**
- Create: `mkdocs.yml`

- [ ] **Step 1: Create `mkdocs.yml` with the specified configuration**

```yaml
site_name: ToolkitX Documentation
site_url: https://github.com/ider-zh/toolkitx
repo_url: https://github.com/ider-zh/toolkitx
edit_uri: edit/main/docs/

theme:
  name: material
  palette:
    - scheme: default
      primary: indigo
      accent: indigo
      toggle:
        icon: material/brightness-7
        name: Switch to dark mode
    - scheme: slate
      primary: indigo
      accent: indigo
      toggle:
        icon: material/brightness-4
        name: Switch to light mode
  features:
    - navigation.tabs
    - navigation.sections
    - navigation.top
    - search.suggest
    - search.highlight
    - content.code.copy

plugins:
  - search
  - gen-files:
      scripts:
        - scripts/gen_ref_pages.py
  - literate-nav:
      nav_file: SUMMARY.md
  - section-index
  - mkdocstrings:
      handlers:
        python:
          paths: [.]
          options:
            docstring_style: google
            show_source: true
            show_root_heading: true
            show_category_heading: true

markdown_extensions:
  - admonition
  - pymdownx.highlight:
      anchor_linenums: true
  - pymdownx.inlinehilite
  - pymdownx.snippets
  - pymdownx.superfences
  - pymdownx.tabbed:
      alternate_style: true
```

### Task 2: Create `docs/index.md`

**Files:**
- Create: `docs/index.md`

- [ ] **Step 1: Create `docs/index.md` with the welcome content**

```markdown
# Welcome to ToolkitX

ToolkitX is a personal Python toolkit for common tasks, focusing on resilience, text processing, and lab tools like translators.

## Modules

- **Task Utils**: Resilience decorators and persistent task queues.
- **Text Utils**: Smart text truncation and word-count based splitting.
- **Lab**: Experimental tools including Baidu and Tencent translators.

## Getting Started

Check the [API Reference](reference/toolkitx/index.md) for detailed documentation of all modules.
```

### Task 3: Verification and Commit

- [ ] **Step 1: Verify files exist**

Run: `ls -l mkdocs.yml docs/index.md`

- [ ] **Step 2: Commit the changes**

Run: `git add mkdocs.yml docs/index.md && git commit -m "chore: configure mkdocs and create index page"`
