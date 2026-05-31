# Rich Interactive Documentation with Automated Validation Design

**Goal:** Transform the static API reference into a living documentation system by adding rich, verifiable usage examples to all public methods and classes.

**Standard:**
- **Format:** Google Style `Examples:` section.
- **Verification:** Examples must use standard `doctest` syntax (`>>>` followed by expected output).
- **Scope:** All major functions and classes in `toolkitx`.

---

## 1. Documentation Enrichment Strategy

### 1.1 Content Structure
Each major docstring will include:
1.  **Basic Usage:** The most common way to use the function.
2.  **Advanced Scenarios:** Handling edge cases, specific parameters (e.g., `tolerance` in truncation), or complex structures (e.g., nested tables).
3.  **Expected Results:** Clear output representation so users (and Agents) know exactly what to expect.

### 1.2 Target Modules & Functions
- **`text_utils.py`**:
    - `truncate_text_smart`: Examples for both 'char' and 'word' modes.
    - `split_text_by_word_count`: Examples with and without overlap.
- **`html_utils.py`**:
    - `html_to_markdown`: Examples showing `colspan`/`rowspan` expansion and nested table JSON serialization.
- **`task_utils.py`**:
    - `TokenBucket`: Simple QPS control simulation.
    - `with_resilience`: Decorator usage example.
    - `PersistentTaskQueue`: A complete workflow (setup -> enqueue -> process -> results).

---

## 2. Automated Validation (Doctest Integration)

### 2.1 Makefile Integration
Add a new target `make test-docs` (or similar) to run `pytest --doctest-modules`. This ensures that every example in the documentation is technically correct and functioning.

### 2.2 CI/CD Alignment
The doctest validation will be recommended as part of the standard testing suite to prevent "documentation rot".

---

## 3. Success Criteria
- [ ] Every major function has at least one `Examples:` block.
- [ ] Running `pytest --doctest-modules toolkitx` passes for all files.
- [ ] The MkDocs site renders these examples as syntax-highlighted code blocks.
- [ ] Complex examples (like `PersistentTaskQueue`) are documented with step-by-step logic.
