# Architecture

**Analysis Date:** 2026-03-14

## Pattern Overview

**Overall:** Multi-layer CLI application with pluggable language support and external service integration

**Key Characteristics:**
- Pluggable language support system with lazy registration
- Clear separation between CLI orchestration, core logic, and utilities
- External integrations: LeetCode GraphQL API (scraper), Claude AI (generator), GitHub CLI (vault ops), Git (version control)
- Language-agnostic test harness execution with language-specific implementations
- Configuration-driven behavior with YAML settings

## Layers

**CLI Layer:**
- Purpose: Command-line interface, argument parsing, user input/output, workflow orchestration
- Location: `src/algo_atlas/cli/`
- Contains: Argument parsing (`args.py`), batch processing (`batch.py`), input handlers (`input_handlers.py`), workflow orchestration (`workflows.py`)
- Depends on: Core, Languages, Config, Utils
- Used by: Entry point (`main()` in `workflows.py`)

**Core Logic Layer:**
- Purpose: Central business logic for scraping, generation, verification, and test parsing
- Location: `src/algo_atlas/core/`
- Contains: Problem scraper (`scraper.py`), Claude integration (`generator.py`), solution verification (`verifier.py`), test case parsing (`test_parser.py`), timeout utilities (`timeout.py`)
- Depends on: Languages (for test execution), Config (settings), Utils (logging, prompts)
- Used by: CLI layer, Languages module

**Language Support Layer:**
- Purpose: Pluggable, extensible language-specific implementations
- Location: `src/algo_atlas/languages/`
- Contains: Abstract base (`base.py`), language implementations (Python, JavaScript, TypeScript, Java, C++, C, Go, Rust, C#, Kotlin, Swift, Ruby, PHP), registry system (`__init__.py`)
- Depends on: Config (settings), Core (timeout utilities)
- Used by: Core verifier, CLI workflows

**Configuration Layer:**
- Purpose: Settings management and environment configuration
- Location: `src/algo_atlas/config/`
- Contains: Settings classes for LeetCode, Verifier, Claude, Language preferences
- Depends on: None (lowest-level configuration)
- Used by: All layers for environment configuration

**Utilities Layer:**
- Purpose: Cross-cutting concerns including logging, file operations, Git operations, GitHub integration, prompts
- Location: `src/algo_atlas/utils/`
- Contains: Rich-based logger (`logger.py`), vault file operations (`vault_files.py`), Git operations (`git_ops.py`), GitHub CLI operations (`github_ops.py`), vault README generation (`vault_readme.py`), vault search (`vault_search.py`), prompt templates (`prompts.py`), aggregation module (`file_manager.py`)
- Depends on: Config (settings), external: requests, pyyaml, rich
- Used by: All layers

## Data Flow

**Single Problem Workflow:**

1. CLI receives URL input from user → validates with `validate_leetcode_url()`
2. `scrape_problem()` calls LeetCode GraphQL API → parses response → returns `ProblemData`
3. User provides solution code via stdin or file
4. `verify_solution()` delegates to language-specific `run_test_case()` → executes tests
5. `generate_documentation()` passes ProblemData + solution to Claude CLI → receives markdown
6. `build_readme_content()` wraps generated content with problem metadata
7. If not dry-run: `create_problem_folder()` → `save_solution_file()` + `save_markdown()`
8. Git operations: `create_and_checkout_branch()` → `stage_files()` → `commit_changes()` → `push_branch()`
9. `create_pull_request()` calls GitHub CLI with labels
10. `update_vault_readme()` regenerates stats and topic index

**Batch Workflow:**

1. CLI parses batch file (JSON or text format)
2. Iterates items, running single problem workflow for each
3. On error: either stops or continues based on `--continue-on-error` flag
4. Collects results and reports summary

**State Management:**
- CLI maintains `Logger` instance for all output
- `Settings` object loaded once at startup (immutable during execution)
- Language registry populated lazily on first access
- `ProblemData` passed through workflow functions as immutable container
- Git operations mutate filesystem and remote state

## Key Abstractions

**ProblemData:**
- Purpose: Container for scraped LeetCode problem metadata
- Examples: `src/algo_atlas/core/scraper.py` (dataclass definition)
- Pattern: Immutable dataclass with examples, constraints, test cases, code snippets

**LanguageSupport:**
- Purpose: Abstract interface for language-specific implementations
- Examples: `src/algo_atlas/languages/base.py` (ABC), `src/algo_atlas/languages/python.py` (concrete), `src/algo_atlas/languages/java.py` (concrete)
- Pattern: Abstract base class with concrete implementations registered in global registry; methods: `check_syntax()`, `extract_method_name()`, `count_method_params()`, `run_test_case()`

**GenerationResult:**
- Purpose: Container for Claude API response with success/error handling
- Examples: `src/algo_atlas/core/generator.py`
- Pattern: Dataclass with `success: bool`, `content: Optional[str]`, `error: Optional[str]`

**VerificationResult:**
- Purpose: Container for solution verification outcome with test details
- Examples: `src/algo_atlas/core/verifier.py`
- Pattern: Dataclass tracking syntax validity, test pass/fail counts, and individual `TestResult` objects

**Settings:**
- Purpose: Hierarchical configuration with YAML file support
- Examples: `src/algo_atlas/config/settings.py`
- Pattern: Nested dataclasses for LeetCode, Verifier, Claude, Language settings; loads from multiple search paths

## Entry Points

**CLI Main:**
- Location: `src/algo_atlas/cli/workflows.py::main()`
- Triggers: User runs `algo-atlas` or `algo-atlas status`/`algo-atlas search`/`algo-atlas batch`
- Responsibilities: Parse arguments, run startup checks, dispatch to appropriate command handler (status/search/batch/default), manage main loop for single problem workflow

**Startup Checks:**
- Location: `src/algo_atlas/cli/input_handlers.py::startup_checks()`
- Triggers: Called at beginning of `main()` before any workflow
- Responsibilities: Validate Claude CLI installed, validate vault repo structure, check language runtimes available, display configuration status

## Error Handling

**Strategy:** Exceptions bubble up to CLI layer; CLI logs errors and either continues (batch mode with `--continue-on-error`) or exits (fatal errors during startup)

**Patterns:**
- Scraper: Network errors caught, retried with exponential backoff (via `requests` library)
- Generator: Claude CLI timeouts caught, GenerationResult returned with error
- Verifier: Language-specific exceptions caught per test case, individual TestResult marked failed
- File Manager: Path errors logged and returned as tuple `(success: bool, message: str)`
- Git operations: Command failures returned as tuple `(success: bool, message: str)` with user-friendly messages

## Cross-Cutting Concerns

**Logging:** Rich-based logger in `src/algo_atlas/utils/logger.py::Logger` class provides colored output, progress spinners, status contexts, and interactive prompts. Instantiated once per CLI session via `get_logger()` singleton.

**Validation:**
- URL validation: `validate_leetcode_url()` in scraper
- Code syntax: `check_syntax()` via language implementations
- Vault structure: `validate_vault_repo()` in vault_files

**Authentication:**
- Claude CLI: Already authenticated on user's machine (no API keys handled)
- GitHub: `gh` CLI already authenticated (no tokens handled)
- LeetCode: Public GraphQL endpoint (no auth required)

**Test Execution Timeout:**
- Core timeout wrapper: `src/algo_atlas/core/timeout.py::_run_with_timeout()` with configurable timeout
- Default: 5 seconds per test case (configurable via `VerifierSettings.execution_timeout`)
- Language-specific implementations use this timeout when calling `run_test_case()`

---

*Architecture analysis: 2026-03-14*
