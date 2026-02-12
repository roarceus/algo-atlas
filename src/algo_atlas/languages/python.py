"""Python language support for AlgoAtlas."""

import ast
from typing import Any, Optional

from algo_atlas.config.settings import get_settings
from algo_atlas.core.timeout import TimeoutError, _run_with_timeout
from algo_atlas.languages.base import (
    LanguageInfo,
    LanguageSupport,
    SyntaxResult,
    TestResult,
)


class PythonLanguage(LanguageSupport):
    """Python language support with AST-based syntax checking and exec-based test execution."""

    def info(self) -> LanguageInfo:
        return LanguageInfo(
            name="Python",
            slug="python3",
            file_extension=".py",
            solution_filename="solution.py",
            code_fence="python",
            leetcode_slugs=["python3", "python"],
        )

    def check_syntax(self, code: str) -> SyntaxResult:
        """Check Python syntax using ast.parse()."""
        try:
            ast.parse(code)
            return SyntaxResult(valid=True)
        except SyntaxError as e:
            return SyntaxResult(
                valid=False,
                error_message=str(e.msg) if e.msg else str(e),
                error_line=e.lineno,
            )

    def extract_method_name(self, code: str) -> Optional[str]:
        """Extract the main method name from Solution class."""
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

    def count_method_params(self, code: str) -> int:
        """Count parameters in the solution method (excluding self)."""
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return 0

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == "Solution":
                for item in node.body:
                    if isinstance(item, ast.FunctionDef) and not item.name.startswith("_"):
                        args = item.args
                        count = len(args.args)
                        if count > 0 and args.args[0].arg == "self":
                            count -= 1
                        return count

        return 0

    def run_test_case(
        self,
        code: str,
        input_args: list[Any],
        expected_output: Any,
        timeout: Optional[int] = None,
    ) -> TestResult:
        """Run a single test case by exec-ing the Python solution."""
        if timeout is None:
            settings = get_settings()
            timeout = settings.verifier.execution_timeout

        # Extract Solution class
        solution_class = self._extract_solution_class(code)
        if solution_class is None:
            return TestResult(
                passed=False,
                input_args=input_args,
                expected=expected_output,
                actual=None,
                error="Could not extract Solution class",
            )

        # Get method name
        method_name = self.extract_method_name(code)
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
            from algo_atlas.core.verifier import _compare_results

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

    @staticmethod
    def _build_exec_namespace() -> dict:
        """Build namespace with common LeetCode imports for exec()."""
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

    @classmethod
    def _extract_solution_class(cls, code: str) -> Optional[type]:
        """Extract Solution class from code string."""
        namespace = cls._build_exec_namespace()

        try:
            exec(code, namespace)
        except Exception:
            return None

        return namespace.get("Solution")
