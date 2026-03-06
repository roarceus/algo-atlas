"""Ruby language support for AlgoAtlas."""

import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Optional

from algo_atlas.config.settings import get_settings
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
        if not shutil.which("ruby"):
            return TestResult(
                passed=False,
                input_args=input_args,
                expected=expected_output,
                actual=None,
                error="ruby not found",
            )

        method_name = self.extract_method_name(code)
        if not method_name:
            return TestResult(
                passed=False,
                input_args=input_args,
                expected=expected_output,
                actual=None,
                error="Could not extract method name",
            )

        m = _METHOD_PATTERN.search(code)
        params_str = m.group(2) if m else ""
        params = _split_ruby_params(params_str)

        settings = get_settings()
        execution_timeout = settings.verifier.execution_timeout

        with tempfile.TemporaryDirectory() as tmp:
            sol_path = Path(tmp) / "solution.rb"
            main_path = Path(tmp) / "main.rb"

            sol_path.write_text(code, encoding="utf-8")
            main_path.write_text(
                self._build_test_harness(method_name, params, input_args),
                encoding="utf-8",
            )

            try:
                run_proc = subprocess.run(
                    ["ruby", str(main_path)],
                    capture_output=True,
                    text=True,
                    timeout=execution_timeout,
                )
            except subprocess.TimeoutExpired:
                return TestResult(
                    passed=False,
                    input_args=input_args,
                    expected=expected_output,
                    actual=None,
                    error="Execution timed out",
                )
            except FileNotFoundError:
                return TestResult(
                    passed=False,
                    input_args=input_args,
                    expected=expected_output,
                    actual=None,
                    error="ruby not found",
                )

            if run_proc.returncode != 0:
                return TestResult(
                    passed=False,
                    input_args=input_args,
                    expected=expected_output,
                    actual=None,
                    error=f"Runtime error: {run_proc.stderr.strip()}",
                )

            output = run_proc.stdout.strip()
            try:
                data = json.loads(output)
                actual = data.get("result")
            except (json.JSONDecodeError, AttributeError):
                return TestResult(
                    passed=False,
                    input_args=input_args,
                    expected=expected_output,
                    actual=None,
                    error=f"Invalid output: {output!r}",
                )

            passed = actual == expected_output
            return TestResult(
                passed=passed,
                input_args=input_args,
                expected=expected_output,
                actual=actual,
            )

    def _build_test_harness(
        self,
        method_name: str,
        params: list[str],
        input_args: list,
    ) -> str:
        """Generate main.rb content for running a single test case."""
        lines = ["require 'json'", "require_relative 'solution'", ""]

        param_vars = []
        for i, value in enumerate(input_args):
            var = f"p{i}"
            literal = self._python_to_ruby_literal(value)
            lines.append(f"{var} = {literal}")
            param_vars.append(var)

        args_str = ", ".join(param_vars)
        lines.append("sol = Solution.new")
        lines.append(f"result = sol.{method_name}({args_str})")
        lines.append('puts({"result" => result}.to_json)')
        return "\n".join(lines)

    @staticmethod
    def _python_to_ruby_literal(value: Any) -> str:
        """Convert a Python value to a Ruby literal."""
        if value is None:
            return "nil"
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, int):
            return str(value)
        if isinstance(value, float):
            return str(value)
        if isinstance(value, str):
            escaped = value.replace("\\", "\\\\").replace('"', '\\"')
            return f'"{escaped}"'
        if isinstance(value, list):
            if not value:
                return "[]"
            items = ", ".join(
                RubyLanguage._python_to_ruby_literal(v) for v in value
            )
            return f"[{items}]"
        return str(value)


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
