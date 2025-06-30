# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.1] - 2025-06-30

### Fixed

- Fixed sync_version.py script to work with pyproject.toml instead of setup.py
- Fixed ruff target-version configuration to use proper Python version (py38)
- Fixed pytest minversion to use proper pytest version (6.0)
- Improved version synchronization to only update project version, not tool configurations

### Changed

- Enhanced sync_version.py with proper regex patterns for version extraction and updating

## [0.1.0] - 2025-06-30

### Added

- Initial project setup with FastAPI framework
- URL shortening functionality with custom or auto-generated codes
- API key authentication system with bcrypt encryption
- Admin token protection for API key management
- Environment-aware configuration (development vs production modes)
- Alembic database migrations
- Comprehensive test suite with pytest
- Pre-commit hooks for code quality
- Deployment configurations for nginx and systemd
- Documentation with usage examples
- GitHub Actions workflows for CI/CD

[Unreleased]: https://github.com/rsmith/ezcs-url-shortener/compare/v0.1.1...HEAD
[0.1.1]: https://github.com/rsmith/ezcs-url-shortener/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/rsmith/ezcs-url-shortener/releases/tag/v0.1.0
