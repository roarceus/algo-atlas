# External Integrations

**Analysis Date:** 2026-03-14

## APIs & External Services

**LeetCode GraphQL API:**
- Service: LeetCode.com problem data scraping
  - SDK/Client: `requests` library (HTTP client)
  - Endpoint: https://leetcode.com/graphql
  - Auth: User-agent rotation (no API key required)
  - Files: `src/algo_atlas/core/scraper.py`
  - Features:
    - GraphQL query for problem details, code snippets, examples, constraints
    - Automatic retry with exponential backoff (configurable max_retries, retry_delay)
    - User-agent rotation from 5 different browser user agents
    - Timeout support (default 30s, configurable)
    - Response validation and error handling
    - HTML content parsing for problem descriptions

**Claude Code CLI:**
- Service: Anthropic Claude AI for documentation generation
  - SDK/Client: CLI invocation via subprocess (`claude` command)
  - Executable: `claude` binary in PATH
  - Auth: Configured via Claude CLI setup/login (no env var needed in code)
  - Files: `src/algo_atlas/core/generator.py`
  - Command: `claude -p --output-format text`
  - Communication: Prompt passed via stdin to avoid Windows command-line escaping issues
  - Timeout: Configurable, default 300s (5 minutes)
  - Max tokens: Default 4096
  - Installation: `npm install -g @anthropic-ai/claude-code`
  - Status check: `check_claude_installed()` uses `shutil.which()` to verify PATH

**GitHub CLI:**
- Service: GitHub operations for vault repository
  - SDK/Client: `gh` CLI (subprocess invocation)
  - Executable: `gh` binary in PATH
  - Auth: GitHub CLI authentication via `gh auth login` (not in code)
  - Files: `src/algo_atlas/utils/github_ops.py`
  - Operations:
    - `gh pr create` - Create pull requests with body, title, labels
    - `gh label create` - Create/manage PR labels
    - `gh auth status` - Check authentication status
  - Installation: https://cli.github.com/
  - Status check: `check_gh_installed()` runs `gh auth status`

## Data Storage

**Vault Repository:**
- Type: Local Git repository (filesystem-based)
  - Not accessed by algo-atlas directly via API
  - Used via git operations in `src/algo_atlas/utils/git_ops.py`
  - Layout: Easy/Medium/Hard directories, each containing problem folders
  - Each problem folder contains: solution code file, README.md, test file

**Configuration Files:**
- Type: YAML files on local filesystem
  - Primary: `config/config.yaml` or user's home directory
  - Parsed by: `src/algo_atlas/config/settings.py`
  - Content: vault_path, leetcode settings, verifier settings, claude model selection

**File Storage:**
- Type: Local filesystem only
  - No cloud storage integration
  - Vault is a local Git repository that users push to GitHub manually or via `gh pr create`
  - Solutions written to disk before committing

**Caching:**
- Type: None
  - LeetCode problems are fetched fresh each time
  - No local problem cache implemented
  - Network request made for every `scrape_problem()` call

## Authentication & Identity

**LeetCode:**
- Auth Provider: None (public GraphQL API)
  - No authentication credentials needed
  - Uses user-agent rotation to avoid blocks
  - Referer header set to problem URL

**Claude Code CLI:**
- Auth Provider: Anthropic Claude setup (external to tool)
  - User logs in: `claude auth login`
  - Token stored by Claude CLI installation
  - algo-atlas calls `claude` subprocess directly
  - No API keys passed in environment variables

**GitHub:**
- Auth Provider: GitHub personal access tokens (external to tool)
  - User authenticates: `gh auth login`
  - Token stored by GitHub CLI
  - algo-atlas calls `gh` subprocess directly
  - No credentials in code

## Monitoring & Observability

**Error Tracking:**
- Type: None
  - No Sentry, Datadog, or similar
  - Application-level logging only

**Logs:**
- Approach: Custom logger in `src/algo_atlas/utils/logger.py`
  - Levels: DEBUG, INFO, WARNING, ERROR
  - Output: Console output with colored text (rich library)
  - Debug mode: Controlled via `--verbose`/`-v` flag
  - Log format: `[Component] Message` pattern (e.g., `[Scraper]`, `[Claude]`, `[Verifier]`)
  - File logging: Not currently implemented

## CI/CD & Deployment

**Hosting:**
- Type: GitHub Releases (no server deployment)
  - Package published to GitHub Release as wheel and source distribution
  - Installed locally via `pip install`

**CI Pipeline:**
- Service: GitHub Actions
  - Workflows location: `.github/workflows/`
  - Workflows:
    1. **ci.yml** - Main CI pipeline (lint, test on push/PR to main)
       - Runs on: ubuntu-latest
       - Python 3.12
       - Jobs: lint (black, isort, flake8), test (pytest with coverage)
       - Sets up Kotlin for testing
       - Uploads coverage to Codecov
    2. **release.yml** - Automated release (triggered after successful CI on main)
       - Uses python-semantic-release v10
       - Auto-bumps version in pyproject.toml and __init__.py
       - Creates GitHub Release with changelog
       - Builds wheel distribution via `python -m build`
    3. **dependency-check.yml** - Security scanning
       - Details not analyzed (file exists but not critical)

**Dependency Management:**
- No lock file for Python packages (not using pipenv, poetry)
- requirements.txt specifies min versions (>=)
- CI installs dependencies fresh: `pip install -e ".[dev]"`

## Environment Configuration

**Required env vars:**
- None hardcoded in application
- Configuration handled via YAML config file or defaults
- No `.env` file support (uses config.yaml instead)
- LeetCode timeout configurable in config.yaml

**Secrets location:**
- Claude Code CLI - Handled by `claude` CLI installation (user-managed)
- GitHub - Handled by `gh` CLI installation (user-managed)
- No secrets stored in code or env vars
- No API keys or tokens in application code

**GitHub Actions secrets:**
- `RELEASE_TOKEN` - GitHub personal access token for release automation
  - Used in release.yml for creating releases and publishing

## Webhooks & Callbacks

**Incoming:**
- Type: None
  - No webhook endpoints in application

**Outgoing:**
- GitHub PR creation: Creates PR via `gh pr create` (not a webhook)
- LeetCode GraphQL: One-way HTTP request to fetch problem data
- Claude CLI: One-way subprocess call to generate documentation

## Language Runtime Execution

**Solution Testing Infrastructure:**
- Location: `src/algo_atlas/languages/` (one module per language)
- Base interface: `base.py` - `LanguageSupport` ABC
- Execution approaches:
  - **Python** - ast.parse() for syntax, exec() for test execution
  - **JavaScript** - node --check for syntax, node for execution via JSON output
  - **TypeScript** - tsx (Node.js package) for both syntax and execution
  - **Java** - javac for compilation, java for execution with custom Main.java harness
  - **C++** - g++ -fsyntax-only for syntax, g++ compilation + binary execution
  - **C** - gcc for both compilation and execution (two-step)
  - **Go** - go build for compilation, separate execution to avoid timeout
  - **Rust** - rustc --emit=metadata for syntax, rustc for compilation + binary
  - **C#** - dotnet build for compilation (targets net8.0), Library output type for syntax
  - **Kotlin** - kotlinc for compilation, java -jar for execution
  - **Swift** - swiftc -typecheck for syntax, swiftc + binary execution
  - **Ruby** - ruby -c for syntax, ruby interpreter for execution (no compilation)
  - **PHP** - php -l for syntax, php interpreter for execution (no compilation)

**Test Harness Generation:**
- Each language generates test harness in memory
- Harness wraps solution code with:
  - Method extraction
  - Input argument parsing
  - Expected output assertion
  - JSON serialization of results for cross-platform output parsing
- Timeout protection: `src/algo_atlas/core/timeout.py` with signal-based timeout (Unix) and multiprocessing (Windows fallback)

---

*Integration audit: 2026-03-14*
