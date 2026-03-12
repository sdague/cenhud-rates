.PHONY: help test lint format validate-hacs install-dev clean

help:
	@echo "Available commands:"
	@echo "  make test           - Run pytest tests"
	@echo "  make lint           - Run ruff linting"
	@echo "  make format         - Format code with ruff"
	@echo "  make validate-hacs  - Run HACS validation checks"
	@echo "  make install-dev    - Install development dependencies"
	@echo "  make clean          - Clean up temporary files"

test:
	pytest tests/ -v

lint:
	ruff check custom_components/ tests/ scraper/
	ruff format --check custom_components/ tests/ scraper/

format:
	ruff format custom_components/ tests/ scraper/

validate-hacs:
	./scripts/validate-hacs.sh

install-dev:
	pip install -r requirements-dev.txt

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete