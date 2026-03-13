#!/bin/bash
# Install git hooks for the project

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "Installing git hooks..."
echo ""

# Check if we're in a git repository
if [ ! -d .git ]; then
    echo "Error: Not in a git repository root directory"
    exit 1
fi

# Create pre-commit hook
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
# Pre-commit hook to run linting before each commit

echo "Running pre-commit checks..."
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Run linting
echo "🔍 Running ruff linting..."

# Try to run ruff, using python -m if direct command fails
if command -v ruff &> /dev/null; then
    RUFF_CMD="ruff"
else
    RUFF_CMD="python -m ruff"
fi

# Check code
if $RUFF_CMD check custom_components/ tests/ scraper/; then
    echo -e "${GREEN}✓ Ruff check passed${NC}"
else
    echo -e "${RED}✗ Ruff check failed${NC}"
    echo ""
    echo "Please fix the linting errors before committing."
    echo ""
    echo "To bypass this check (not recommended), use:"
    echo "  git commit --no-verify"
    exit 1
fi

# Check formatting
echo "🔍 Checking code formatting..."
if $RUFF_CMD format --check custom_components/ tests/ scraper/; then
    echo -e "${GREEN}✓ Formatting check passed${NC}"
else
    echo -e "${RED}✗ Formatting check failed${NC}"
    echo ""
    echo "Please run 'make format' to auto-fix formatting issues."
    echo ""
    echo "To bypass this check (not recommended), use:"
    echo "  git commit --no-verify"
    exit 1
fi

echo ""
echo -e "${GREEN}✓ All pre-commit checks passed!${NC}"
exit 0
EOF

# Make the hook executable
chmod +x .git/hooks/pre-commit

echo -e "${GREEN}✓ Pre-commit hook installed successfully!${NC}"
echo ""
echo "The hook will run 'make lint' before each commit."
echo "To bypass the hook (not recommended), use: git commit --no-verify"
echo ""

# Made with Bob
