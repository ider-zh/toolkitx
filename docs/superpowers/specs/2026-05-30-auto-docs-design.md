# Automated Python API Documentation Design

**Goal:** Establish a zero-maintenance documentation system that automatically generates a modern, searchable API website from Python source code, type hints, and Google-style docstrings.

**Architecture:**
- **Static Site Generator:** MkDocs
- **Theme:** Material for MkDocs (for a modern, responsive UI)
- **API Extraction:** `mkdocstrings[python]` (to parse code and docstrings)
- **Automation Logic:** `mkdocs-gen-files` (to dynamically map the `toolkitx/` package structure to documentation pages)
- **Navigation:** `mkdocs-literate-nav` (to automatically generate sidebar navigation based on folder hierarchy)

**User Experience:**
- Developers write code with Google-style docstrings.
- The documentation website is always in sync with the source code.
- New modules or functions appear automatically in the docs upon build.

---

## 1. Component Details

### 1.1 Configuration (`mkdocs.yml`)
The main configuration file will define the site identity, Material theme settings (color, icons), and the plugin pipeline. It will also enable the search and code-highlighting features.

### 1.2 Automation Script (`scripts/gen_ref_pages.py`)
This script acts as a build hook. It:
1. Iterates through all `.py` files in `toolkitx/` (excluding `__init__.py` if preferred or handling them as index pages).
2. For each module, it creates a virtual Markdown file in the `reference/` directory.
3. It uses the `::: <module_path>` syntax which `mkdocstrings` recognizes to pull in the actual code documentation.

### 1.3 Documentation Standard
We will adopt the **Google Python Style Guide** for docstrings.
Example:
```python
def my_function(param1: int, param2: str) -> bool:
    """Summary line.

    Args:
        param1: Description of param1.
        param2: Description of param2.

    Returns:
        Description of return value.
    """
```

---

## 2. Integration into Workflow

### 2.1 Dependencies
Add the following to `pyproject.toml` dev dependencies:
- `mkdocs`
- `mkdocs-material`
- `mkdocstrings[python]`
- `mkdocs-gen-files`
- `mkdocs-literate-nav`
- `mkdocs-section-index` (for folder-level documentation)

### 2.2 Makefile Targets
- `make docs-serve`: Runs the local development server with hot-reloading.
- `make docs-build`: Generates the static site for deployment.

---

## 3. Success Criteria
- [ ] Running `mkdocs build` generates a full API reference for `toolkitx`.
- [ ] No manual creation of `.md` files is required for new modules.
- [ ] Navigation sidebar matches the package structure.
- [ ] Type hints are correctly rendered as types in the documentation.
