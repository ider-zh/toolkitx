update:
	uv lock

test_translator:
	uv run --env-file .env  python toolkitx/lab/translator.py 

lint:
	uv run ruff check .

format:
	uv run ruff format .

fix:
	uv run ruff check . --fix

docs-serve:
	uv run --extra docs mkdocs serve

docs-build:
	uv run --extra docs mkdocs build
 