BACKEND := backend
FRONTEND := frontend
UV := uv run --directory $(BACKEND)
NPM := npm --prefix $(FRONTEND)

.PHONY: install dev dev-backend dev-frontend test test-all lint format typecheck check

install:
	uv sync --directory $(BACKEND)
	$(NPM) ci

dev:
	$(MAKE) -j2 dev-backend dev-frontend

dev-backend:
	$(UV) uvicorn amanuensis.main:build_app --factory --reload --reload-dir src

dev-frontend:
	$(NPM) run dev

test:
	$(UV) pytest
	$(NPM) test

test-all:
	$(UV) pytest -m ""
	$(NPM) test

lint:
	$(UV) ruff check .
	$(UV) ruff format --check .
	$(NPM) run lint

format:
	$(UV) ruff check --fix .
	$(UV) ruff format .

typecheck:
	$(UV) mypy
	$(NPM) run typecheck

check: lint typecheck test
