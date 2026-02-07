"""Solution verification and test case execution."""

import ast
from dataclasses import dataclass
from typing import Any, Optional

from algo_atlas.config.settings import get_settings
from algo_atlas.core.test_parser import (
    _parse_expected_output,
    _parse_test_input,
)
from algo_atlas.core.timeout import TimeoutError, _run_with_timeout


@dataclass
class SyntaxResult:
    """Result of syntax check."""

    valid: bool
    error_message: Optional[str] = None
    error_line: Optional[int] = None


@dataclass
class TestResult:
    """Result of a single test case execution."""

    passed: bool
    input_args: list[Any]
    expected: Any
    actual: Any
    error: Optional[str] = None


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


def check_syntax(code: str) -> SyntaxResult:
    """Check Python syntax using ast.parse().

    Args:
        code: Python source code to check.

    Returns:
        SyntaxResult with validation status.
    """
    try:
        ast.parse(code)
        return SyntaxResult(valid=True)
    except SyntaxError as e:
        return SyntaxResult(
            valid=False,
            error_message=str(e.msg) if e.msg else str(e),
            error_line=e.lineno,
        )


def _build_exec_namespace() -> dict:
    """Build namespace with common LeetCode imports for exec().

    Provides typing, collections, and other stdlib modules commonly
    used in LeetCode solutions so users don't need to include imports.

    Returns:
        Dict namespace pre-populated with common imports.
    """
    import collections
    import bisect
    import heapq
    import math
    import itertools
    import functools
    from typing import Dict, List, Optional, Set, Tuple

    return {
        "List": List,
        "Dict": Dict,
        "Optional": Optional,
        "Set": Set,
        "Tuple": Tuple,
        "collections": collections,
        "defaultdict": collections.defaultdict,
        "deque": collections.deque,
        "Counter": collections.Counter,
        "OrderedDict": collections.OrderedDict,
        "heapq": heapq,
        "heappush": heapq.heappush,
        "heappop": heapq.heappop,
        "bisect": bisect,
        "math": math,
        "inf": float("inf"),
        "itertools": itertools,
        "functools": functools,
    }


def _extract_solution_class(code: str) -> Optional[type]:
    """Extract Solution class from code string.

    Args:
        code: Python source code containing Solution class.

    Returns:
        Solution class if found, None otherwise.
    """
    # Create namespace with common LeetCode imports
    namespace = _build_exec_namespace()

    try:
        exec(code, namespace)
    except Exception:
        return None

    return namespace.get("Solution")


def _extract_method_name(code: str) -> Optional[str]:
    """Extract the main method name from Solution class.

    Args:
        code: Python source code.

    Returns:
        Method name if found, None otherwise.
    """
    # Parse the AST to find the method
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return None

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "Solution":
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and not item.name.startswith("_"):
                    return item.name

    return None


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


def run_test_case(
    solution_code: str,
    input_args: list[Any],
    expected_output: Any,
    timeout: Optional[int] = None,
) -> TestResult:
    """Run a single test case against solution.

    Args:
        solution_code: Python solution code with Solution class.
        input_args: Input arguments for the method.
        expected_output: Expected return value.
        timeout: Execution timeout in seconds.

    Returns:
        TestResult with execution details.
    """
    if timeout is None:
        settings = get_settings()
        timeout = settings.verifier.execution_timeout

    # Extract Solution class
    solution_class = _extract_solution_class(solution_code)
    if solution_class is None:
        return TestResult(
            passed=False,
            input_args=input_args,
            expected=expected_output,
            actual=None,
            error="Could not extract Solution class",
        )

    # Get method name
    method_name = _extract_method_name(solution_code)
    if method_name is None:
        return TestResult(
            passed=False,
            input_args=input_args,
            expected=expected_output,
            actual=None,
            error="Could not find solution method",
        )

    # Create instance and get method
    try:
        instance = solution_class()
        method = getattr(instance, method_name)
    except Exception as e:
        return TestResult(
            passed=False,
            input_args=input_args,
            expected=expected_output,
            actual=None,
            error=f"Could not instantiate Solution: {e}",
        )

    # Run with timeout
    try:
        actual = _run_with_timeout(method, input_args, timeout)
        passed = _compare_results(expected_output, actual)

        return TestResult(
            passed=passed,
            input_args=input_args,
            expected=expected_output,
            actual=actual,
        )
    except TimeoutError:
        return TestResult(
            passed=False,
            input_args=input_args,
            expected=expected_output,
            actual=None,
            error=f"Execution timed out after {timeout}s",
        )
    except Exception as e:
        return TestResult(
            passed=False,
            input_args=input_args,
            expected=expected_output,
            actual=None,
            error=str(e),
        )


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


def _count_method_params(code: str) -> int:
    """Count the number of parameters in the solution method (excluding self).

    Args:
        code: Python source code.

    Returns:
        Number of parameters.
    """
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return 0

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "Solution":
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and not item.name.startswith("_"):
                    # Count args excluding 'self'
                    args = item.args
                    count = len(args.args)
                    if count > 0 and args.args[0].arg == "self":
                        count -= 1
                    return count

    return 0


def run_test_cases(
    solution_code: str,
    test_cases: list[str],
    examples: list[dict],
    expected_outputs: Optional[list[Any]] = None,
) -> VerificationResult:
    """Run all test cases against solution.

    Args:
        solution_code: Python solution code.
        test_cases: Raw test case input strings from LeetCode.
        examples: Parsed examples with input/output.
        expected_outputs: Optional list of expected outputs for test_cases
                         (provided by Claude or other source).

    Returns:
        VerificationResult with all test outcomes.
    """
    # First check syntax
    syntax_result = check_syntax(solution_code)
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

        test_result = run_test_case(solution_code, input_args, expected)
        result.test_results.append(test_result)
        result.tests_run += 1
        if test_result.passed:
            result.tests_passed += 1

    # Run additional test cases if expected outputs are provided
    if expected_outputs and test_cases:
        # Determine how many args per test case
        args_per_case = _count_method_params(solution_code)
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

                test_result = run_test_case(solution_code, input_args, expected)
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
) -> VerificationResult:
    """Full solution verification with syntax check and test execution.

    Args:
        solution_code: Python solution code.
        test_cases: Raw test case strings.
        examples: Parsed examples with expected outputs.
        expected_outputs: Optional list of expected outputs for additional test_cases.

    Returns:
        VerificationResult with complete verification status.
    """
    return run_test_cases(solution_code, test_cases, examples, expected_outputs)
