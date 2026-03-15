# Coding Conventions

**Analysis Date:** 2026-03-14

## Naming Patterns

**Files:**
- Module files: `snake_case.py` (e.g., `settings.py`, `scraper.py`, `verifier.py`)
- Class files: `snake_case.py` containing PascalCase classes (e.g., `base.py` with `LanguageSupport`)
- Language implementations: `{language}.py` in `src/algo_atlas/languages/` (e.g., `python.py`, `java.py`, `typescript.py`)
- Test files: `test_{module}.py` in `tests/` directory (e.g., `test_scraper.py`, `test_java.py`)
- Fixture/config files: `conftest.py` for pytest shared fixtures

**Functions:**
- Public functions: `snake_case` (e.g., `get_language()`, `check_syntax()`, `parse_args()`)
- Private functions: `_leading_underscore_snake_case()` (e.g., `_resolve_language()`, `_compare_results()`)
- Static methods: `_method_name()` convention for private static methods (e.g., `_build_exec_namespace()`)
- Class methods: `@classmethod` with `_method_name()` for private helpers (e.g., `_extract_solution_class()`)

**Variables:**
- Local variables: `snake_case` (e.g., `solution_code`, `test_cases`, `expected_output`)
- Constants: `SCREAMING_SNAKE_CASE` (e.g., `ALGOATLAS_THEME`, `_UNICODE`, `_CHECK`)
- Dataclass fields: `snake_case` (e.g., `vault_path`, `execution_timeout`)
- Instance attributes: `snake_case` (e.g., `self.verbose`, `self.console`)

**Types:**
- Classes: `PascalCase` (e.g., `PythonLanguage`, `JavaLanguage`, `LanguageSupport`, `Settings`)
- Dataclasses: `PascalCase` for type names (e.g., `LanguageInfo`, `SyntaxResult`, `TestResult`)
- Type hints: Full typing module imports (e.g., `list[str]`, `Optional[str]`, `dict[str, Any]`)

## Code Style

**Formatting:**
- Tool: `black` (line length: 88)
- Enforcement: Pre-commit hook via `.pre-commit-config.yaml`
- Configuration in `pyproject.toml`:
  ```
  [tool.black]
  line-length = 88
  target-version = ["py310", "py311", "py312"]
  ```

**Linting:**
- Tool: `flake8` (version 7.0.0)
- Configuration: Max line length 88, ignore E203 (whitespace before ':') and W503 (line break before binary operator)
- Pre-commit hook enforces linting before commits
- Additional dependency: `flake8-bugbear` for extra checks

**Code Quality:**
- Type checking: `mypy` (version 1.8.0)
- Configuration: `disallow_untyped_defs = true` - all functions must have type hints
- Python version: 3.10+ required (`requires-python = ">=3.10"`)

## Import Organization

**Order:**
1. Standard library imports (e.g., `import json`, `import re`, `from pathlib import Path`)
2. Third-party imports (e.g., `import yaml`, `import requests`, `from rich.console import Console`)
3. Local imports (e.g., `from algo_atlas.config.settings import get_settings`)

**Pattern:**
```python
# Standard library
import json
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

# Third-party
import requests
from rich.console import Console

# Local
from algo_atlas.config.settings import get_settings
from algo_atlas.languages.base import LanguageSupport
```

**Path Aliases:**
- No path aliases configured (`jsconfig.json` not used in Python project)
- Import from package root: `from algo_atlas.module import name`
- Explicit relative imports avoided; always use absolute imports from `algo_atlas` root

**Import Organization Tool:** `isort`
- Configuration: `profile = "black"`, `line_length = 88`
- Pre-commit enforces isort before commits
- Removes unused imports automatically (causes CI failure if not applied)

## Error Handling

**Patterns:**

**Specific Exception Catching:**
```python
try:
    ast.parse(code)
except SyntaxError as e:
    return SyntaxResult(valid=False, error_message=str(e.msg) if e.msg else str(e))
```
- Catch specific exception types, not bare `except:`
- Examples in codebase: `except SyntaxError`, `except json.JSONDecodeError`, `except ValueError`, `except subprocess.TimeoutExpired`

**Custom Errors with Context:**
```python
raise ValueError(f"Batch file not found: {file_path}")
raise ValueError(f"Unsupported language: {language}")
```
- Raise with descriptive message including context
- Use f-strings for error message formatting

**Graceful Degradation:**
```python
def can_run_tests(self) -> bool:
    return shutil.which("javac") is not None and shutil.which("java") is not None
```
- Check runtime availability (javac, java, gcc, etc.) before executing
- Return `False` or handle gracefully rather than crash

**None/Optional Returns:**
```python
def extract_method_name(self, code: str) -> Optional[str]:
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return None
    # ... logic ...
    return None
```
- Return `None` for missing/invalid data rather than raising
- Use `Optional[T]` type hint when returning `None` is valid

**Subprocess Error Handling:**
```python
try:
    result = subprocess.run(["javac", str(src_path)], timeout=15, capture_output=True)
except subprocess.TimeoutExpired:
    return SyntaxResult(valid=False, error_message="Compilation timed out")
except FileNotFoundError:
    return SyntaxResult(valid=False, error_message="javac not found")
```
- Catch `TimeoutExpired` and `FileNotFoundError` separately
- Parse stderr for error location/message

