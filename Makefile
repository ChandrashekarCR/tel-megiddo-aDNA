BASE_PYTHON ?= python
CONDA_ENV_NAME := tel-megiddo
PYTHON := ~/.conda/envs/$(CONDA_ENV_NAME)/bin/python
NEXTFLOW := ~/.conda/envs/$(CONDA_ENV_NAME)/bin/nextflow

DEFAULT_GOAL := all
SHELL := bash
.SHELLFLAGS := -euo pipefail -c
.SUFFIXES:
.DELETE_ON_ERROR:

hello: # Hello Makefile
	@echo "Makefile working.."
	@echo "[hello] ok"

lint: # Linting python scripts
	@$(PYTHON) -m ruff check . || (echo '[lint] ruff failed' >&2; exit 1)
	@echo "[lint] ok"

format: # Code formatting using ruff
	@echo "Organizing imports with ruff.."
	@$(PYTHON) -m ruff check --fix src/ tests/ || (echo '[format] ruff import sorting failed' >&2; exit 1)
	@$(PYTHON) -m ruff format src/ tests/ || (echo '[format] ruff format failed' >&2; exit 1)
	@echo "[format] ok"

clean: # Clean all the cache files and .out and .err files from slurm runs
	@find . -type f -name "*.err" -delete
	@find . -type f -name "*.out" -delete
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@find . -type d -name "*.egg-info" -exec rm -rf {} +
	@find . -type d -name ".pytest_cache" -exec rm -rf {} +
	@find . -type d -name ".ruff_cache" -exec rm -rf {} +
	@find . -type f -name ".nextflow*" -exec rm -rf {} +
	@echo "[clean] ok"

conda_env: environment.yaml
	@bash -c 'if conda env list | grep "$(CONDA_ENV_NAME)"; then \
		echo "Environment already exisits. Syncing packages.."; \
		conda env update -n $(CONDA_ENV_NAME) -f environment.yaml --prune;\
	else \
		echo "Environment does not exist. Creating the environment from yml file."; \
		conda env create -f environment.yaml; \
	fi'
	@echo "Environment is ready. Run conda activate $(CONDA_ENV_NAME) to activate it."
	@echo "[conda_env] ok"

build-image: # Build a .sif file for containerization
	@echo "Checking if the .sif file exists"
	@if [ -f tel-megiddo.sif ]; then \
		echo "Image 'tel-megiddo.sif' already exists." >&2; \
		exit 1; \
	fi
	@if [ ! -f Singularity ]; then \
		echo "Singularity definition file 'Singularity' does not exist." >&2; \
		exit 1; \
	fi
	@echo "Building image using Singularity file..."
	@apptainer build tel-megiddo.sif Singularity
	@echo "[build-image] ok"

test: # Run pytests for script
	@echo "Running core tests.."
	@$(PYTHON) -m pytest tests/
	@echo "[test] ok"

smoke-test: # Run Nextflow workflow in stub mode (CI smoke test)
	@echo "Running Nextflow smoke test (stub mode).."
	@which $(NEXTFLOW) > /dev/null || (echo '[smoke-test] nextflow not found. Install with: conda install -c bioconda nextflow' >&2; exit 1)
	
	@$(NEXTFLOW) run src/main.nf \
		-c config/test.config \
		-stub \

	@echo "[smoke-test] ok"