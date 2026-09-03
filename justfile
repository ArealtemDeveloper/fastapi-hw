@a_default:
    just --list

@dev:
    uv run fastapi dev src/fastapi_hw/main.py

@lint:
    uv run ruff check --fix