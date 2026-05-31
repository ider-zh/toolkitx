# Table Grid Expansion Logic Fix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix data loss in table normalization by robustly calculating grid width and preventing accidental decomposition of nested table cells.

**Architecture:** Use a tracking dictionary to account for `rowspan` and `colspan` when calculating `max_cols`. Ensure all `find_all` calls for table structural elements (`tr`, `td`, `th`) use `recursive=False`.

**Tech Stack:** Python, BeautifulSoup4

---

### Task 1: Robust max_cols Calculation

**Files:**
- Modify: `toolkitx/html_utils.py`
- Test: `tests/test_table_fix.py` (or use isolated test)

- [ ] **Step 1: Write the failing test**
(Already done in `tests/test_table_fix.py` and `test_table_isolated.py`)

- [ ] **Step 2: Run test to verify it fails**
Run: `PYTHONPATH=. python3 test_table_isolated.py`
Expected: `max_cols=1`, "B" is lost in output.

- [ ] **Step 3: Update max_cols calculation logic**

```python
    # Calculate actual grid width accounting for rowspans
    max_cols = 0
    occupied = set() # (row, col)
    for row_idx, tr in enumerate(rows):
        cells = tr.find_all(["td", "th"], recursive=False)
        col = 0
        for cell in cells:
            while (row_idx, col) in occupied:
                col += 1
            rs = max(1, int(cell.get("rowspan", 1)))
            cs = max(1, int(cell.get("colspan", 1)))
            for dr in range(rs):
                for dc in range(cs):
                    occupied.add((row_idx + dr, col + dc))
            col += cs
            max_cols = max(max_cols, col)
```

- [ ] **Step 4: Run test to verify it passes**
Run: `PYTHONPATH=. python3 test_table_isolated.py`
Expected: `max_cols=2`, "B" is preserved in row 2.

- [ ] **Step 5: Commit**

```bash
git add toolkitx/html_utils.py
git commit -m "fix: robust max_cols calculation for table expansion"
```

### Task 2: Prevent Recursive Decomposition

**Files:**
- Modify: `toolkitx/html_utils.py`

- [ ] **Step 1: Write the failing test for nested tables**
(Already done in `test_table_isolated.py`)

- [ ] **Step 2: Run test to verify behavior**
Run: `PYTHONPATH=. python3 test_table_isolated.py`
Verify if nested cells are affected (though stringification hides it, we should fix the logic).

- [ ] **Step 3: Add recursive=False to decomposition loop**

```python
    for row_idx, tr in enumerate(rows):
        for cell in tr.find_all(["td", "th"], recursive=False):
            cell.decompose()
```

- [ ] **Step 4: Run all tests to ensure no regressions**
Run: `PYTHONPATH=. python3 tests/test_html_utils.py`
Run: `PYTHONPATH=. python3 test_table_isolated.py`

- [ ] **Step 5: Commit**

```bash
git add toolkitx/html_utils.py
git commit -m "fix: prevent recursive decomposition of nested table cells"
```
