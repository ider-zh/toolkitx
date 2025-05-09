# toolkitx

A personal Python toolkit for common tasks. This package provides various utility functions to simplify common development workflows.

## Features

*   **Text Utilities** (`toolkitx.text_utils`):
    *   `truncate_text_smart`: Smartly truncates text by characters or words, with options for suffix and tolerance, attempting to preserve sentence or word boundaries.
    *   `split_text_by_word_count`: Splits long text into overlapping chunks based on word count.
*   **Command-Line Script**:
    *   `hello`: A simple script accessible via `hello` command after installation, prints a greeting message.
*   **Experimental Translator** (`toolkitx.lab.translator`):
    *   `Translator`: A class providing translation capabilities using Baidu or Tencent translation APIs, with disk-based caching for performance. (Requires API credentials)

## Installation

1.  Clone the repository:
    ```bash
    git clone https://github.com/ider-zh/toolkitx.git
    cd toolkitx
    ```
2.  Install the package. For development, you can install it in editable mode with development dependencies:
    ```bash
    pip install -e ".[dev]"
    ```
    For regular installation:
    ```bash
    pip install .
    ```

## Usage

### Text Utilities

```python
from toolkitx import truncate_text_smart, split_text_by_word_count

# Smart Truncation
text = "This is a very long sentence that needs to be truncated."
truncated_char = truncate_text_smart(text, limit=20, mode="char", suffix="...")
print(f"Char truncated: {truncated_char}")

truncated_word = truncate_text_smart(text, limit=5, mode="word", suffix="...")
print(f"Word truncated: {truncated_word}")

# Split Text
long_text = "This is a long piece of text that we want to split into several smaller chunks with some overlap between them for context."
chunks = split_text_by_word_count(long_text, max_words=10, overlap=2)
for i, chunk in enumerate(chunks):
    print(f"Chunk {i+1}: {chunk}")
```
