# Codebase Structure

## Overview

AlgoAtlas uses a `src/` layout with a single installable package `algo_atlas`. All source lives under `src/algo_atlas/`; tests are co-located at the repo root under `tests/`.

---

## Directory Layout

```
algo-atlas/
├── src/
│   └── algo_atlas/              # Main package
│       ├── __init__.py          # Version: __version__ = "1.15.0"
│       ├── __main__.py          # python -m algo_atlas entry point
│       ├── cli/                 # CLI layer
│       │   ├── __init__.py      # Exports main()
│       │   ├── args.py          # argparse definitions (subcommands + flags)
│       │   ├── batch.py         # Batch processing loop
│       │   ├── input_handlers.py# User prompts, startup checks
│       │   └── workflows.py     # Top-level workflow orchestration (main())
│       ├── config/              # Configuration
│       │   ├── __init__.py
│       │   └── settings.py      # Settings dataclass + YAML loader + global singleton
│       ├── core/                # Core business logic
│       │   ├── __init__.py
│       │   ├── generator.py     # Claude CLI invocation + markdown cleaning
│       │   ├── scraper.py       # LeetCode GraphQL scraper + ProblemData
│       │   ├── test_parser.py   # Parse test cases from problem examples
│       │   ├── timeout.py       # Cross-platform subprocess timeout helper
│       │   └── verifier.py      # Solution verification orchestrator
│       ├── languages/           # Multi-language support
│       │   ├── __init__.py      # Lazy registry: get_language(), list_languages()
│       │   ├── base.py          # LanguageSupport ABC + LanguageInfo, SyntaxResult, TestResult
│       │   ├── python.py        # Python: AST syntax, exec() test runner
│       │   ├── javascript.py    # JavaScript: node --check, subprocess JSON runner
│       │   ├── typescript.py    # TypeScript: npx tsx, shutil.which() for Windows
│       │   ├── java.py          # Java: javac compile + java run, Main.java harness
│       │   ├── kotlin.py        # Kotlin: kotlinc + java -jar, ASCII JSON escaping
│       │   ├── cpp.py           # C++: g++ -fsyntax-only + g++ compile + binary
│       │   ├── c.py             # C: gcc two-step compile + run
│       │   ├── go.py            # Go: go build + binary (separate to avoid timeout)
│       │   ├── rust.py          # Rust: rustc --emit=metadata, single-file harness
│       │   ├── csharp.py        # C#: dotnet build, OutputType=Library, net8.0
│       │   ├── swift.py         # Swift: swiftc -typecheck, main.swift (lowercase)
│       │   ├── ruby.py          # Ruby: ruby -c, ruby main.rb (interpreted)
│       │   └── php.py           # PHP: php -l, php main.php (interpreted)
│       └── utils/               # Shared utilities
│           ├── __init__.py
│           ├── file_manager.py  # Vault file writes (markdown → Easy/Medium/Hard/)
│           ├── git_ops.py       # Git commit/push operations on vault repo
│           ├── github_ops.py    # GitHub PR creation via gh CLI
│           ├── logger.py        # Rich terminal logger + global singleton
│           ├── prompts.py       # Claude prompt construction
│           ├── vault_files.py   # Vault directory validation + file existence checks
│           ├── vault_readme.py  # README.md generation/update for vault
│           └── vault_search.py  # Search index over vault markdown files
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # Shared fixtures (sample_problem, mock_graphql_response, language solutions)
│   ├── test_languages.py        # Cross-language registry assertions (all 13 slugs)
│   ├── test_scraper.py          # Scraper unit tests (mocked HTTP)
│   ├── test_verifier.py         # Verifier unit tests
│   ├── test_file_manager.py     # File manager unit tests
│   ├── test_cli.py              # CLI workflow tests
│   ├── test_logger.py           # Logger unit tests
│   ├── test_python.py           # Python language: 24 tests
│   ├── test_javascript.py       # JavaScript language: 24 tests
│   ├── test_typescript.py       # TypeScript language: 24 tests
│   ├── test_java.py             # Java language: 24 tests
│   ├── test_kotlin.py           # Kotlin language: 24 tests
│   ├── test_cpp.py              # C++ language: 24 tests
│   ├── test_c.py                # C language: 24 tests
│   ├── test_go.py               # Go language: 24 tests
│   ├── test_rust.py             # Rust language: 24 tests
│   ├── test_csharp.py           # C# language: 24 tests
│   ├── test_swift.py            # Swift language: 24 tests
│   ├── test_ruby.py             # Ruby language: 24 tests
│   └── test_php.py              # PHP language: 24 tests
├── config/
│   └── config.yaml              # User config (vault_path, language.default, claude.model, etc.)
├── .github/
│   └── workflows/
│       └── ci.yml               # GitHub Actions CI (lint + test matrix)
├── pyproject.toml               # Build config, dependencies, tool settings
├── README.md                    # Project docs + supported languages table
└── CHANGELOG.md                 # Semantic release changelog
```

