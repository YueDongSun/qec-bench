export PATH := $(HOME)/.local/bin:$(PATH)

.PHONY: setup fmt fmt-check lint type test validate check

setup:
	uv sync --frozen --all-groups
	uv run pre-commit install --hook-type pre-commit --hook-type commit-msg --hook-type pre-push
	bash tools/hooks/install_pre_push.sh

fmt:
	uv run ruff format src tests tools tasks

fmt-check:
	uv run ruff format --check src tests tools tasks

lint:
	uv run ruff check src tests tools tasks

type:
	uv run mypy --strict src/qecbench

test:
	uv run pytest

validate:
	uv run python tools/validate_tasks.py

check: fmt-check lint type test validate
