# AGENTS.md

## Project Overview

Home Assistant custom component providing Central Hudson Gas & Electric
residential electricity rate sensors. Rates are scraped monthly from
cenhud.com and stored in `custom_components/central_hudson/data/prices.json`.

## Architecture

- `custom_components/central_hudson/` - The HA integration (sensors, config flow, utilities)
- `scraper/` - Selenium-based web scraper for fetching current rates
- `tests/` - pytest test suite
- `scripts/` - Build, release, and validation scripts

## Development

Use a virtualenv in the working directory:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements-dev.txt
```

## Commands

- `make test` - Run pytest (required before commit)
- `make lint` - Run ruff check + format check (required before commit)
- `make format` - Auto-format with ruff
- `make validate-hacs` - HACS compatibility validation
- `make prepare-release VERSION=x.y.z` - Prepare a release

## Testing

pytest with `pytest-homeassistant-custom-component`. Tests are async
(`asyncio_mode = auto`). Run `make test` and confirm all pass before
committing.

## Code Style

Ruff handles both linting and formatting. Run `make lint` to check,
`make format` to fix. Key rules:

- Double quotes, space indentation
- No line-length lint (formatter handles it)
- isort for imports

## Commit Workflow

1. `make lint` - must pass
2. `make test` - must pass
3. Commit (this repo is github.com, no co-author line)

## Rate Data

`prices.json` contains an array of rate periods with effective dates. The
sensor picks the most recent rate whose `effective_date` has passed. To add
a new rate period, run `make update-rates` (`scripts/update_rates.py`), which
prompts for the charges and updates `prices.json`, `RATE_HISTORY.md`, and the
`[Unreleased]` CHANGELOG section together. Alternatively run the scraper or
edit the JSON directly, then update RATE_HISTORY.md and CHANGELOG by hand.

## Releasing

See `docs/RELEASE_QUICKSTART.md`. Use `make prepare-release VERSION=x.y.z`
which updates manifest.json, CHANGELOG, and creates a git tag.
