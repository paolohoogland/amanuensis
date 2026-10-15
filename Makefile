BACKEND := backend
UV := uv run --directory $(BACKEND)

.PHONY: install test test-all lint format typecheck check

install:
	uv sync --directory $(BACKEND)

test:
	$(UV) pytest

test-all:
	$(UV) pytest -m ""

lint:
	$(UV) ruff check .
	$(UV) ruff format --check .

format:
	$(UV) ruff check --fix .
	$(UV) ruff format .

typecheck:
	$(UV) mypy

check: lint typecheck test
