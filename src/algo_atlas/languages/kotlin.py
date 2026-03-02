"""Kotlin language support for AlgoAtlas."""

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

# JSON serialiser injected into the test harness.
# Uses ASCII codes 34 (") and 92 (\) to avoid escape sequences in this string.
_KOTLIN_TO_JSON = """\
fun toJson(value: Any?): String {
    if (value == null) return "null"
    if (value is Boolean || value is Int || value is Long || value is Double) return value.toString()
    if (value is String) {
        val sb = StringBuilder()
        sb.append(34.toChar())
        for (c in value) {
            when (c.code) {
                34 -> { sb.append(92.toChar()); sb.append(34.toChar()) }
                92 -> { sb.append(92.toChar()); sb.append(92.toChar()) }
                else -> sb.append(c)
            }
        }
        sb.append(34.toChar())
        return sb.toString()
    }
    if (value is IntArray) return value.joinToString(",", "[", "]") { toJson(it) }
    if (value is LongArray) return value.joinToString(",", "[", "]") { toJson(it) }
    if (value is Array<*>) return value.joinToString(",", "[", "]") { toJson(it) }
    if (value is List<*>) return value.joinToString(",", "[", "]") { toJson(it) }
    return value.toString()
}
"""


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
        for m in _METHOD_PATTERN.finditer(code):
            name = m.group(1)
            if name not in _KOTLIN_KEYWORDS:
                return name
        return None

    def count_method_params(self, code: str) -> int:
        m = _METHOD_PATTERN.search(code)
        if not m:
            return 0
        return len(_split_kotlin_params(m.group(2)))

    def run_test_case(
        self, code: str, input_args: list, expected_output: Any
    ) -> TestResult:
        if not shutil.which("kotlinc"):
            return TestResult(
                passed=False,
                input_args=input_args,
                expected=expected_output,
                actual=None,
                error="kotlinc not found",
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

        m = _METHOD_FULL_PATTERN.search(code)
        params_str = m.group(2) if m else ""
        return_type = (m.group(3) or "Any").strip() if m else "Any"
        params = _parse_kotlin_params(params_str)

        settings = get_settings()
        execution_timeout = settings.verifier.execution_timeout

        with tempfile.TemporaryDirectory() as tmp:
            sol_path = Path(tmp) / "Solution.kt"
            main_path = Path(tmp) / "Main.kt"
            jar_path = Path(tmp) / "solution.jar"

            sol_path.write_text(code, encoding="utf-8")
            main_path.write_text(
                self._build_test_harness(method_name, params, input_args, return_type),
                encoding="utf-8",
            )

            try:
                compile_proc = subprocess.run(
                    [
                        "kotlinc",
                        str(sol_path),
                        str(main_path),
                        "-include-runtime",
                        "-d",
                        str(jar_path),
                    ],
                    capture_output=True,
                    text=True,
                    timeout=60,
                )
            except subprocess.TimeoutExpired:
                return TestResult(
                    passed=False,
                    input_args=input_args,
                    expected=expected_output,
                    actual=None,
                    error="Compilation timed out",
                )
            except FileNotFoundError:
                return TestResult(
                    passed=False,
                    input_args=input_args,
                    expected=expected_output,
                    actual=None,
                    error="kotlinc not found",
                )

            if compile_proc.returncode != 0:
                errors = [
                    line
                    for line in (
                        compile_proc.stdout + compile_proc.stderr
                    ).splitlines()
                    if ": error:" in line
                ]
                msg = (
                    "\n".join(errors)
                    if errors
                    else (compile_proc.stdout + compile_proc.stderr).strip()
                )
                return TestResult(
                    passed=False,
                    input_args=input_args,
                    expected=expected_output,
                    actual=None,
                    error=f"Compilation error: {msg}",
                )

            try:
                run_proc = subprocess.run(
                    ["java", "-jar", str(jar_path)],
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
                    error="java not found",
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
        params: list[dict],
        input_args: list,
        return_type: str,
    ) -> str:
        """Generate Main.kt content for running a single test case."""
        lines = ["fun main() {", "    val sol = Solution()"]

        param_names = []
        for i, (param, value) in enumerate(zip(params, input_args)):
            kt_type = param["type"]
            name = f"p{i}"
            literal = self._python_to_kotlin_literal(value, kt_type)
            lines.append(f"    val {name}: {kt_type} = {literal}")
            param_names.append(name)

        args_str = ", ".join(param_names)
        lines.append(f"    val result = sol.{method_name}({args_str})")
        lines.append("    val q = 34.toChar()")
        lines.append('    println("{${q}result${q}:" + toJson(result) + "}")')
        lines.append("}")
        lines.append("")
        lines.append(_KOTLIN_TO_JSON)
        return "\n".join(lines)

    @staticmethod
    def _python_to_kotlin_literal(value: Any, kt_type: str) -> str:
        """Convert a Python value to a Kotlin literal matching kt_type."""
        kt_type = kt_type.strip()
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
                if "List" in kt_type:
                    return "listOf()"
                if kt_type == "IntArray":
                    return "intArrayOf()"
                return "arrayOf()"
            if kt_type == "IntArray":
                items = ", ".join(str(v) for v in value)
                return f"intArrayOf({items})"
            if kt_type == "LongArray":
                items = ", ".join(str(v) for v in value)
                return f"longArrayOf({items})"
            if kt_type.startswith("List<"):
                inner = kt_type[5:-1]
                items = ", ".join(
                    KotlinLanguage._python_to_kotlin_literal(v, inner) for v in value
                )
                return f"listOf({items})"
            if kt_type.startswith("Array<"):
                inner = kt_type[6:-1]
                items = ", ".join(
                    KotlinLanguage._python_to_kotlin_literal(v, inner) for v in value
                )
                return f"arrayOf({items})"
            # Fallback by Python value type
            if value and isinstance(value[0], list):
                inner_items = [
                    "intArrayOf(" + ", ".join(str(v) for v in row) + ")"
                    for row in value
                ]
                return "arrayOf(" + ", ".join(inner_items) + ")"
            if value and isinstance(value[0], str):
                items = ", ".join(f'"{v}"' for v in value)
                return f"arrayOf({items})"
            items = ", ".join(str(v) for v in value)
            return f"intArrayOf({items})"
        return str(value)


def _split_kotlin_params(params_str: str) -> list[str]:
    """Split param string by comma, ignoring commas inside angle brackets."""
    parts: list[str] = []
    depth = 0
    current: list[str] = []
    for ch in params_str:
        if ch == "<":
            depth += 1
            current.append(ch)
        elif ch == ">":
            depth -= 1
            current.append(ch)
        elif ch == "," and depth == 0:
            part = "".join(current).strip()
            if part:
                parts.append(part)
            current = []
        else:
            current.append(ch)
    part = "".join(current).strip()
    if part:
        parts.append(part)
    return parts


def _parse_kotlin_params(params_str: str) -> list[dict]:
    """Parse Kotlin param string into list of {name, type} dicts.

    Kotlin params are formatted as `name: Type`, e.g. `nums: IntArray`.
    """
    result = []
    for param in _split_kotlin_params(params_str):
        param = param.strip()
        if ": " in param:
            name, type_ = param.split(": ", 1)
            result.append({"name": name.strip(), "type": type_.strip()})
    return result
