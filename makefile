update:
	uv lock

test_translator:
	uv run --env-file .env  python toolkitx/lab/translator.py 