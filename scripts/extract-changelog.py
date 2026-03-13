#!/usr/bin/env python3
"""Extract changelog entry for a specific version."""

import re
import sys


def extract_changelog(version: str, changelog_path: str = "CHANGELOG.md") -> str:
    """Extract the changelog entry for a specific version.

    Args:
        version: Version number (e.g., "1.2.0")
        changelog_path: Path to CHANGELOG.md file

    Returns:
        Changelog entry for the version
    """
    try:
        with open(changelog_path, "r") as f:
            content = f.read()
    except FileNotFoundError:
        return f"No changelog found for version {version}"

    # Pattern to match version headers like ## [1.2.0] - 2026-03-12
    version_pattern = rf"## \[{re.escape(version)}\].*?\n(.*?)(?=\n## \[|\Z)"

    match = re.search(version_pattern, content, re.DOTALL)

    if match:
        changelog_entry = match.group(1).strip()
        if changelog_entry:
            return changelog_entry
        else:
            return f"Version {version} found but no changelog content available."
    else:
        return f"No changelog entry found for version {version}. Please update CHANGELOG.md."


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: extract-changelog.py <version>")
        sys.exit(1)

    version = sys.argv[1]
    changelog = extract_changelog(version)
    print(changelog)

# Made with Bob
