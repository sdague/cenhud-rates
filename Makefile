.PHONY: help test lint format validate-hacs install-dev install-hooks clean prepare-release

help:
	@echo "Available commands:"
	@echo "  make test              - Run pytest tests"
	@echo "  make lint              - Run ruff linting"
	@echo "  make format            - Format code with ruff"
	@echo "  make validate-hacs     - Run HACS validation checks"
	@echo "  make install-dev       - Install development dependencies"
	@echo "  make install-hooks     - Install git pre-commit hooks"
	@echo "  make clean             - Clean up temporary files"
	@echo "  make prepare-release   - Prepare a new release (requires VERSION=x.y.z)"

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

install-hooks:
	./scripts/install-hooks.sh

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

prepare-release:
	@if [ -z "$(VERSION)" ]; then \
		echo "Error: VERSION is required. Usage: make prepare-release VERSION=1.2.0"; \
		exit 1; \
	fi
	./scripts/prepare-release.sh $(VERSION)