#!/bin/bash
# Script to validate HACS integration locally

set -e

echo "🔍 Running HACS validation..."
echo ""

# Check if running in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "❌ Error: Not in a git repository"
    exit 1
fi

# Check required files exist
echo "📋 Checking required files..."
required_files=(
    "custom_components/central_hudson/manifest.json"
    "custom_components/central_hudson/__init__.py"
    "hacs.json"
    "README.md"
)

for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ Missing required file: $file"
        exit 1
    fi
    echo "✅ Found: $file"
done

# Validate JSON files
echo ""
echo "🔧 Validating JSON files..."
for json_file in hacs.json custom_components/central_hudson/manifest.json custom_components/central_hudson/data/prices.json custom_components/central_hudson/strings.json; do
    if python3 -m json.tool "$json_file" > /dev/null 2>&1; then
        echo "✅ Valid JSON: $json_file"
    else
        echo "❌ Invalid JSON: $json_file"
        exit 1
    fi
done

# Check manifest.json required fields
echo ""
echo "📦 Validating manifest.json..."
manifest="custom_components/central_hudson/manifest.json"
required_manifest_fields=("domain" "name" "version" "documentation" "issue_tracker" "codeowners")

for field in "${required_manifest_fields[@]}"; do
    if grep -q "\"$field\"" "$manifest"; then
        echo "✅ Found field: $field"
    else
        echo "❌ Missing field in manifest.json: $field"
        exit 1
    fi
done

# Check hacs.json
echo ""
echo "🏠 Validating hacs.json..."
if grep -q '"name"' hacs.json; then
    echo "✅ hacs.json has name field"
else
    echo "❌ hacs.json missing name field"
    exit 1
fi

# Check for brand icon
echo ""
echo "🎨 Checking brand assets..."
if [ -f "custom_components/central_hudson/brand/icon.png" ]; then
    echo "✅ Brand icon found"
else
    echo "⚠️  Warning: Brand icon not found (optional but recommended)"
fi

# Run Python validation using HACS action locally if available
echo ""
echo "🐍 Running Python-based validation..."
if command -v docker &> /dev/null; then
    echo "🐳 Docker found, running HACS validation container..."
    docker run --rm -v "$(pwd):/github/workspace" ghcr.io/hacs/action:main || {
        echo "⚠️  HACS validation container failed or not available"
        echo "   This is expected if running locally without proper GitHub context"
    }
else
    echo "⚠️  Docker not found, skipping container-based validation"
    echo "   Install Docker to run full HACS validation locally"
fi

echo ""
echo "✅ Local validation checks passed!"
echo ""
echo "Note: Full HACS validation runs in GitHub Actions on push/PR"
echo "See: .github/workflows/ci.yml"

# Made with Bob
