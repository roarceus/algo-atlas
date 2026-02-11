"""Base interface for language support in AlgoAtlas."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class LanguageInfo:
    """Metadata about a supported programming language."""

    name: str  # "Python", "JavaScript"
    slug: str  # "python3", "javascript"
    file_extension: str  # ".py", ".js"
    solution_filename: str  # "solution.py", "solution.js"
    code_fence: str  # "python", "javascript"
    leetcode_slugs: list[str] = field(default_factory=list)  # ["python3", "python"]


@dataclass
class SyntaxResult:
    """Result of a syntax check."""

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


class LanguageSupport(ABC):
    """Abstract base class for language-specific support."""

    @abstractmethod
    def info(self) -> LanguageInfo:
        """Return metadata about this language."""
        ...

    @abstractmethod
    def check_syntax(self, code: str) -> SyntaxResult:
        """Check syntax validity of the given code.

        Args:
            code: Source code to check.

        Returns:
            SyntaxResult with validation status.
        """
        ...

    @abstractmethod
    def extract_method_name(self, code: str) -> Optional[str]:
        """Extract the main method/function name from solution code.

        Args:
            code: Source code.

        Returns:
            Method name if found, None otherwise.
        """
        ...

    @abstractmethod
    def count_method_params(self, code: str) -> int:
        """Count the number of parameters in the solution method.

        Args:
            code: Source code.

        Returns:
            Number of parameters (excluding self/this).
        """
        ...

    @abstractmethod
    def run_test_case(
        self,
        code: str,
        input_args: list[Any],
        expected_output: Any,
        timeout: Optional[int] = None,
    ) -> TestResult:
        """Run a single test case against the solution.

        Args:
            code: Solution source code.
            input_args: Input arguments for the method.
            expected_output: Expected return value.
            timeout: Execution timeout in seconds.

        Returns:
            TestResult with execution details.
        """
        ...

    def can_run_tests(self) -> bool:
        """Check if this language can run test cases.

        Returns:
            True if the language runtime is available.
        """
        return True
