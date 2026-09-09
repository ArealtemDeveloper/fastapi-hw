@a_default:
    just --list

@dev:
    uv run uvicorn main:app --app-dir src --reload --log-config log_conf.yaml

@lint:
    uv run ruff check --fix

@format:
    uv run ruff format