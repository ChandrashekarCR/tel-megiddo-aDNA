BASE_PYTHON ?= python
PYTHON := .venv/bin/python

DEFAULT_GOAL := all
SHELL := bash
.SHELL_FLAGS := -euo pipefail -c
.PHONY := hello 
.SUFFIXES:
.DELETE_ON_ERROR:

hello: # Hello Makefile
	@echo "Makefile working.."
	@echo "[hello] ok.."

lint: # Linting python scripts
	@$(PYTHON) -m ruff check . || (echo '[lint] ruff failed' >&2; exit 1)
	@echo "[lint] ok"

format: # Code formatting using ruff
	@echo "Organizing imports with ruff.."
	@$(PYTHON) -m ruff check --fix src/ tests/ || (echo '[format] ruff import sorting failed' >&2; exit 1)
	@$(PYTHON) -m ruff format src/ tests/ || (echo '[format] ruff format failed' >&2; exit 1)
	@echo "[format] ok."

clean: # Clean all the cache files and .out and .err files from slurm runs
	@find . -type f -name "*.err" -delete
	@find . -type f -name "*.out" -delete
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@find . -type d -name "*.egg-info" -exec rm -rf {} +
	@find . -type d -name ".pytest_cache" -exec rm -rf {} +
	@find . -type d -name ".ruff_cache" -exec rm -rf {} +
	@echo "[clean] ok"