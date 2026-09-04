@a_default:
    just --list

@dev:
    uv run fastapi dev src/main.py

@lint:
    uv run ruff check --fix