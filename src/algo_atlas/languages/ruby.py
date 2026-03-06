"""Ruby language support for AlgoAtlas."""

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

# Matches a `def` inside class Solution.
# group(1) = method name, group(2) = raw params string.
_METHOD_PATTERN = re.compile(
    r"^\s*def\s+(\w+)\s*\(([^)]*)\)",
    re.MULTILINE,
)

# Method names that are not LeetCode solution methods.
_RUBY_KEYWORDS = frozenset({"initialize"})


class RubyLanguage(LanguageSupport):
    """Ruby language support using ruby."""

    def info(self) -> LanguageInfo:
        return LanguageInfo(
            name="Ruby",
            slug="ruby",
            file_extension=".rb",
            solution_filename="solution.rb",
            code_fence="ruby",
            leetcode_slugs=["ruby"],
        )

    def can_run_tests(self) -> bool:
        return shutil.which("ruby") is not None

    def check_syntax(self, code: str) -> SyntaxResult:
        if not shutil.which("ruby"):
            return SyntaxResult(valid=False, error_message="ruby not found")
        if not code.strip():
            return SyntaxResult(valid=True)
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "solution.rb"
            src.write_text(code, encoding="utf-8")
            proc = subprocess.run(
                ["ruby", "-c", str(src)],
                capture_output=True,
                text=True,
            )
            if proc.returncode == 0:
                return SyntaxResult(valid=True)
            msg = (proc.stdout + proc.stderr).strip()
            return SyntaxResult(valid=False, error_message=msg)

    def extract_method_name(self, code: str) -> Optional[str]:
        for m in _METHOD_PATTERN.finditer(code):
            name = m.group(1)
            if name not in _RUBY_KEYWORDS:
                return name
        return None

    def count_method_params(self, code: str) -> int:
        m = _METHOD_PATTERN.search(code)
        if not m:
            return 0
        return len(_split_ruby_params(m.group(2)))

    def run_test_case(
        self, code: str, input_args: list, expected_output: Any
    ) -> TestResult:
        return TestResult(
            passed=False,
            input_args=input_args,
            expected=expected_output,
            actual=None,
            error="not implemented",
        )


def _split_ruby_params(params_str: str) -> list[str]:
    """Split param string by comma, ignoring commas inside brackets or parens.

    Strips default values (e.g. ``name = default``) and sigils (``*``, ``**``,
    ``&``) so only the bare parameter name is returned.
    """
    parts: list[str] = []
    depth = 0
    current: list[str] = []
    for ch in params_str:
        if ch in ("[", "(", "{"):
            depth += 1
            current.append(ch)
        elif ch in ("]", ")", "}"):
            depth -= 1
            current.append(ch)
        elif ch == "," and depth == 0:
            part = "".join(current).strip()
            name = part.split("=")[0].strip().lstrip("*&").strip()
            if name:
                parts.append(name)
            current = []
        else:
            current.append(ch)
    part = "".join(current).strip()
    name = part.split("=")[0].strip().lstrip("*&").strip()
    if name:
        parts.append(name)
    return parts
