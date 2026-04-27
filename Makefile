.PHONY: install test types lint-check lint-fix format-check format-fix check

install:
	poetry install

test:
	poetry run pytest

types:
	poetry run mypy

lint-check:
	poetry run ruff check src/ tests/

lint-fix:
	poetry run ruff check --fix src/ tests/

format-check:
	poetry run ruff format --check src/ tests/

format-fix:
	poetry run ruff format src/ tests/

check: format-check lint-check types test
