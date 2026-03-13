#!/bin/bash
# Helper script to prepare a new release

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if version argument is provided
if [ -z "$1" ]; then
    echo -e "${RED}Error: Version number required${NC}"
    echo "Usage: $0 <version>"
    echo "Example: $0 1.2.0"
    exit 1
fi

VERSION=$1

# Validate version format (X.Y.Z)
if ! [[ "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo -e "${RED}Error: Version must be in format X.Y.Z (e.g., 1.2.0)${NC}"
    exit 1
fi

echo -e "${GREEN}Preparing release v$VERSION${NC}"
echo ""

# Check if we're on main branch
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "main" ]; then
    echo -e "${YELLOW}Warning: You are not on the main branch (current: $CURRENT_BRANCH)${NC}"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check for uncommitted changes
if ! git diff-index --quiet HEAD --; then
    echo -e "${YELLOW}Warning: You have uncommitted changes${NC}"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Update version in manifest.json
echo "Updating version in manifest.json..."
python3 -c "
import json
with open('custom_components/central_hudson/manifest.json', 'r') as f:
    manifest = json.load(f)
manifest['version'] = '$VERSION'
with open('custom_components/central_hudson/manifest.json', 'w') as f:
    json.dump(manifest, f, indent=2)
    f.write('\n')
"

echo -e "${GREEN}✓ Updated manifest.json to version $VERSION${NC}"

# Check if CHANGELOG.md has an entry for this version
if ! grep -q "\[$VERSION\]" CHANGELOG.md; then
    echo -e "${YELLOW}Warning: No entry found for version $VERSION in CHANGELOG.md${NC}"
    echo ""
    echo "Please add a changelog entry in the following format:"
    echo ""
    echo "## [$VERSION] - $(date +%Y-%m-%d)"
    echo ""
    echo "### Added"
    echo "- New feature 1"
    echo ""
    echo "### Changed"
    echo "- Changed feature 1"
    echo ""
    echo "### Fixed"
    echo "- Bug fix 1"
    echo ""
    read -p "Open CHANGELOG.md in editor? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        ${EDITOR:-nano} CHANGELOG.md
    fi
else
    echo -e "${GREEN}✓ Found changelog entry for version $VERSION${NC}"
fi

echo ""
echo -e "${GREEN}Release preparation complete!${NC}"
echo ""
echo "Next steps:"
echo "1. Review the changes:"
echo "   git diff"
echo ""
echo "2. Run tests to ensure everything works:"
echo "   make test"
echo ""
echo "3. Commit the changes:"
echo "   git add custom_components/central_hudson/manifest.json CHANGELOG.md"
echo "   git commit -m \"Prepare release $VERSION\""
echo ""
echo "4. Push to GitHub:"
echo "   git push origin main"
echo ""
echo "5. Create the release on GitHub:"
echo "   Go to: https://github.com/$(git config --get remote.origin.url | sed 's/.*github.com[:/]\(.*\)\.git/\1/')/actions/workflows/release.yml"
echo "   Click 'Run workflow' and confirm"
echo ""

# Made with Bob
