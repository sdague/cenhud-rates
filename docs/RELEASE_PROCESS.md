# Release Process

This document describes how to create a new release of the Central Hudson Electric Rates integration.

## Overview

Releases are created using a GitHub Actions workflow that:
1. Validates the version format
2. Runs all tests (pytest, ruff, HACS validation)
3. Creates a GitHub release with changelog
4. Creates a git tag
5. Generates a zip file for HACS users

## Prerequisites

- Write access to the repository
- All changes merged to `main` branch
- Tests passing locally
- Changelog updated

## Step-by-Step Release Process

### 1. Prepare the Release

Use the helper script to update version numbers:

```bash
make prepare-release VERSION=1.2.0
```

Or manually:

```bash
./scripts/prepare-release.sh 1.2.0
```

This script will:
- Update the version in `custom_components/central_hudson/manifest.json`
- Check if `CHANGELOG.md` has an entry for this version
- Provide guidance on next steps

### 2. Update CHANGELOG.md

If not already done, add a changelog entry for the new version:

```markdown
## [1.2.0] - 2026-03-13

### Added
- New feature description

### Changed
- Changed feature description

### Fixed
- Bug fix description
```

Follow the [Keep a Changelog](https://keepachangelog.com/) format.

### 3. Run Tests Locally

Ensure all tests pass before releasing:

```bash
make test
make lint
make validate-hacs
```

### 4. Commit and Push

Commit the version bump and changelog:

```bash
git add custom_components/central_hudson/manifest.json CHANGELOG.md
git commit -m "Prepare release 1.2.0"
git push origin main
```

### 5. Trigger the Release Workflow

1. Go to the [Actions tab](../../actions/workflows/release.yml) on GitHub
2. Click "Run workflow"
3. Optionally specify a version (or leave empty to use the version from manifest.json)
4. Click "Run workflow" to start

The workflow will:
- Validate the version
- Run all tests
- Create the GitHub release
- Create the git tag
- Upload the release zip file

### 6. Verify the Release

After the workflow completes:

1. Check the [Releases page](../../releases) to see the new release
2. Verify the changelog is correct
3. Download and test the zip file if needed
4. HACS users will be automatically notified of the update

## Release Workflow Details

### Version Format

Versions must follow semantic versioning: `MAJOR.MINOR.PATCH`

- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

Examples: `1.0.0`, `1.2.3`, `2.0.0`

### What Gets Released

The release includes:
- Git tag (e.g., `v1.2.0`)
- GitHub release with changelog
- Zip file: `central-hudson-1.2.0.zip` containing the integration

### Changelog Extraction

The workflow automatically extracts the changelog for the specific version from `CHANGELOG.md`. Make sure your changelog follows this format:

```markdown
## [1.2.0] - 2026-03-13

### Added
- Feature 1
- Feature 2

### Fixed
- Bug 1
```

## Troubleshooting

### "Tag already exists" Error

If you see this error, a release with this version already exists. Either:
- Use a different version number
- Delete the existing tag and release (if it was a mistake)

### Tests Failing

The release workflow will fail if any tests don't pass. Fix the issues and try again:

```bash
# Run tests locally to debug
make test
make lint
```

### Changelog Not Found

If the workflow can't find a changelog entry:
- Ensure `CHANGELOG.md` has an entry for the version
- Check the version format matches exactly: `## [1.2.0] - YYYY-MM-DD`

### Workflow Permission Issues

If you see permission errors:
- Ensure you have write access to the repository
- Check that GitHub Actions has permission to create releases

## Manual Release (Emergency)

If the automated workflow fails, you can create a release manually:

```bash
# Create and push tag
git tag v1.2.0
git push origin v1.2.0

# Create release zip
cd custom_components
zip -r ../central-hudson-1.2.0.zip central_hudson/
cd ..

# Upload to GitHub Releases manually
```

Then create the release on GitHub's web interface.

## Best Practices

1. **Test thoroughly** before releasing
2. **Update changelog** with all changes
3. **Use semantic versioning** correctly
4. **Release from main branch** only
5. **Don't skip versions** - release sequentially
6. **Announce releases** in relevant channels if needed

## Version History

See [CHANGELOG.md](../CHANGELOG.md) for the complete version history.

## Questions?

If you have questions about the release process, please:
- Check this documentation
- Review the [GitHub Actions workflow](../.github/workflows/release.yml)
- Open an issue for clarification