---

## Key File Locations

| Purpose | File |
|---------|------|
| CLI entry point | `src/algo_atlas/cli/workflows.py:main()` |
| Argument parsing | `src/algo_atlas/cli/args.py` |
| Language ABC | `src/algo_atlas/languages/base.py` |
| Language registry | `src/algo_atlas/languages/__init__.py` |
| Config loading | `src/algo_atlas/config/settings.py` |
| Claude invocation | `src/algo_atlas/core/generator.py` |
| LeetCode scraper | `src/algo_atlas/core/scraper.py` |
| Solution verifier | `src/algo_atlas/core/verifier.py` |
| Vault file writer | `src/algo_atlas/utils/file_manager.py` |
| Terminal logger | `src/algo_atlas/utils/logger.py` |
| Shared test fixtures | `tests/conftest.py` |

---

## Naming Conventions

### Files
- Module files: `snake_case.py` (e.g., `file_manager.py`, `vault_files.py`)
- Test files: `test_<module>.py` (e.g., `test_javascript.py`)
- Language files: named by language slug (e.g., `python.py`, `csharp.py`)

### Classes
- PascalCase: `LanguageSupport`, `JavaScriptLanguage`, `ProblemData`, `Settings`
- Language classes: `{Name}Language` (e.g., `KotlinLanguage`, `TypeScriptLanguage`)

### Functions
- `snake_case` throughout
- Private helpers prefixed with `_` (e.g., `_build_test_harness()`, `_python_to_java_literal()`)
- Module-level constants: `UPPER_SNAKE_CASE` (e.g., `_METHOD_PATTERN`, `_RUST_JSON_HELPERS`)

### Variables
- `snake_case` throughout
- Private module globals: `_settings`, `_logger`, `_REGISTRY`

---

## Where to Add New Code

### New language support
1. Create `src/algo_atlas/languages/{slug}.py` implementing `LanguageSupport`
2. Register in `src/algo_atlas/languages/__init__.py` (add import + `_REGISTRY[slug] = LangClass()`)
3. Add fixtures to `tests/conftest.py` (solution code + mock_graphql_response snippet)
4. Create `tests/test_{slug}.py` with 24 tests across 6 classes
5. Update `tests/test_languages.py` to assert slug present
6. Update `tests/test_scraper.py` snippet count assertion
7. Add language to `README.md` supported languages table

### New CLI subcommand
1. Add subparser in `src/algo_atlas/cli/args.py`
2. Add handler function in `src/algo_atlas/cli/workflows.py`
3. Wire `args.command == "{name}"` in `main()`

### New utility
- Add to `src/algo_atlas/utils/` if reused across multiple modules
- Add to the relevant module directly if only used in one place

### New config option
1. Add field to appropriate `*Settings` dataclass in `src/algo_atlas/config/settings.py`
2. Wire loading in `Settings._load_from_file()`
3. Document in `config/config.yaml` with comments

---

## Special Directories

| Directory | Purpose |
|-----------|---------|
| `.planning/` | GSD workflow planning documents |
| `.planning/codebase/` | Codebase map documents (this directory) |
| `config/` | User-editable YAML configuration |
| `.github/workflows/` | CI/CD pipeline definitions |
| `src/` | PEP 517 src layout — keeps package separate from project root |
