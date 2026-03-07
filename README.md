# toolkitx

A personal Python toolkit for common tasks. This package provides various utility functions to simplify common development workflows.

## Features

*   **Text Utilities** (`toolkitx.text_utils`):
    *   `truncate_text_smart`: Smartly truncates text by characters or words, with options for suffix and tolerance, attempting to preserve sentence or word boundaries.
    *   `split_text_by_word_count`: Splits long text into overlapping chunks based on word count.
    
*   **Task Utilities** (`toolkitx.task_utils`):
    *   `with_resilience`: A decorator for API resilience with rate limiting (QPS), exponential backoff retry, and jitter to prevent thundering herd.
    *   `PersistentTaskQueue`: A persistent task queue with SQLite backend, supporting concurrent processing, automatic retry, crash recovery, and graceful shutdown.
    
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

### Task Utilities

#### with_resilience Decorator

```python
from toolkitx.task_utils import with_resilience
import requests

@with_resilience(qps=5.0, max_retries=3, base_delay=1.0, max_delay=60.0)
def call_api_with_retry(url: str) -> dict:
    """Call API with automatic retry and rate limiting"""
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return response.json()

# The decorator will automatically:
# - Limit requests to 5 per second (QPS)
# - Retry up to 3 times on failure with exponential backoff
# - Add random jitter to prevent thundering herd
result = call_api_with_retry("https://api.example.com/data")
```

#### PersistentTaskQueue

```python
import polars as pl
from pydantic import BaseModel
from toolkitx.task_utils import PersistentTaskQueue
import tempfile

# Define your data model
class EntityModel(BaseModel):
    name: str
    is_company: bool

# Define your processing function
def extract_entity(text: str) -> EntityModel:
    """Extract entity information from text"""
    # Your processing logic here
    return EntityModel(name=text.split()[0], is_company=True)

# Prepare data
df = pl.DataFrame({
    "batch_id": ["batch1", "batch1", "batch2"],
    "input_text": ["Apple Inc.", "Google Corp.", "Microsoft"]
})

# Initialize queue with temporary database
with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
    db_path = f.name

queue = PersistentTaskQueue(db_path=db_path, task_name="entity_extraction", max_retries=3)

# Setup and enqueue data
queue.setup()
queue.enqueue_dataframe(df)

# Process tasks with concurrency control (supports Ctrl+C for graceful shutdown)
queue.process(worker_func=extract_entity, concurrency=10)

# Get results
results = queue.get_results(response_model=EntityModel)
print(results)
```
