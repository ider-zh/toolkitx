# Enrich `text_utils.py` with Doctests Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enrich `text_utils.py` documentation with verifiable Google Style `Examples:` sections using `doctest` syntax.

**Architecture:** Update docstrings of `truncate_text_smart` and `split_text_by_word_count` to include `Examples:` sections that double as tests.

**Tech Stack:** Python, Doctest, Pytest.

---

### Task 1: Update `truncate_text_smart` Docstring

**Files:**
- Modify: `toolkitx/text_utils.py:4-15`

- [ ] **Step 1: Update docstring with examples**

```python
def truncate_text_smart(
    text: str,
    limit: int = 100,
    mode: str = "char",
    suffix: str = "...",
    tolerance: int = 10,
) -> str:
    \"\"\"
    Smartly truncates text based on character or word limit, with tolerance.

    Args:
        text: The original string.
        limit: The target truncation length (in characters or words).
        mode: Truncation mode: 'char' for character-based, 'word' for word-based.
        suffix: The suffix to append after truncation.
        tolerance: The allowed deviation from the limit for smart truncation.

    Returns:
        The truncated string.

    Raises:
        ValueError: If the mode is not 'char' or 'word'.

    Examples:
        >>> truncate_text_smart("Hello World. This is a test.", limit=12)
        'Hello World...'
        >>> truncate_text_smart("Hello World. This is a test.", limit=15, mode="word")
        'Hello World. This is a test.'
        >>> truncate_text_smart("A very long sentence that should be truncated by word count.", limit=5, mode="word")
        'A very long sentence that...'
    \"\"\"
```

- [ ] **Step 2: Verify doctests for this function**

Run: `uv run pytest --doctest-modules toolkitx/text_utils.py`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add toolkitx/text_utils.py
git commit -m "docs: add doctests to truncate_text_smart"
```

### Task 2: Update `split_text_by_word_count` Docstring

**Files:**
- Modify: `toolkitx/text_utils.py:126-136`

- [ ] **Step 1: Update docstring with examples**

```python
def split_text_by_word_count(
    text: str, max_words: int = 300, overlap: int = 0
) -> list[str]:
    \"\"\"
    Split a long text into overlapping chunks (trunks), each with at most `max_words` words,
    and `overlap` words overlapping between consecutive trunks.

    Args:
        text: The input text.
        max_words: Maximum number of words per chunk.
        overlap: Number of overlapping words between adjacent chunks.

    Returns:
        A list of text chunks.

    Examples:
        >>> split_text_by_word_count("one two three four five", max_words=2)
        ['one two', 'three four', 'five']
        >>> split_text_by_word_count("one two three four five", max_words=3, overlap=1)
        ['one two three', 'three four five']
    \"\"\"
```

- [ ] **Step 2: Verify all doctests in the file**

Run: `uv run pytest --doctest-modules toolkitx/text_utils.py`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add toolkitx/text_utils.py
git commit -m "docs: add doctests to split_text_by_word_count"
```
