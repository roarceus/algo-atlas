"""Swift language support for AlgoAtlas."""

import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Optional

from algo_atlas.languages.base import (
    LanguageInfo,
    LanguageSupport,
    SyntaxResult,
    TestResult,
)

# Matches a `func` inside class Solution.
# group(1) = method name, group(2) = raw params string.
_METHOD_PATTERN = re.compile(
    r"\bfunc\s+"
    r"(\w+)\s*"  # group(1) = method name
    r"\(([^)]*)\)",  # group(2) = raw params string
    re.MULTILINE,
)

# Same but also captures return type as group(3).
_METHOD_FULL_PATTERN = re.compile(
    r"\bfunc\s+"
    r"(\w+)\s*"  # group(1) = method name
    r"\(([^)]*)\)"  # group(2) = params
    r"(?:\s*->\s*([^\n{]+?))?(?:\s*\{)",  # group(3) = return type (optional)
    re.MULTILINE,
)

# Method names that are not LeetCode solution methods.
_SWIFT_KEYWORDS = frozenset({"init", "deinit", "subscript"})


class SwiftLanguage(LanguageSupport):
    """Swift language support using swiftc."""

    def info(self) -> LanguageInfo:
        return LanguageInfo(
            name="Swift",
            slug="swift",
            file_extension=".swift",
            solution_filename="solution.swift",
            code_fence="swift",
            leetcode_slugs=["swift"],
        )

    def can_run_tests(self) -> bool:
        return shutil.which("swiftc") is not None

    def check_syntax(self, code: str) -> SyntaxResult:
        if not shutil.which("swiftc"):
            return SyntaxResult(valid=False, error_message="swiftc not found")
        if not code.strip():
            return SyntaxResult(valid=True)
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "solution.swift"
            src.write_text(code, encoding="utf-8")
            proc = subprocess.run(
                ["swiftc", "-typecheck", str(src)],
                capture_output=True,
                text=True,
            )
            if proc.returncode == 0:
                return SyntaxResult(valid=True)
            errors = [
                line
                for line in (proc.stdout + proc.stderr).splitlines()
                if ": error:" in line
            ]
            msg = "\n".join(errors) if errors else (proc.stdout + proc.stderr).strip()
            return SyntaxResult(valid=False, error_message=msg)

    def extract_method_name(self, code: str) -> Optional[str]:
        return None

    def count_method_params(self, code: str) -> int:
        return 0

    def run_test_case(
        self, code: str, input_args: list, expected_output: Any
    ) -> TestResult:
        return TestResult(
            passed=False,
            input_args=input_args,
            expected=expected_output,
            actual=None,
            error="Not implemented",
        )
