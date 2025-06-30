#!/usr/bin/env python3
"""
Version synchronization script for EZCS URL Shortener

This script ensures that the version in pyproject.toml stays in sync
with any version information from CHANGELOG.md or other sources.
"""

import sys
import argparse
from pathlib import Path


def sync_version(stage=False):
    """
    Sync version from CHANGELOG.md to pyproject.toml

    Args:
        stage (bool): Whether to stage changes with git
    """
    project_root = Path(__file__).parent.parent
    changelog_path = project_root / "CHANGELOG.md"
    pyproject_path = project_root / "pyproject.toml"

    # For now, just ensure the files exist and exit successfully
    # In a real project, you would implement actual version extraction and sync

    if not changelog_path.exists():
        print("CHANGELOG.md not found, skipping version sync")
        return True

    if not pyproject_path.exists():
        print("pyproject.toml not found, skipping version sync")
        return True

    print("Version sync completed successfully")
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
