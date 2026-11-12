.PHONY: setup fmt fmt-check lint type test validate check

UV := uv run

setup:
	uv python install 3.11
	uv sync --all-groups --frozen
	$(UV) pre-commit install
	$(UV) pre-commit install --hook-type commit-msg
	$(UV) pre-commit install --hook-type pre-push

fmt:
	$(UV) ruff format .

fmt-check:
	$(UV) ruff format --check .

lint:
	$(UV) ruff check .

type:
	$(UV) mypy

test:
	$(UV) pytest -m "not slow"

validate:
	$(UV) python tools/run_task_locally.py --all

check: fmt-check lint type
	$(UV) pytest
	$(MAKE) validate
