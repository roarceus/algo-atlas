# Technology Stack

**Analysis Date:** 2026-03-14

## Languages

**Primary:**
- Python 3.10+ - Core CLI application, scraper, verifier, generator
  - Minimum: 3.10, Tested: 3.10, 3.11, 3.12
  - Location: `src/algo_atlas/`

**Secondary (Support for Solution Languages):**
- JavaScript - Solution testing via Node.js
- TypeScript - Solution testing via tsx CLI
- Java - Solution compilation/testing via javac and java
- C++ - Solution compilation/testing via g++
- C - Solution compilation/testing via gcc
- Go - Solution compilation/testing via go build
- Rust - Solution syntax checking and compilation via rustc
- C# - Solution compilation/testing via dotnet CLI
- Kotlin - Solution compilation/testing via kotlinc
- Swift - Solution testing via swiftc
- Ruby - Solution testing via ruby interpreter
- PHP - Solution testing via php CLI

## Runtime

**Environment:**
- Python 3.10+
- CPython (no specific implementation required)

**Package Manager:**
- pip (comes with Python)
- Lockfile: `requirements.txt` present - development dependencies also in `requirements-dev.txt`

## Frameworks

**Core:**
- No web framework used - CLI-only application

**Testing:**
- pytest 7.4.0+ - Test runner for unit tests
  - Config: `pyproject.toml` [tool.pytest.ini_options]
  - Command: `pytest tests/ -v --cov=algo_atlas --cov-report=term-missing`

**Code Quality:**
- black 23.0.0+ - Code formatter, configured for 88-char line length
- isort 5.12.0+ - Import sorting with black profile
- flake8 6.1.0+ - Linting with flake8-bugbear plugin
- mypy 1.5.0+ - Type checking
  - Config: `pyproject.toml` [tool.mypy], ignores missing imports

**Pre-commit Hooks:**
- pre-commit 3.4.0+ - Hook orchestration
  - Config: `.pre-commit-config.yaml`
  - Hooks: trailing-whitespace, end-of-file-fixer, check-yaml, large-file detection, merge-conflict detection, private-key detection
  - Versions: black 24.1.1, isort 5.13.2, flake8 7.0.0, mypy v1.8.0

## Key Dependencies

**Critical:**
- requests 2.31.0+ - HTTP client for LeetCode GraphQL API
  - Location: `src/algo_atlas/core/scraper.py`
  - Purpose: Makes authenticated requests to https://leetcode.com/graphql
  - Features: Retry logic with exponential backoff, custom headers, user-agent rotation

- pyyaml 6.0+ - YAML configuration file parsing
  - Location: `src/algo_atlas/config/settings.py`
  - Purpose: Loads configuration from config.yaml files

- rich 13.0.0+ - Terminal UI and output formatting
  - Location: Throughout CLI modules
  - Purpose: Panels, spinners, progress bars, colored text, table formatting

**Infrastructure:**
- No database ORM
- No async/await framework
- No web server

## Configuration

**Environment:**
- Configuration loaded from YAML file in one of these locations (searched in order):
  1. `./config/config.yaml`
  2. `./config.yaml`
  3. `~/.config/algo-atlas/config.yaml`
  4. `~/.algo-atlas/config.yaml`
- If no config file found, defaults are used
- Key config sections:
  - `vault_path` - Required for vault operations
  - `leetcode.timeout` - Default 30s
  - `leetcode.max_retries` - Default 3
  - `leetcode.retry_delay` - Default 2s (with exponential backoff)
  - `verifier.execution_timeout` - Default 5s
  - `claude.model` - Optional model selection
  - `language.default` - Default language, default "python3"

**Build:**
- `pyproject.toml` - Primary package configuration (setuptools backend)
  - Build backend: setuptools
  - Project metadata, dependencies, entry point, tool configurations
- `setup.py` - Minimal setup script (delegates to pyproject.toml)
- CLI entry point: `algo_atlas.cli:main` (installed as `algo-atlas` command)

## Platform Requirements

**Development:**
- Python 3.10+
- pip for package installation
- For code quality: black, isort, flake8, mypy
- Pre-commit hooks require git

**Production/Runtime:**
- Python 3.10+ for CLI
- Language-specific runtimes for solution testing (optional based on which languages used):
  - Node.js (for JavaScript/TypeScript)
  - JDK (for Java/Kotlin)
  - GCC/G++ (for C/C++)
  - Go toolchain (for Go)
  - Rust toolchain (for Rust)
  - .NET SDK 8+ (for C#)
  - Swift toolchain (for Swift)
  - Ruby interpreter (for Ruby)
  - PHP interpreter (for PHP)
- Claude Code CLI (for documentation generation): `npm install -g @anthropic-ai/claude-code`
- GitHub CLI (for PR creation): https://cli.github.com/

**Deployment:**
- Build distribution: `python -m build`
- Package format: Wheel + source distribution
- PyPI-ready (though currently released via GitHub Releases)
- Semantic versioning with python-semantic-release
- Release automation via GitHub Actions workflow

## Semantic Versioning

**Release Process:**
- Tool: python-semantic-release v10
- Triggered on successful CI for push to main
- Automatic version bumping based on conventional commits
- GitHub Release creation
- Package build and distribution

---

*Stack analysis: 2026-03-14*
