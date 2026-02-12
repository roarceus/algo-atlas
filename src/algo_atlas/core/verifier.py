"""Solution verification and test case execution.

Public functions delegate to the default language (Python) via the
languages registry.  Shared types (VerificationResult) and
language-agnostic helpers (_compare_results, _group_test_case_inputs)
live here.
"""

from dataclasses import dataclass
from typing import Any, Optional

from algo_atlas.core.test_parser import (
    _parse_expected_output,
    _parse_test_input,
)
from algo_atlas.languages import default_language, get_language
from algo_atlas.languages.base import LanguageSupport

# Re-export from languages.base so existing imports keep working
from algo_atlas.languages.base import SyntaxResult, TestResult  # noqa: F401


@dataclass
class VerificationResult:
    """Result of full verification."""

    syntax_valid: bool
    syntax_error: Optional[str] = None
    tests_run: int = 0
    tests_passed: int = 0
    test_results: list[TestResult] = None

    def __post_init__(self):
        if self.test_results is None:
            self.test_results = []

    @property
    def all_passed(self) -> bool:
        """Check if all tests passed."""
        return self.syntax_valid and self.tests_run > 0 and self.tests_passed == self.tests_run


def _compare_results(expected: Any, actual: Any) -> bool:
    """Compare expected and actual results.

    Handles special cases like unordered lists for some problems.

    Args:
        expected: Expected result.
        actual: Actual result.

    Returns:
        True if results match, False otherwise.
    """
    # Direct equality
    if expected == actual:
        return True

    # Handle list comparison (some problems accept any order)
    if isinstance(expected, list) and isinstance(actual, list):
        if len(expected) != len(actual):
            return False

        # Try sorted comparison for simple lists
        try:
            if sorted(expected) == sorted(actual):
                return True
        except TypeError:
            pass

    return False


def _group_test_case_inputs(test_cases: list[str], args_per_case: int) -> list[list[str]]:
    """Group raw test case lines into individual test cases.

    Args:
        test_cases: List of input lines from LeetCode.
        args_per_case: Number of arguments per test case.

    Returns:
        List of grouped test case inputs.
    """
    if args_per_case <= 0 or not test_cases:
        return []

    grouped = []
    for i in range(0, len(test_cases), args_per_case):
        group = test_cases[i:i + args_per_case]
        if len(group) == args_per_case:
            grouped.append(group)

    return grouped


def _resolve_language(language: Optional[str] = None) -> LanguageSupport:
    """Resolve a language slug to a LanguageSupport instance.

    Args:
        language: Language slug (e.g. "python3", "javascript").
                  When None, returns the default language.

    Returns:
        LanguageSupport instance.

    Raises:
        ValueError: If the language slug is not recognized.
    """
    if language is None:
        return default_language()
    lang = get_language(language)
    if lang is None:
        raise ValueError(f"Unsupported language: {language}")
    return lang


# ---------------------------------------------------------------------------
# Public API — thin wrappers that delegate to the resolved language
# ---------------------------------------------------------------------------


def check_syntax(code: str, language: Optional[str] = None) -> SyntaxResult:
    """Check syntax of code.

    Args:
        code: Source code to check.
        language: Language slug. Defaults to Python when None.

    Returns:
        SyntaxResult with validation status.
    """
    return _resolve_language(language).check_syntax(code)


def run_test_case(
    solution_code: str,
    input_args: list[Any],
    expected_output: Any,
    timeout: Optional[int] = None,
    language: Optional[str] = None,
) -> TestResult:
    """Run a single test case against solution.

    Args:
        solution_code: Solution code with Solution class.
        input_args: Input arguments for the method.
        expected_output: Expected return value.
        timeout: Execution timeout in seconds.
        language: Language slug. Defaults to Python when None.

    Returns:
        TestResult with execution details.
    """
    return _resolve_language(language).run_test_case(
        solution_code, input_args, expected_output, timeout
    )


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
        expected_outputs: Optional list of expected outputs for test_cases
                         (provided by Claude or other source).
        language: Language slug. Defaults to Python when None.

    Returns:
        VerificationResult with all test outcomes.
    """
    lang = _resolve_language(language)

    # First check syntax
    syntax_result = lang.check_syntax(solution_code)
    if not syntax_result.valid:
        return VerificationResult(
            syntax_valid=False,
            syntax_error=f"Line {syntax_result.error_line}: {syntax_result.error_message}",
        )

    result = VerificationResult(syntax_valid=True)

    # Track which inputs we've already tested to avoid duplicates
    tested_inputs = set()

    # Run tests from examples (which have expected outputs)
    for example in examples:
        input_str = example.get("input", "")
        output_str = example.get("output", "")

        if not input_str or not output_str:
            continue

        input_args = _parse_test_input(input_str)
        expected = _parse_expected_output(output_str)

        # Create hashable key for deduplication
        try:
            input_key = str(input_args)
            tested_inputs.add(input_key)
        except Exception:
            pass

        test_result = lang.run_test_case(solution_code, input_args, expected)
        result.test_results.append(test_result)
        result.tests_run += 1
        if test_result.passed:
            result.tests_passed += 1

    # Run additional test cases if expected outputs are provided
    if expected_outputs and test_cases:
        # Determine how many args per test case
        args_per_case = lang.count_method_params(solution_code)
        if args_per_case > 0:
            grouped_inputs = _group_test_case_inputs(test_cases, args_per_case)

            for i, input_lines in enumerate(grouped_inputs):
                if i >= len(expected_outputs):
                    break

                input_args = _parse_test_input("\n".join(input_lines))
                expected = expected_outputs[i]

                # Skip if already tested
                try:
                    input_key = str(input_args)
                    if input_key in tested_inputs:
                        continue
                    tested_inputs.add(input_key)
                except Exception:
                    pass

                test_result = lang.run_test_case(solution_code, input_args, expected)
                result.test_results.append(test_result)
                result.tests_run += 1
                if test_result.passed:
                    result.tests_passed += 1

    return result


def verify_solution(
    solution_code: str,
    test_cases: list[str],
    examples: list[dict],
    expected_outputs: Optional[list[Any]] = None,
    language: Optional[str] = None,
) -> VerificationResult:
    """Full solution verification with syntax check and test execution.

    Args:
        solution_code: Solution code.
        test_cases: Raw test case strings.
        examples: Parsed examples with expected outputs.
        expected_outputs: Optional list of expected outputs for additional test_cases.
        language: Language slug. Defaults to Python when None.

    Returns:
        VerificationResult with complete verification status.
    """
    return run_test_cases(solution_code, test_cases, examples, expected_outputs, language)
