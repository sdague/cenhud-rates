# Release Quick Start Guide

This is a quick reference for creating releases. For detailed information, see [RELEASE_PROCESS.md](RELEASE_PROCESS.md).

## TL;DR - Create a Release

```bash
# 1. Prepare the release
make prepare-release VERSION=1.2.0

# 2. Review and update CHANGELOG.md if needed
# Edit CHANGELOG.md to add release notes

# 3. Run tests
make test

# 4. Commit and push
git add custom_components/central_hudson/manifest.json CHANGELOG.md
git commit -m "Prepare release 1.2.0"
git push origin main

# 5. Go to GitHub Actions and trigger the release workflow
# https://github.com/YOUR-USERNAME/YOUR-REPO/actions/workflows/release.yml
# Click "Run workflow" button
```

## What Happens When You Release

1. ✅ Version validation
2. ✅ All tests run (pytest, ruff, HACS)
3. ✅ GitHub release created with changelog
4. ✅ Git tag created (e.g., `v1.2.0`)
5. ✅ Zip file generated for HACS users
6. ✅ HACS users notified of update

## Files to Update Before Release

1. **`custom_components/central_hudson/manifest.json`** - Version number (automated by script)
2. **`CHANGELOG.md`** - Add release notes for the new version

## Changelog Format

```markdown
## [1.2.0] - 2026-03-13

### Added
- New feature 1
- New feature 2

### Changed
- Changed behavior 1

### Fixed
- Bug fix 1
- Bug fix 2
```

## Common Commands

```bash
# Prepare release
make prepare-release VERSION=1.2.0

# Run all tests
make test

# Check code quality
make lint

# Validate HACS compatibility
make validate-hacs

# See all available commands
make help
```

## Troubleshooting

**Tests failing?**
```bash
make test
make lint
```

**Tag already exists?**
- Use a different version number
- Or delete the existing tag if it was a mistake

**Changelog not found?**
- Ensure CHANGELOG.md has an entry: `## [1.2.0] - YYYY-MM-DD`

## Need Help?

- 📖 [Full Release Process Documentation](RELEASE_PROCESS.md)
- 📋 [Release Options Comparison](RELEASE_OPTIONS.md)
- 🐛 [Open an Issue](../../issues)