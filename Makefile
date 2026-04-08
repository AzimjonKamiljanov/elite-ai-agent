# JARVIS Prime — Makefile
.PHONY: run api voice test lint install setup health

PYTHON := python3
PORT   := 8000

## Install all dependencies
install:
	$(PYTHON) -m pip install -e ".[voice,memory,perf,dev]"

## Run the full setup script
setup:
	bash scripts/setup.sh

## Start interactive CLI (life assistant + modes)
run:
	$(PYTHON) -m apps.cli

## Start FastAPI server
api:
	$(PYTHON) -m apps.cli --api --port $(PORT)

## Start voice assistant
voice:
	$(PYTHON) -m apps.cli --voice

## Run pytest suite
test:
	$(PYTHON) -m pytest tests/ -v --tb=short

## Run tests multiple times (required: 5 green runs)
test-5:
	@for i in 1 2 3 4 5; do \
		echo "\n=== Test run $$i/5 ==="; \
		$(PYTHON) -m pytest tests/ -q --tb=short || exit 1; \
	done
	@echo "\n✅ All 5 test runs passed."

## Lint with ruff
lint:
	$(PYTHON) -m ruff check . --fix
	$(PYTHON) -m ruff format .

## System health check
health:
	$(PYTHON) scripts/health_check.py

## Download Vosk model for offline STT
vosk-model:
	bash scripts/download_vosk_model.sh

## Show help
help:
	@echo "JARVIS Prime — available targets:"
	@echo "  make install    — install dependencies"
	@echo "  make run        — start CLI"
	@echo "  make api        — start FastAPI server (port $(PORT))"
	@echo "  make voice      — start voice assistant"
	@echo "  make test       — run pytest suite"
	@echo "  make test-5     — run tests 5 times"
	@echo "  make lint       — run ruff linter"
	@echo "  make health     — health check"
	@echo "  make vosk-model — download Vosk offline STT model"
