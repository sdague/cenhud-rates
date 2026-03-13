# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2026-03-12

### Added

- Binary sensor for current rate class
- Release scripts

## [1.1.0] - 2026-03-12

### Added
- GitHub Actions CI workflow for automated testing
- Ruff linting and formatting configuration
- HACS validation in CI pipeline
- Development requirements file (requirements-dev.txt)
- CI status badge in README
- Brand icon (custom_components/central_hudson/brand/icon.png) with Central Hudson blue and lightning bolt
- Local HACS validation script (scripts/validate-hacs.sh)
- Makefile with common development commands
- Development section in README with setup and testing instructions
- pytest.ini for async test configuration

### Fixed
- All tests now pass with async fixtures
- Linting issues resolved (import order, unused imports, unnecessary file modes)
- Test data structure updated to match current implementation

## [1.0.0] - 2026-03-11

### Added
- Initial release of Central Hudson Electric Rates integration
- Support for residential and commercial electricity rates
- Configuration flow for easy setup through Home Assistant UI
- Sensor entity displaying current electricity rate in $/kWh
- Web scraper script to fetch monthly price updates from Central Hudson website
- HACS compatibility
- Energy Dashboard integration support
- Comprehensive documentation and installation instructions