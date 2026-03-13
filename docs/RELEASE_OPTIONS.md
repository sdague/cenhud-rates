# Automated Release Options for Central Hudson Electric Rates

This document outlines three different approaches for automating releases of this Home Assistant custom integration.

## Option 1: Manual Trigger Workflow (Recommended)

### Overview
A GitHub Actions workflow that you trigger manually when you're ready to release. This gives you full control while automating the tedious parts.

### How It Works
1. You update the version in `manifest.json` and `CHANGELOG.md`
2. Commit and push to main
3. Go to GitHub Actions → "Release" workflow → "Run workflow"
4. The workflow:
   - Validates the version format
   - Runs all tests (pytest, ruff, HACS validation)
   - Creates a GitHub release with changelog notes
   - Creates a git tag (e.g., `v1.2.0`)
   - Generates a zip file for HACS users
   - Optionally notifies HACS repository

### Pros
- **Full control**: You decide exactly when to release
- **Safe**: Tests must pass before release is created
- **Simple**: Easy to understand and maintain
- **Standard**: Follows Home Assistant community practices
- **Flexible**: Can add pre-release, draft releases, etc.

### Cons
- Requires manual trigger (but that's often desired)
- Need to manually update version numbers

### Files Created
- `.github/workflows/release.yml` - The release workflow
- `scripts/prepare-release.sh` - Helper script to update versions
- Updates to `Makefile` - Add release commands

### Usage Example
```bash
# Prepare a new release
make prepare-release VERSION=1.2.0

# Review changes, then commit
git add .
git commit -m "Prepare release 1.2.0"
git push

# Go to GitHub Actions and trigger the release workflow
```

---

## Option 2: Auto-Release on Version Bump

### Overview
Automatically creates a release whenever you update the version in `manifest.json` and push to main.

### How It Works
1. You update version in `manifest.json` and `CHANGELOG.md`
2. Commit with message like "Bump version to 1.2.0"
3. Push to main
4. GitHub Actions detects the version change
5. Automatically creates release, tag, and zip

### Pros
- **Fully automated**: No manual trigger needed
- **Fast**: Release happens immediately on push
- **Consistent**: Same process every time

### Cons
- **Less control**: Can't easily stop a release once pushed
- **Risky**: If you push a version bump by mistake, release happens
- **Testing timing**: Release happens even if you wanted to test more
- **Accidental releases**: Easy to trigger unintentionally

### Files Created
- `.github/workflows/auto-release.yml` - Monitors version changes
- `scripts/prepare-release.sh` - Helper script

### Usage Example
```bash
# Update version
scripts/prepare-release.sh 1.2.0

# Commit and push - release happens automatically
git add .
git commit -m "Bump version to 1.2.0"
git push  # Release is created automatically!
```

---

## Option 3: Release Please (Google's Tool)

### Overview
Uses Google's Release Please action to automatically manage versions, changelogs, and releases based on conventional commit messages.

### How It Works
1. You write commits following conventional commit format:
   - `feat: add new sensor` (minor version bump)
   - `fix: correct calculation` (patch version bump)
   - `feat!: breaking change` (major version bump)
2. Release Please creates a "release PR" automatically
3. When you merge the release PR, it:
   - Updates version in manifest.json
   - Updates CHANGELOG.md automatically
   - Creates GitHub release
   - Creates git tag

### Pros
- **Automatic changelog**: Generated from commit messages
- **Semantic versioning**: Automatically determines version bumps
- **Professional**: Used by many large projects
- **Comprehensive**: Handles everything end-to-end

### Cons
- **Learning curve**: Must learn conventional commits
- **Less control**: Version numbers determined by commit types
- **Complex**: More moving parts to understand
- **Overkill**: May be too much for a small project
- **Commit discipline**: Requires consistent commit message format
- **HA-specific**: Need to customize for manifest.json updates

### Files Created
- `.github/workflows/release-please.yml` - Release Please workflow
- `.release-please-config.json` - Configuration
- `.release-please-manifest.json` - Version tracking

### Usage Example
```bash
# Make changes with conventional commits
git commit -m "feat: add time-of-use rate support"
git commit -m "fix: correct holiday detection"
git push

# Release Please creates a PR automatically
# Review and merge the PR
# Release is created automatically when PR is merged
```

---

## Comparison Table

| Feature | Option 1: Manual | Option 2: Auto | Option 3: Release Please |
|---------|-----------------|----------------|-------------------------|
| Control | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| Simplicity | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ |
| Automation | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Safety | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| HA Community Standard | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| Changelog Management | Manual | Manual | Automatic |
| Version Management | Manual | Manual | Automatic |
| Learning Curve | Low | Low | Medium |
| Maintenance | Low | Low | Medium |

---

## Recommendation

**For this project, I recommend Option 1 (Manual Trigger Workflow)** because:

1. **Home Assistant Standard**: Most HA custom integrations use manual releases
2. **Safety First**: You can test thoroughly before releasing
3. **Simple**: Easy to understand and maintain
4. **Flexible**: Can create pre-releases, drafts, or skip releases
5. **Control**: You decide when users get updates
6. **HACS Compatible**: Works perfectly with HACS update mechanism

Option 2 is good if you want maximum automation and are very disciplined about testing before pushing.

Option 3 is better for larger projects with multiple contributors where automatic changelog generation is valuable.

---

## Next Steps

Choose your preferred option and I'll implement it for you:
- **Option 1**: I'll create the manual trigger workflow
- **Option 2**: I'll create the auto-release workflow
- **Option 3**: I'll set up Release Please

Or I can implement multiple options so you can try them and choose later!