# Codebase Concerns

**Analysis Date:** 2025-03-14

## Tech Debt

**Broad Exception Handling:**
- Issue: Multiple functions catch generic `Exception` instead of specific error types
- Files: `src/algo_atlas/cli/batch.py` (lines 197, 335), `src/algo_atlas/core/timeout.py` (line 45), multiple language files
- Impact: Masks true errors and makes debugging difficult; hides bugs that should surface. Catches things like `KeyboardInterrupt` which should propagate.
- Fix approach: Replace with specific exception types (e.g., `FileNotFoundError`, `json.JSONDecodeError`, `subprocess.TimeoutExpired`). Only use `Exception` as fallback in outermost workflow functions.

**Temporary Directory Cleanup:**
- Issue: Language implementations create temp files/directories but rely on `finally` blocks for cleanup. Windows paths may fail cleanup if file is locked.
- Files: `src/algo_atlas/languages/javascript.py` (line 62), `src/algo_atlas/languages/java.py` (lines 104-108), `src/algo_atlas/languages/rust.py` (line 116+), `src/algo_atlas/languages/kotlin.py` (line 89)
- Impact: Temp files accumulate in system temp directories; potential disk space issues on long-running processes
- Fix approach: Use `contextlib.contextmanager` wrapper or ensure all temp file paths are tracked and cleaned up immediately after use. Consider `tempfile.TemporaryDirectory()` with explicit cleanup.

**Loose Input Validation in test_parser:**
- Issue: `_parse_single_value()` returns fallback string when parsing fails silently, making it hard to distinguish invalid input from intentional strings
- Files: `src/algo_atlas/core/test_parser.py` (lines 84-108)
- Impact: Invalid test inputs silently become strings, leading to confusing test failures downstream
- Fix approach: Add logging when parsing fails, or raise an exception with context about what failed to parse

**Silent Failures in Scraper:**
- Issue: `scrape_problem()` returns `None` for many failure modes (invalid URL, network error, GraphQL error) without detailed logging
- Files: `src/algo_atlas/core/scraper.py` (lines 309-326)
- Impact: CLI users see "Failed to scrape problem" with no indication whether it's a URL issue, network timeout, or GraphQL error
- Fix approach: Raise specific exceptions with context; let caller decide how to handle. Log detailed failure reason at DEBUG level.

## Known Bugs

**Temporary File Race Condition in Java/Kotlin:**
- Symptoms: `shutil.rmtree()` on Windows may fail if antivirus or file locking holds reference
- Files: `src/algo_atlas/languages/java.py` (line 106), `src/algo_atlas/languages/kotlin.py` (line 89)
- Trigger: On Windows with antivirus active, running tests on Java/Kotlin code may leave temp files behind
- Workaround: Add `ignore_errors=True` or use `time.sleep(0.1)` before cleanup to release file locks

**Regex Pattern for Error Parsing in Multiple Languages:**
- Symptoms: Error line extraction from compiler/runtime output may fail for non-standard error formats
- Files: `src/algo_atlas/languages/javascript.py` (lines 72-82), `src/algo_atlas/languages/java.py` (lines 74-86), `src/algo_atlas/languages/rust.py` (lines 146-165)
- Trigger: Languages with custom build systems (rustc, javac) or non-English error messages
- Workaround: Currently falls back to full error message if line extraction fails; works but provides poor user experience

**Test Input Parsing Edge Case:**
- Symptoms: Bracket depth tracking in `_split_leetcode_input()` fails for nested string literals containing brackets
- Files: `src/algo_atlas/core/test_parser.py` (lines 52-81)
- Trigger: Input like `'key="value[with]brackets"'` will be misparsed
- Impact: Test case with string values containing brackets fail to parse
- Workaround: Currently falls back to string parsing if JSON/ast.literal_eval fails

**Settings Global State:**
- Symptoms: `_settings` global variable in `get_settings()` is not thread-safe
- Files: `src/algo_atlas/config/settings.py` (lines 139-154)
- Trigger: Concurrent calls to `get_settings()` from multiple threads during first access may cause race condition
- Impact: Unlikely in single-threaded CLI, but problematic if integrated into multi-threaded applications
- Workaround: Currently works because CLI is single-threaded, but should use `threading.Lock()` for safety

## Security Considerations

**Claude CLI Integration via stdin:**
- Risk: Passing problem descriptions and solution code through stdin to Claude CLI; if Claude CLI caches or logs, sensitive code patterns could be exposed
- Files: `src/algo_atlas/core/generator.py` (lines 64-70)
- Current mitigation: Passes via stdin to avoid command-line length limits (Windows issue), but no sanitization of sensitive patterns
- Recommendations: Document that Claude CLI should not log input; consider adding opt-in "redact" flag to mask certain patterns before sending to Claude