**Context Managers for Cleanup:**
```python
@contextmanager
def status(self, message: str) -> Generator[Optional[Status], None, None]:
    if self._progress_active:
        yield None
    else:
        with self.console.status(...) as status:
            yield status
```
- Use `@contextmanager` for resource cleanup
- Ensure `finally` blocks or context manager exit code runs

## Logging

**Framework:** Custom `Logger` class in `src/algo_atlas/utils/logger.py` using `rich.console.Console`

**Methods:**
- `logger.success(message)` — Green checkmark + green text
- `logger.error(message)` — Red X + red text
- `logger.warning(message)` — Yellow ! + yellow text
- `logger.info(message)` — Blue bullet + text
- `logger.step(message)` — Cyan arrow + text (for workflow steps)
- `logger.debug(message)` — Dim text (only printed if `verbose=True`)

**Patterns:**

**Debug Output (verbose mode):**
```python
logger = get_logger()
logger.debug(f"[Claude] Command: claude -p --output-format text")
logger.debug(f"[Claude] Prompt length: {len(prompt)} chars")
```
- Use `[Category]` prefix in debug messages
- Only printed when `-v`/`--verbose` flag is used
- Debug calls on generators, scrapers, and Claude integration

**Step Output (workflows):**
```python
logger.step("Scraping problem from LeetCode...")
logger.step("Verifying solution...")
```
- Step messages for user-visible workflow progression

**Status/Progress:**
```python
with logger.status("Processing...") as status:
    # Long operation
    if status:
        status.update("Almost done...")
```
- Context manager for spinner during long operations
- Degrades gracefully when progress bar is active

**Global Logger:**
```python
_logger: Optional[Logger] = None

def get_logger(verbose: bool = False) -> Logger:
    global _logger
    if _logger is None:
        _logger = Logger(verbose=verbose)
    return _logger
```
- Singleton pattern with lazy initialization
- Call `get_logger()` in modules, don't instantiate directly

## Comments

**When to Comment:**
- Complex algorithm logic (e.g., error line parsing in `java.py` javac output)
- Workarounds for platform-specific issues (e.g., Git Bash Unicode handling)
- Non-obvious intent or correctness requirements

**JSDoc/Docstring Pattern:**
All public functions and classes use Google-style docstrings:

```python
def run_test_cases(
    solution_code: str,
    test_cases: list[str],
    examples: list[dict],
    expected_outputs: Optional[list[Any]] = None,
    language: Optional[str] = None,
) -> VerificationResult:
    """Run all test cases against solution.

    Args:
        solution_code: Solution code.
        test_cases: Raw test case input strings from LeetCode.
        examples: Parsed examples with input/output.
        expected_outputs: Optional list of expected outputs.
        language: Language slug. Defaults to Python when None.

    Returns:
        VerificationResult with all test outcomes.

    Raises:
        ValueError: If language slug is not recognized.
    """
```

**ABC Abstract Methods:**
```python
@abstractmethod
def check_syntax(self, code: str) -> SyntaxResult:
    """Check syntax validity of the given code.

    Args:
        code: Source code to check.

    Returns:
        SyntaxResult with validation status.
    """
    ...
```

## Function Design

**Size:**
- Most functions: 20-50 lines
- Complex workflows: Up to 100 lines with clear sections
- Language-specific handlers: 50-150 lines (e.g., `run_test_case()` methods with subprocess setup)

**Parameters:**
- Maximum 4-5 parameters for public functions
- Use dataclasses for related parameters: `LanguageInfo`, `Settings`, `ProblemData`
- Optional parameters at end with `None` defaults
- Type hints required for all parameters

**Return Values:**
- Single return type (not `Tuple[bool, str]` - use dataclass instead)
- Dataclass returns for complex results: `SyntaxResult`, `TestResult`, `VerificationResult`
- `Optional[T]` for nullable returns instead of exceptions
- Early returns for error cases:
  ```python
  if condition:
      return error_result
  # happy path continues
  ```

## Module Design

**Exports:**
- `__init__.py` files use explicit imports, no `from .module import *`
- Public API re-exported with `# noqa: F401` for flake8
  ```python
  # src/algo_atlas/languages/__init__.py
  from algo_atlas.languages.python import PythonLanguage  # noqa: F401
  from algo_atlas.languages.java import JavaLanguage  # noqa: F401
  ```

**Module Organization:**
- `src/algo_atlas/languages/` — Language implementations (one class per file)
- `src/algo_atlas/config/` — Settings and configuration
- `src/algo_atlas/core/` — Core logic (scraper, verifier, generator)
- `src/algo_atlas/cli/` — Command-line interface and workflows
- `src/algo_atlas/utils/` — Helper utilities (logger, file ops, git ops)

**Barrel Files:**
- `src/algo_atlas/cli/__init__.py` re-exports: `parse_args`, `parse_batch_file`, `BatchItem`, `BatchResult`, `main`
- `src/algo_atlas/languages/__init__.py` re-exports: `get_language()`, `get_language_by_extension()`, `list_languages()`, `default_language()` plus all language classes
- Allows cleaner imports: `from algo_atlas.cli import parse_args` instead of `from algo_atlas.cli.args import parse_args`

---

*Convention analysis: 2026-03-14*
