# Testing

## Framework

- **pytest** with `pytest-cov` for coverage
- **unittest.mock** (`patch`, `MagicMock`) for mocking
- Config: `pyproject.toml` `[tool.pytest.ini_options]`

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_functions = ["test_*"]
addopts = "-v --cov=algo_atlas --cov-report=term-missing"

[tool.coverage.run]
source = ["src/algo_atlas"]
branch = true
```

Run tests:
```bash
pytest                          # all tests with coverage
pytest tests/test_javascript.py # single file
pytest -k "test_valid_syntax"   # by name filter
```

---

## Test File Organization

19 test files, ~481 tests total:

| File | Tests | Coverage |
|------|-------|----------|
| `tests/test_python.py` | 24 | PythonLanguage |
| `tests/test_javascript.py` | 24 | JavaScriptLanguage |
| `tests/test_typescript.py` | 24 | TypeScriptLanguage |
| `tests/test_java.py` | 24 | JavaLanguage |
| `tests/test_kotlin.py` | 24 | KotlinLanguage |
| `tests/test_cpp.py` | 24 | CppLanguage |
| `tests/test_c.py` | 24 | CLanguage |
| `tests/test_go.py` | 24 | GoLanguage |
| `tests/test_rust.py` | 24 | RustLanguage |
| `tests/test_csharp.py` | 24 | CSharpLanguage |
| `tests/test_swift.py` | 24 | SwiftLanguage |
| `tests/test_ruby.py` | 24 | RubyLanguage |
| `tests/test_php.py` | 24 | PHPLanguage |
| `tests/test_languages.py` | ~13 | Registry cross-language |
| `tests/test_scraper.py` | ~20 | LeetCode scraper |
| `tests/test_verifier.py` | ~15 | Solution verifier |
| `tests/test_file_manager.py` | ~10 | Vault file writes |
| `tests/test_cli.py` | ~10 | CLI workflows |
| `tests/test_logger.py` | ~8 | Terminal logger |

---

## Standard Language Test Structure

Each language test file follows a rigid 6-class, 24-test pattern:

```python
# tests/test_{lang}.py

class Test{Lang}Registry:          # 3 tests
    def test_get_language_{slug}    # get_language("slug") returns right type
    def test_get_language_by_extension_{ext}  # lookup by file extension
    def test_list_languages_includes_{slug}   # present in list_languages()

class Test{Lang}Info:               # 3 tests
    def test_info                   # name, slug, file_extension, solution_filename, etc.
    def test_is_language_support    # isinstance check against LanguageSupport
    def test_can_run_tests_reflects_{runtime}  # mirrors shutil.which() result

class Test{Lang}CheckSyntax:        # 4 tests
    def test_valid_syntax           # valid solution → SyntaxResult(valid=True)
    def test_invalid_syntax         # bad syntax → SyntaxResult(valid=False, error_message=...)
    def test_syntax_check_without_{runtime}  # patched shutil.which=None → valid=False
    def test_syntax_result_has_no_error_on_valid  # error_message is None on success

class Test{Lang}ExtractMethodName:  # 5 tests
    def test_extract_simple_method  # twoSum → "twoSum"
    def test_extract_another_method # maxProfit → "maxProfit"
    def test_extract_returns_none_on_empty  # "" → None
    def test_extract_returns_none_on_no_method  # garbage → None
    def test_extract_from_problem_snippet  # real LeetCode snippet

class Test{Lang}CountMethodParams:  # 4 tests
    def test_count_two_params       # (nums, target) → 2
    def test_count_one_param        # (s) → 1
    def test_count_zero_params      # () → 0
    def test_count_complex_params   # type-annotated or default-valued params

class Test{Lang}RunTestCase:        # 5 tests
    def test_correct_solution       # correct code → TestResult(passed=True)
    def test_wrong_answer           # wrong output → TestResult(passed=False)
    def test_syntax_error           # syntax error → TestResult(passed=False)
    def test_runtime_error          # exception in solution → TestResult(passed=False)
    def test_without_{runtime}      # patched shutil.which=None → TestResult(passed=False, error=...)
```

---

## Shared Fixtures (`tests/conftest.py`)

```python
@pytest.fixture
def sample_problem() -> ProblemData:
    """Two Sum problem with 3 examples and test_cases."""

@pytest.fixture
def valid_solution() -> str:
    """Valid Python Two Sum: hash map approach."""

@pytest.fixture
def mock_graphql_response() -> dict:
    """Full GraphQL response with 13 language code snippets."""
    # Slugs: python3, javascript, typescript, java, cpp, c, golang,
    #        rust, csharp, kotlin, swift, ruby, php
    # test_scraper.py asserts len(snippets) == 13

# Per-language fixtures (one per language file):
@pytest.fixture
def valid_{lang}_solution() -> str: ...
@pytest.fixture
def invalid_{lang}_syntax() -> str: ...
@pytest.fixture
def wrong_{lang}_answer() -> str: ...
@pytest.fixture
def runtime_error_{lang}_solution() -> str: ...  # (some languages)
```

**Critical:** When adding a new language, increment the snippet count assertion in `tests/test_scraper.py` and add the new slug to `mock_graphql_response`.

---

## Mocking Patterns

### Mocking subprocess/runtime availability

```python
# Pattern: patch shutil.which to simulate missing runtime
with patch("shutil.which", return_value=None):
    result = lang.check_syntax(code)
    assert result.valid is False

# Pattern used in can_run_tests tests
with patch("shutil.which", return_value=None):
    assert lang.can_run_tests() is False
```

### Mocking HTTP requests (scraper tests)

```python
# tests/test_scraper.py uses requests_mock or unittest.mock.patch
with patch("requests.Session.post") as mock_post:
    mock_post.return_value.json.return_value = mock_graphql_response
    mock_post.return_value.status_code = 200
    result = scraper.scrape(url)
```

### Mocking file system (file_manager tests)

```python
with patch("pathlib.Path.write_text") as mock_write:
    file_manager.save(...)
    mock_write.assert_called_once()
```

---

## Test Types

| Type | Coverage | Notes |
|------|----------|-------|
| Unit | Language classes, config, utils | Majority of tests |
| Integration | Scraper (mocked HTTP), verifier (real subprocess) | Real subprocess calls for syntax/run |
| No E2E | No tests hitting real LeetCode API or Claude CLI | Mocked at HTTP/subprocess boundary |

**Integration note:** Language `check_syntax` and `run_test_case` tests invoke real compiler/interpreter subprocesses. Tests that require a runtime (e.g., Node, javac, kotlinc) are guarded by `can_run_tests()` checks or use `@pytest.mark.skipif`.

---

## CI Configuration (`.github/workflows/ci.yml`)

- Runs on: push/PR to `main`
- Python versions: 3.10, 3.11, 3.12
- Steps: `pip install -e ".[dev]"` → `flake8` → `pytest`
- Notable runtime setups per language CI:
  - Kotlin: `fwilhe2/setup-kotlin@v1` (NOT v2)
  - C#: targets `net8.0`
  - Go: separate `go build` + run (avoids `go run` timeout)

---

## Coverage Exclusions

```toml
[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
]
```

---

## Adding Tests for a New Language

1. Add fixtures to `tests/conftest.py`:
   - `valid_{slug}_solution`, `invalid_{slug}_syntax`, `wrong_{slug}_answer`
   - Add code snippet to `mock_graphql_response` dict
2. Create `tests/test_{slug}.py` with 6 classes × 4–5 tests = 24 tests
3. Update `tests/test_languages.py`: add slug to registry assertion list
4. Update `tests/test_scraper.py`: increment snippet count (`len == N+1`)
