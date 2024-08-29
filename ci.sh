#! /bin/bash
# if VIRTUAL_ENV variable set (i.e. in a poetry shell), then run command
if [ -n "$VIRTUAL_ENV" ]; then
    echo "=== ruff format ===" && ruff format --check
    echo "=== ruff lint ===" && ruff check --fix
    echo "=== isort ===" && isort . --check --diff
else
    echo "=== ruff format ===" && poetry run ruff format --check
    echo "=== ruff lint ===" && poetry run ruff check --fix
    echo "=== isort ===" && poetry run isort . --check --diff
fi
