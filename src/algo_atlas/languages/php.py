"""PHP language support for AlgoAtlas."""

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

# Matches a public/protected/private function inside class Solution.
# group(1) = method name, group(2) = raw params string.
_METHOD_PATTERN = re.compile(
    r"(?:public|protected|private)?\s*function\s+(\w+)\s*\(([^)]*)\)",
    re.MULTILINE,
)

# Method names that are not LeetCode solution methods.
_PHP_KEYWORDS = frozenset({"__construct", "__destruct", "__toString"})


class PHPLanguage(LanguageSupport):
    """PHP language support using php."""

    def info(self) -> LanguageInfo:
        return LanguageInfo(
            name="PHP",
            slug="php",
            file_extension=".php",
            solution_filename="solution.php",
            code_fence="php",
            leetcode_slugs=["php"],
        )

    def can_run_tests(self) -> bool:
        return shutil.which("php") is not None

    def check_syntax(self, code: str) -> SyntaxResult:
        if not shutil.which("php"):
            return SyntaxResult(valid=False, error_message="php not found")
        if not code.strip():
            return SyntaxResult(valid=True)
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "solution.php"
            src.write_text(code, encoding="utf-8")
            proc = subprocess.run(
                ["php", "-l", str(src)],
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
            if name not in _PHP_KEYWORDS:
                return name
        return None

    def count_method_params(self, code: str) -> int:
        m = _METHOD_PATTERN.search(code)
        if not m:
            return 0
        return len(_split_php_params(m.group(2)))

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


def _split_php_params(params_str: str) -> list[str]:
    """Split param string by comma, ignoring commas inside brackets or parens.

    Strips type hints, default values, and sigils (``$``, ``&``, ``...``)
    so only the bare parameter name is returned.
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
            name = _extract_php_param_name(part)
            if name:
                parts.append(name)
            current = []
        else:
            current.append(ch)
    part = "".join(current).strip()
    name = _extract_php_param_name(part)
    if name:
        parts.append(name)
    return parts


def _extract_php_param_name(param: str) -> str:
    """Extract bare name from a PHP param like ``array $nums``, ``int &$n = 0``."""
    # Strip default value
    param = param.split("=")[0].strip()
    # The variable is the last token containing $
    tokens = param.split()
    for token in reversed(tokens):
        if "$" in token:
            # Strip leading & ... $ and return identifier
            return re.sub(r"^[&.]*\$", "", token)
    return ""
