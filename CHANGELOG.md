# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.6] - 2026-03-27

### Changed

- Add additional attribute for debugging DST bug

## [1.2.5] - 2026-03-27

### Fixed

- Fixed binary_sensor platform not being exposed in Home Assistant by adding Platform.BINARY_SENSOR to PLATFORMS list

## [1.2.4] - 2026-03-25

### Changed

- Updated `actions/setup-python` from v5 to v6 in CI workflow
- Updated `actions/checkout` from v4 to v6 in CI workflow

## [1.2.3] - 2026-03-17

### Fixed

- Fixed peak/off-peak time determination to use timezone-aware datetime with proper daylight savings time handling
- Changed `is_on_peak_time()` to use Home Assistant's `dt_util.now()` instead of `datetime.now()`
- Fixed `fetch_prices_selenium.py` scraper to properly skip 12-month average row
- Added extraction of effective date from first column of pricing data
- Added automatic calculation of total_per_kwh using delivery charges from historical data
- Scraper now includes delivery_charge and total_per_kwh in output when historical data is available

## [1.2.2] - 2026-03-15

### Fixed

- Fixed `fetch_prices_selenium.py` scraper to correctly extract supply charges only (not total charges)
- Fixed scraper to skip the first row of prices which contains 12-month averages
- Updated rate format to properly separate supply charges from delivery charges

## [1.2.1] - 2026-03-14

### Fixed

- Update prices for March 2026

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