**LeetCode GraphQL Endpoint Rotation:**
- Risk: User-agent rotation in scraper is predictable; LeetCode may detect and block
- Files: `src/algo_atlas/core/scraper.py` (lines 19-25)
- Current mitigation: Rotates between 5 predefined user agents; includes random selection
- Recommendations: Add rate limiting (--delay flag) and exponential backoff already present but could be more sophisticated (implement jitter)

**File Write Permissions:**
- Risk: Saving solution files to vault without checking existing file ownership/permissions could overwrite unintended files
- Files: `src/algo_atlas/utils/vault_files.py` (lines 111+)
- Current mitigation: Uses `mkdir(exist_ok=True)` and overwrites files silently
- Recommendations: Add `--force` flag for overwrites; warn user if file already exists; use atomic writes (write to temp, then rename)

**GitHub CLI Token Exposure:**
- Risk: GitHub CLI auth token stored in system keychain/config; if process is debugged or logs are captured, token could leak
- Files: `src/algo_atlas/utils/github_ops.py` (lines 37-48)
- Current mitigation: Uses GitHub CLI subprocess (delegates auth to gh CLI)
- Recommendations: Verify GitHub CLI is using OS-level secret storage; document that GitHub CLI must be authenticated separately

## Performance Bottlenecks

**GraphQL Request Network Overhead:**
- Problem: Each problem scrape makes a single network request; retry logic sleeps 2, 4, 8 seconds between attempts
- Files: `src/algo_atlas/core/scraper.py` (lines 138-168)
- Cause: Synchronous requests with exponential backoff; no request pooling or caching
- Improvement path:
  - Add local problem cache (cache scraped JSON by problem number)
  - Implement persistent cache with TTL (e.g., cache for 7 days)
  - Add `--skip-scrape` flag to load from local cache

**Claude CLI Timeout:**
- Problem: 300-second timeout for Claude documentation generation is long; blocks CLI for 5 minutes
- Files: `src/algo_atlas/core/generator.py` (line 36)
- Cause: Claude CLI can be slow for complex problems; no streaming or background mode
- Improvement path:
  - Reduce timeout to 120s with warning about truncation
  - Add async/background mode (save to .draft, prompt user to complete later)
  - Stream output instead of waiting for full response

**Language Test Harness Compilation:**
- Problem: Compiling test harness for each test case (Java, Rust, Kotlin) is slow; compiles once per test
- Files: `src/algo_atlas/languages/java.py` (lines 240+), `src/algo_atlas/languages/rust.py` (lines 240+), `src/algo_atlas/languages/kotlin.py` (lines 180+)
- Cause: Separate compile+run architecture; no caching of compiled harness
- Improvement path:
  - Compile once, run multiple times (cache compiled .jar, .o, or binary)
  - Use in-memory compilation if available
  - Batch test cases into single run

**Batch Processing Sequential:**
- Problem: `batch` command processes problems one-at-a-time; no parallelism
- Files: `src/algo_atlas/cli/batch.py` (lines 310-336)
- Cause: Synchronous processing; network I/O blocks entire batch
- Improvement path:
  - Add `--parallel N` flag for N concurrent workers
  - Use `asyncio` or `ThreadPoolExecutor` for I/O-bound operations
  - Separate network (scrape) from CPU-bound (verify) stages

## Fragile Areas

**LeetCode HTML Parsing:**
- Files: `src/algo_atlas/core/scraper.py` (lines 171-229)
- Why fragile: Regex-based extraction of examples, constraints, and problem description depends on LeetCode's exact HTML structure. Site redesigns break parsing.
- Safe modification: Add comprehensive test fixtures (mock_graphql_response in conftest.py already does this); extract to separate parser module with versioning
- Test coverage: `test_scraper.py` mocks GraphQL response; good coverage but only tests current format

**Method Name Extraction Across Languages:**
- Files: `src/algo_atlas/languages/python.py`, `src/algo_atlas/languages/javascript.py` (lines 109-130), `src/algo_atlas/languages/java.py` (lines 113+), multiple others
- Why fragile: Regex patterns assume specific coding styles (e.g., function name before params, class/function keywords). Custom code patterns fail silently.
- Safe modification: Add strict validation after extraction; verify extracted name is valid Python/JS/Java identifier; test against real LeetCode solutions
- Test coverage: Each language has tests, but limited edge cases for unusual formatting

**Test Case Grouping Logic:**
- Files: `src/algo_atlas/core/verifier.py` (lines 81-102)
- Why fragile: Groups test cases by parameter count; assumes all test cases have same number of parameters. Fails if problem has variable params.
- Safe modification: Add `--args-per-case N` flag to override; validate grouped inputs match expected count before running
- Test coverage: No test for variable parameter counts

