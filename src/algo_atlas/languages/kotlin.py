"""Kotlin language support for AlgoAtlas."""

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

# Matches a `fun` inside class Solution.
# group(1) = method name, group(2) = raw params string.
_METHOD_PATTERN = re.compile(
    r"\bfun\s+"
    r"(\w+)\s*"  # group(1) = method name
    r"\(([^)]*)\)",  # group(2) = raw params string
    re.MULTILINE,
)

# Same but also captures return type as group(3).
_METHOD_FULL_PATTERN = re.compile(
    r"\bfun\s+"
    r"(\w+)\s*"  # group(1) = method name
    r"\(([^)]*)\)"  # group(2) = params
    r"(?:\s*:\s*([^\n{]+?))?(?:\s*\{)",  # group(3) = return type (optional)
    re.MULTILINE,
)

# Method names that are not LeetCode solution methods.
_KOTLIN_KEYWORDS = frozenset({"toString", "hashCode", "equals", "compareTo"})


class KotlinLanguage(LanguageSupport):
    """Kotlin language support using kotlinc."""

    def info(self) -> LanguageInfo:
        return LanguageInfo(
            name="Kotlin",
            slug="kotlin",
            file_extension=".kt",
            solution_filename="solution.kt",
            code_fence="kotlin",
            leetcode_slugs=["kotlin"],
        )

    def can_run_tests(self) -> bool:
        return shutil.which("kotlinc") is not None

    def check_syntax(self, code: str) -> SyntaxResult:
        if not shutil.which("kotlinc"):
            return SyntaxResult(valid=False, error_message="kotlinc not found")
        if not code.strip():
            return SyntaxResult(valid=True)
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "solution.kt"
            out = Path(tmp) / "solution.jar"
            src.write_text(code, encoding="utf-8")
            proc = subprocess.run(
                ["kotlinc", str(src), "-d", str(out)],
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
