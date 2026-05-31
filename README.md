# ToolkitX

[![Documentation Status](https://readthedocs.org/projects/toolkitx/badge/?version=latest)](https://toolkitx.readthedocs.io/en/latest/?badge=latest)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)

A personal Python toolkit for common tasks. This package provides robust utility functions to simplify common development workflows, focusing on text processing, HTML conversion, and task resilience.

📖 **Full Documentation**: [https://toolkitx.readthedocs.io/en/latest/](https://toolkitx.readthedocs.io/en/latest/)

## Features

*   **HTML Utilities** (`toolkitx.html_utils`):
    *   `html_to_markdown`: Robust HTML to Markdown conversion. Handles complex tables (colspan/rowspan) by expansion and serializes nested tables to JSON for better LLM/Agent understanding. Automatically promotes the first row to header if missing.
    
*   **Text Utilities** (`toolkitx.text_utils`):
    *   `truncate_text_smart`: Smartly truncates text by characters or words, attempting to preserve sentence or word boundaries with configurable tolerance.
    *   `split_text_by_word_count`: Splits long text into overlapping chunks based on word count.
    
*   **Task Utilities** (`toolkitx.task_utils`):
    *   `with_resilience`: A decorator for API resilience with rate limiting (QPS), exponential backoff retry, and jitter.
    *   `PersistentTaskQueue`: A persistent task queue with SQLite backend, supporting concurrent processing, automatic retry, crash recovery, and graceful shutdown.
    
*   **Experimental Translator** (`toolkitx.lab.translator`):
    *   `Translator`: A class providing translation capabilities using Baidu or Tencent translation APIs, with disk-based caching.

## Installation

We recommend using [uv](https://github.com/astral-sh/uv) for fast and reliable dependency management.

```bash
# Clone the repository
git clone https://github.com/ider-zh/toolkitx.git
cd toolkitx

# Install with development dependencies
uv pip install -e ".[dev,docs]"
```

## Usage

### HTML to Markdown (Robust Table Support)

```python
from toolkitx import html_to_markdown

# Handles merged cells (colspan/rowspan) and nested tables
html = """
<table>
  <tr><td colspan="2">Merged Header</td></tr>
  <tr><td>Cell 1</td><td>Cell 2</td></tr>
  <tr>
    <td>Outer</td>
    <td>
      <table><tr><td>Nested</td></tr></table>
    </td>
  </tr>
</table>
"""

md = html_to_markdown(html)
print(md)
```

### Text Smart Truncation

```python
from toolkitx import truncate_text_smart

text = "Hello World. This is a long sentence that should be truncated smartly."
# Strips trailing punctuation automatically
truncated = truncate_text_smart(text, limit=12) 
print(truncated) # Output: 'Hello World...'
```

### Task Resilience Decorator

```python
from toolkitx import with_resilience

@with_resilience(qps=2.0, max_retries=3)
def fetch_data(url):
    # This function will be rate-limited and retried automatically
    pass
```

## Development

### Running Tests
```bash
# Run unit tests
make test

# Run documentation tests (verify examples in docstrings)
make test-docs
```

### Documentation
```bash
# Preview documentation locally
make docs-serve

# Build static documentation site
make docs-build
```

## Changelog

### v0.0.5 (2026-05-30)
- **New Feature**: Added `html_utils` with robust `html_to_markdown` converter.
- **Improved**: `truncate_text_smart` now strips trailing punctuation before appending suffix.
- **Documentation**: Established full automated documentation system with MkDocs, Material theme, and Read the Docs integration.
- **Verifiable Docs**: Added `doctest` examples to all core functions and a `make test-docs` target.
- **Workflow**: Integrated `ruff` for linting and formatting.
- **Dependency Management**: Fully transitioned to `uv` and pinned `mkdocs` for stability.

### v0.0.4 (2026-03-07)
- Added `task_utils` module with `with_resilience` decorator and `PersistentTaskQueue`.
- Added `polars`, `pydantic`, and `tqdm` as dependencies.