**Vault README Generation:**
- Files: `src/algo_atlas/utils/vault_readme.py`
- Why fragile: Parses existing README to insert stats; regex-based insertion assumes specific markdown format. Manual edits break parsing.
- Safe modification: Store stats in YAML frontmatter instead of parsing markdown; use front-matter library
- Test coverage: Not checked

## Scaling Limits

**Vault Size Scaling:**
- Current capacity: ~500 problems (estimated from typical use)
- Limit: README generation and topic indexing become slow above 1000 problems; Git operations slow with large repo history
- Scaling path:
  - Split vault into multiple repos by difficulty/topic
  - Use database instead of Git for metadata
  - Generate static site from vault instead of README

**Memory Usage in Batch Mode:**
- Current capacity: ~100 problems per batch before memory pressure
- Limit: All results held in memory; no streaming output
- Scaling path: Stream results to file immediately; use generators instead of lists; add `--output-format jsonl` for streaming

**Test Execution Timeout:**
- Current capacity: 5-second timeout per test case (configurable)
- Limit: Complex algorithms (dynamic programming, graph search) may exceed timeout
- Scaling path: Make timeout configurable per-language; detect O(n²) algorithms and warn; implement timeout per-test-suite instead of per-case

## Dependencies at Risk

**Claude CLI Version Pinning:**
- Risk: `claude --version` output format may change; version detection breaks
- Files: `src/algo_atlas/core/generator.py` (lines 26-32)
- Impact: If Claude CLI updates, syntax checking may fail
- Migration plan: Parse semantic version robustly; add `--claude-version` flag to override

**GitHub CLI Authentication:**
- Risk: GitHub CLI auth token expires or is revoked; no retry logic for auth failures
- Files: `src/algo_atlas/utils/github_ops.py` (lines 37-48)
- Impact: PR creation silently fails if gh is unauthenticated
- Migration plan: Add explicit auth check before PR creation; prompt user to run `gh auth login`

**Language Runtime Dependencies:**
- Risk: Language runtimes (Node.js, Go, rustc, etc.) may not be installed or wrong version
- Files: All language files in `src/algo_atlas/languages/`
- Impact: Graceful degradation works, but error messages may not be clear
- Migration plan: Add `algo-atlas status` command (already done in v1.15.0) to check all runtimes; improve error messages with installation links

## Missing Critical Features

**Problem Caching:**
- Problem: Every scrape makes a network request; no local cache
- Blocks: Can't work offline; batch operations are slow; no way to re-run verification without re-scraping
- Workaround: None (would require implementing cache layer)

**Multi-Language Batch:**
- Problem: Batch file has single language for all problems; can't mix languages
- Blocks: Can't create multi-language vaults efficiently
- Workaround: Create separate batch files per language

**Partial Save on Test Failure:**
- Problem: If verification fails, nothing is saved (hard fail); no draft mode
- Blocks: Can't save incomplete solutions; forces user to re-scrape/re-verify after fixing code
- Workaround: Use `--dry-run` to test, then save manually

## Test Coverage Gaps

**Scraper Edge Cases:**
- What's not tested: Network timeouts, partial response bodies, malformed GraphQL responses, LeetCode rate limiting (HTTP 429)
- Files: `src/algo_atlas/core/scraper.py`
- Risk: Scraper may crash or behave unpredictably on network errors; no test fixtures for edge cases
- Priority: **High** - Network is most likely failure point

**Language Runtime Errors:**
- What's not tested: Runtime errors in generated code (e.g., IndexError, NullPointerException), timeout behavior, memory limits
- Files: All language test harness builders (`src/algo_atlas/languages/*.py`)
- Risk: Test execution may crash or hang on malformed code; timeouts not properly caught
- Priority: **High** - Core feature reliability

**Batch Processing Error Recovery:**
- What's not tested: Partial batch failures (e.g., problem 1 succeeds, 2 fails, 3 succeeds); vault corruption recovery
- Files: `src/algo_atlas/cli/batch.py`
- Risk: Batch processing leaves vault in inconsistent state if one problem fails
- Priority: **Medium** - Only affects users with batch files; manual workflows are fine

**GitHub Integration:**
- What's not tested: PR label creation failures, GitHub CLI not authenticated, branch already exists
- Files: `src/algo_atlas/utils/github_ops.py`
- Risk: PR creation silently fails; user unaware that problem wasn't saved
- Priority: **Medium** - Graceful failure works, but user feedback could be clearer

**Settings Configuration:**
- What's not tested: Invalid YAML in config file, missing required fields, type mismatches
- Files: `src/algo_atlas/config/settings.py`
- Risk: Invalid config causes confusing runtime errors instead of clear validation messages
- Priority: **Low** - Users typically follow docs; edge case

---

*Concerns audit: 2025-03-14*
