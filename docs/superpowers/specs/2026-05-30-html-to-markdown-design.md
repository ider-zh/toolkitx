# HTML to Markdown with Robust Table Support Design

**Goal:** Implement a robust HTML-to-Markdown converter in `toolkitx` that specifically addresses the limitations of Markdown tables (no colspan/rowspan, no nesting) by expanding merged cells and serializing nested structures for better Agent understanding.

**Architecture:**
- **Module:** `toolkitx/html_utils.py`
- **Primary Function:** `html_to_markdown(html: str, handle_nested_tables: str = "json", **kwargs) -> str`
- **Core Dependencies:** `beautifulsoup4` (HTML parsing), `markdownify` (MD conversion).

---

## 1. Core Logic & Algorithms

### 1.1 Recursive Table Processing
To handle nested tables, the algorithm will process tables from the **innermost** to the **outermost**:
1.  Locate all `<table>` elements.
2.  For a given table, if it contains nested tables:
    -   Recursively convert nested tables into a **JSON 2D Array** (Option B: `[["row1col1", ...], ...]`).
    -   Replace the nested `<table>` tag with a text placeholder containing this JSON string.
3.  Once all nested tables within the current table are replaced by text, perform **Grid Expansion**.

### 1.2 Table Grid Expansion
Based on the provided algorithm:
1.  **Grid Mapping:** Create a 2D grid of size `num_rows` x `max_cols`.
2.  **Cell Filling:** Iterate through `<tr>` and `<td>`/`<th>`. For cells with `colspan` or `rowspan`, fill the corresponding rectangular area in the grid with the same content.
3.  **Normalization:** Reconstruct the HTML `<table>` as a perfect grid (all rows have equal number of cells, no merges) before passing it to `markdownify`.
4.  **Empty Cells:** Use a Zero Width Space (`\u200b`) or a standard space to ensure Markdown table pipes remain intact.

### 1.3 Cell Content Serialization
- **Images:** Ensure `<img>` tags are preserved during grid expansion so `markdownify` can turn them into `![]()` syntax.
- **Complex Blocks:** Within a table cell, block-level elements like `<ul>`, `<li>`, `<p>` will be simplified (e.g., converted to inline text separated by `; ` or similar) to ensure the final Markdown table remains valid (one row per line).

---

## 2. Integration & Dependencies

### 2.1 Dependency Updates (`pyproject.toml`)
Add to `dependencies`:
- `beautifulsoup4>=4.12.0`
- `markdownify>=0.14.0`

### 2.2 Public API (`toolkitx/__init__.py`)
Expose `html_to_markdown` for easy access:
```python
from .html_utils import html_to_markdown
```

---

## 3. Success Criteria
- [ ] Correctly expands `colspan` and `rowspan` into repeated content.
- [ ] Converts nested tables into JSON strings within the parent cell.
- [ ] Preserves image URLs in Markdown format.
- [ ] Handles malformed HTML tables gracefully (robust grid calculation).
- [ ] Passing existing and new test cases for complex table layouts.
