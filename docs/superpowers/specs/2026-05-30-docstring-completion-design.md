# Project Documentation Completion Plan Design

**Goal:** Standardize and complete all Python docstrings across the ToolkitX project using the Google Python Style Guide to ensure a professional and informative documentation site.

**Scope:**
- `toolkitx/text_utils.py`
- `toolkitx/task_utils.py`
- `toolkitx/lab/translator.py`
- `toolkitx/__init__.py` (Package level docs)

**Standards:**
- **Format:** Google Style (`Args:`, `Returns:`, `Raises:`, `Example:`).
- **Language:** Chinese (to maintain consistency with existing comments).
- **Type Information:** Include type hints in the docstrings as supported by `mkdocstrings`.

---

## 1. File-Specific Plans

### 1.1 `toolkitx/text_utils.py`
- Update `truncate_text_smart`: Convert Sphinx-style `:param` to Google Style. Add a detailed explanation of the "smart" logic (sentence vs. word boundaries).
- Update `split_text_by_word_count`: Ensure consistency in parameter descriptions.

### 1.2 `toolkitx/task_utils.py`
- **TokenBucket**: Add class-level and `__init__` docstrings.
- **with_resilience**: Convert to Google Style. Clarify the exponential backoff and jitter logic.
- **PersistentTaskQueue**: 
    - Ensure all public methods have complete `Args` and `Returns`.
    - Document `_get_conn` and `_worker` to explain internal data flow.

### 1.3 `toolkitx/lab/translator.py`
- **TranslatorInterface**: Document abstract methods clearly so implementers know the contract.
- **BaiduTranslation / TencentTranslation**: Document engine-specific parameters (like `region`, `api_url`).
- **Translator**: Complete the main entry point documentation, focusing on the cache key mechanism and error handling.

---

## 2. Success Criteria
- [ ] Every class has a descriptive docstring.
- [ ] Every public method has `Args` and `Returns` (if applicable).
- [ ] No Sphinx-style `:param` or `:return` remain in the codebase.
- [ ] Running `make docs-build` produces no warnings from `mkdocstrings`.
- [ ] The generated site displays comprehensive documentation for all modules.
