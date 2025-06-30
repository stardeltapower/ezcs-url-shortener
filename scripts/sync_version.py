#!/usr/bin/env python3
"""
Version synchronization script for EZCS URL Shortener

This script ensures that the version in pyproject.toml stays in sync
with any version information from CHANGELOG.md or other sources.
"""

import sys
import argparse
import re
from pathlib import Path


def extract_version_from_changelog(changelog_path):
    """
    Extract the latest version from CHANGELOG.md

    Args:
        changelog_path (Path): Path to CHANGELOG.md

    Returns:
        str or None: Version string if found, None otherwise
    """
    if not changelog_path.exists():
        return None

    try:
        with open(changelog_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Look for version patterns like ## [1.0.0] or ## v1.0.0
        version_pattern = r'##\s*\[?v?(\d+\.\d+\.\d+)\]?'
        match = re.search(version_pattern, content)

        if match:
            return match.group(1)

    except Exception as e:
        print(f"Error reading CHANGELOG.md: {e}")

    return None


def update_pyproject_version(pyproject_path, new_version):
    """
    Update the version in pyproject.toml

    Args:
        pyproject_path (Path): Path to pyproject.toml
        new_version (str): New version string

    Returns:
        bool: True if updated successfully, False otherwise
    """
    try:
        with open(pyproject_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Update only the project version line (more specific pattern)
        # This pattern looks for 'version = "..."' within the [project] section
        version_pattern = r'(\[project\].*?version\s*=\s*["\'])([^"\']+)(["\'])'

        def replace_version(match):
            return match.group(1) + new_version + match.group(3)

        new_content = re.sub(version_pattern, replace_version, content, flags=re.DOTALL)

        if new_content != content:
            with open(pyproject_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"Updated project version to {new_version} in pyproject.toml")
            return True
        else:
            print("No version update needed in pyproject.toml")
            return True

    except Exception as e:
        print(f"Error updating pyproject.toml: {e}")
        return False


def sync_version(stage=False):
    """
    Sync version from CHANGELOG.md to pyproject.toml

    Args:
        stage (bool): Whether to stage changes with git
    """
    project_root = Path(__file__).parent.parent
    changelog_path = project_root / "CHANGELOG.md"
    pyproject_path = project_root / "pyproject.toml"

    if not pyproject_path.exists():
        print("pyproject.toml not found, cannot sync version")
        return False

    # If CHANGELOG.md doesn't exist, just ensure pyproject.toml is valid
    if not changelog_path.exists():
        print("CHANGELOG.md not found, skipping version sync")
        return True

    # Extract version from changelog
    changelog_version = extract_version_from_changelog(changelog_path)

    if changelog_version:
        print(f"Found version {changelog_version} in CHANGELOG.md")
        success = update_pyproject_version(pyproject_path, changelog_version)

        if success and stage:
            import subprocess
            try:
                subprocess.run(['git', 'add', str(pyproject_path)],
                             cwd=project_root, check=True)
                print("Staged pyproject.toml changes")
            except subprocess.CalledProcessError as e:
                print(f"Failed to stage changes: {e}")
                return False

        return success
    else:
        print("No version found in CHANGELOG.md, keeping current pyproject.toml version")
        return True


def main():
    parser = argparse.ArgumentParser(description="Sync version information")
    parser.add_argument("--stage", action="store_true", help="Stage changes with git")

    args = parser.parse_args()

    success = sync_version(stage=args.stage)

    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
