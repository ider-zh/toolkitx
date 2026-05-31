# Robust HTML to Markdown with Table Support Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a robust HTML-to-Markdown converter that handles complex tables (colspan/rowspan) and nested tables (via JSON serialization) for better Agent understanding.

**Architecture:**
- Use `BeautifulSoup` to pre-process HTML, specifically targeting `<table>` tags.
- Process nested tables recursively from inside out, converting inner tables to JSON 2D arrays.
- Expand merged cells (`colspan`, `rowspan`) by repeating content in a normalized grid.
- Use `markdownify` for the final conversion to Markdown.

**Tech Stack:** Python, beautifulsoup4, markdownify

---

### Task 1: Setup Dependencies

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: Add dependencies to `pyproject.toml`**

Add `beautifulsoup4` and `markdownify` to the main dependencies.

```toml
dependencies = [
    "diskcache>=5.6.3",
    "httpx>=0.28.1",
    "polars>=1.38.1",
    "pydantic>=2.12.5",
    "tencentcloud-sdk-python>=3.1.50",
    "tqdm>=4.67.3",
    "beautifulsoup4>=4.12.0",
    "markdownify>=0.14.0",
]
```

- [ ] **Step 2: Update lockfile**

Run: `uv lock`

- [ ] **Step 3: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "chore: add beautifulsoup4 and markdownify dependencies"
```

### Task 2: Implement Table Grid Expansion Logic

**Files:**
- Create: `toolkitx/html_utils.py`

- [ ] **Step 1: Implement `_expand_table_cells` internal function**

This function should take a BeautifulSoup `table` tag and normalize it into a grid by expanding `colspan` and `rowspan`.

```python
from bs4 import BeautifulSoup
import json

def _expand_table_cells(table):
    """Normalizes a table by expanding colspan and rowspan."""
    rows = table.find_all("tr", recursive=False)
    if not rows:
        return
    
    num_rows = len(rows)
    # Calculate max columns
    max_cols = 0
    for tr in rows:
        cells = tr.find_all(["td", "th"], recursive=False)
        col_count = sum(max(1, int(c.get("colspan", 1))) for c in cells)
        max_cols = max(max_cols, col_count)
        
    grid = [[None] * max_cols for _ in range(num_rows)]
    
    for row_idx, tr in enumerate(rows):
        cells = tr.find_all(["td", "th"], recursive=False)
        col = 0
        cell_idx = 0
        while cell_idx < len(cells) and col < max_cols:
            while col < max_cols and grid[row_idx][col] is not None:
                col += 1
            if col >= max_cols:
                break
                
            cell = cells[cell_idx]
            rs = max(1, int(cell.get("rowspan", 1)))
            cs = max(1, int(cell.get("colspan", 1)))
            
            # Keep the tag structure for images and other inline elements
            # But simplify block elements within cells to keep Markdown table valid
            for block in cell.find_all(["p", "ul", "ol", "li", "div"]):
                block.insert_before(" ")
                block.insert_after(" ")
                block.unwrap()
            
            content = "".join(str(c) for c in cell.contents).strip()
            tag_name = cell.name
            
            for dr in range(rs):
                for dc in range(cs):
                    r, c = row_idx + dr, col + dc
                    if r < num_rows and c < max_cols:
                        grid[r][c] = (content, tag_name)
            
            col += cs
            cell_idx += 1

    # Reconstruct the table rows
    for row_idx, tr in enumerate(rows):
        for cell in tr.find_all(["td", "th"]):
            cell.decompose()
        for col_idx in range(max_cols):
            data = grid[row_idx][col_idx]
            if data:
                content, tag_name = data
                new_cell = table.find_all("tr", recursive=False)[0].parent.new_tag(tag_name)
                new_cell.append(BeautifulSoup(content, "html.parser"))
            else:
                new_cell = table.find_all("tr", recursive=False)[0].parent.new_tag("td")
                new_cell.string = "\u200b"
            tr.append(new_cell)
```

- [ ] **Step 2: Commit**

```bash
git add toolkitx/html_utils.py
git commit -m "feat: implement table grid expansion logic"
```

### Task 3: Implement Recursive Table Conversion and Public API

**Files:**
- Modify: `toolkitx/html_utils.py`

- [ ] **Step 1: Implement `html_to_markdown` with recursion**

```python
from markdownify import markdownify as md

def html_to_markdown(html: str, handle_nested_tables: str = "json", **kwargs) -> str:
    """
    Converts HTML to Markdown with robust table support.
    
    Nested tables are converted to JSON strings to maintain structure in Markdown cells.
    Merged cells (colspan/rowspan) are expanded.
    """
    soup = BeautifulSoup(html, "html.parser")
    
    # Process tables innermost-first
    while True:
        tables = soup.find_all("table")
        if not tables:
            break
            
        # Find a table that doesn't contain other tables
        innermost_table = None
        for t in tables:
            if not t.find("table"):
                innermost_table = t
                break
        
        if not innermost_table:
            # All remaining tables have cycles? (Should not happen with valid HTML)
            # Just process the first one
            innermost_table = tables[0]
            
        # If this table is inside another table, convert it to JSON
        if innermost_table.find_parent("table"):
            if handle_nested_tables == "json":
                rows_data = []
                for tr in innermost_table.find_all("tr", recursive=False):
                    row = [cell.get_text(strip=True) for cell in tr.find_all(["td", "th"], recursive=False)]
                    rows_data.append(row)
                json_str = json.dumps(rows_data, ensure_ascii=False)
                innermost_table.replace_with(f"`{json_str}`")
            else:
                # Default behavior: let markdownify handle it or simple text
                innermost_table.unwrap() 
        else:
            # Top-level table: Expand it
            _expand_table_cells(innermost_table)
            # Mark it so we don't process it again in this loop
            innermost_table.name = "processed_table"

    # Restore tag names
    for t in soup.find_all("processed_table"):
        t.name = "table"
        
    return md(str(soup), **kwargs).strip()
```

- [ ] **Step 2: Commit**

```bash
git add toolkitx/html_utils.py
git commit -m "feat: implement html_to_markdown with recursive table handling"
```

### Task 4: Expose Public Interface and Add Tests

**Files:**
- Modify: `toolkitx/__init__.py`
- Create: `tests/test_html_utils.py`

- [ ] **Step 1: Expose `html_to_markdown` in `__init__.py`**

```python
from .html_utils import html_to_markdown
```

- [ ] **Step 2: Write tests for `html_to_markdown`**

Create `tests/test_html_utils.py` and add tests for:
1. Normal table
2. Colspan/Rowspan expansion
3. Nested tables (JSON serialization)
4. Images in cells

- [ ] **Step 3: Run tests and verify**

Run: `pytest tests/test_html_utils.py`

- [ ] **Step 4: Commit**

```bash
git add toolkitx/__init__.py tests/test_html_utils.py
git commit -m "test: add tests for html_to_markdown and expose interface"
```
