"""Swift language support for AlgoAtlas."""

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

# JSON serialiser injected into the test harness.
# Uses UnicodeScalar codes 34 (") and 92 (\) to avoid escape sequences here.
_SWIFT_JSON_HELPER = """\
func toJson(_ value: Any?) -> String {
    if value == nil { return "null" }
    if let b = value as? Bool { return b ? "true" : "false" }
    if let i = value as? Int { return "\\(i)" }
    if let d = value as? Double { return "\\(d)" }
    if let arr = value as? [Int] { return "[" + arr.map { "\\($0)" }.joined(separator: ",") + "]" }
    if let arr = value as? [[Int]] { return "[" + arr.map { toJson($0) }.joined(separator: ",") + "]" }
    if let arr = value as? [String] { return "[" + arr.map { toJson($0) }.joined(separator: ",") + "]" }
    if let s = value as? String {
        var r = String(Character(UnicodeScalar(34)!))
        for c in s {
            if c == Character(UnicodeScalar(34)!) { r += String(Character(UnicodeScalar(92)!)) + String(Character(UnicodeScalar(34)!)) }
            else if c == Character(UnicodeScalar(92)!) { r += String(Character(UnicodeScalar(92)!)) + String(Character(UnicodeScalar(92)!)) }
            else { r.append(c) }
        }
        return r + String(Character(UnicodeScalar(34)!))
    }
    return "\\(value!)"
}
"""


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
        for m in _METHOD_PATTERN.finditer(code):
            name = m.group(1)
            if name not in _SWIFT_KEYWORDS:
                return name
        return None

    def count_method_params(self, code: str) -> int:
        m = _METHOD_PATTERN.search(code)
        if not m:
            return 0
        return len(_split_swift_params(m.group(2)))

    def run_test_case(
        self, code: str, input_args: list, expected_output: Any
    ) -> TestResult:
        if not shutil.which("swiftc"):
            return TestResult(
                passed=False,
                input_args=input_args,
                expected=expected_output,
                actual=None,
                error="swiftc not found",
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
        params = _parse_swift_params(params_str)

        settings = get_settings()
        execution_timeout = settings.verifier.execution_timeout

        with tempfile.TemporaryDirectory() as tmp:
            sol_path = Path(tmp) / "Solution.swift"
            main_path = Path(tmp) / "Main.swift"
            binary_path = Path(tmp) / "solution"

            sol_path.write_text(code, encoding="utf-8")
            main_path.write_text(
                self._build_test_harness(method_name, params, input_args, return_type),
                encoding="utf-8",
            )

            try:
                compile_proc = subprocess.run(
                    [
                        "swiftc",
                        str(sol_path),
                        str(main_path),
                        "-o",
                        str(binary_path),
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
                    error="swiftc not found",
                )

            if compile_proc.returncode != 0:
                errors = [
                    line
                    for line in (compile_proc.stdout + compile_proc.stderr).splitlines()
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
                    [str(binary_path)],
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
        """Generate Main.swift content for running a single test case."""
        lines = []

        param_names = []
        for i, (param, value) in enumerate(zip(params, input_args)):
            swift_type = param["type"]
            name = f"p{i}"
            literal = self._python_to_swift_literal(value, swift_type)
            lines.append(f"let {name}: {swift_type} = {literal}")
            param_names.append((param["external"], name))

        call_args = []
        for external, name in param_names:
            if external == "_":
                call_args.append(name)
            else:
                call_args.append(f"{external}: {name}")

        args_str = ", ".join(call_args)
        lines.append("let sol = Solution()")
        lines.append(f"let result = sol.{method_name}({args_str})")
        lines.append("let q = String(Character(UnicodeScalar(34)!))")
        lines.append('print("{\\(q)result\\(q):\\(toJson(result))}")')
        lines.append("")
        lines.append(_SWIFT_JSON_HELPER)
        return "\n".join(lines)

    @staticmethod
    def _python_to_swift_literal(value: Any, swift_type: str) -> str:
        """Convert a Python value to a Swift literal matching swift_type."""
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
            if isinstance(value[0], list):
                items = ", ".join(
                    "[" + ", ".join(str(v) for v in row) + "]" for row in value
                )
                return f"[{items}]"
            if isinstance(value[0], str):
                items = ", ".join(f'"{v}"' for v in value)
                return f"[{items}]"
            items = ", ".join(str(v) for v in value)
            return f"[{items}]"
        return str(value)


def _split_swift_params(params_str: str) -> list[str]:
    """Split param string by comma, ignoring commas inside brackets or angle brackets."""
    parts: list[str] = []
    depth = 0
    current: list[str] = []
    for ch in params_str:
        if ch in ("[", "<"):
            depth += 1
            current.append(ch)
        elif ch in ("]", ">"):
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


def _parse_swift_params(params_str: str) -> list[dict]:
    """Parse Swift param string into list of {external, internal, type} dicts.

    Swift params: `_ nums: [Int]`, `target: Int`, `_ matrix: [[Int]]`.
    """
    result = []
    for param in _split_swift_params(params_str):
        param = param.strip()
        if ": " not in param:
            continue
        left, type_ = param.split(": ", 1)
        parts = left.strip().split()
        if len(parts) == 2:
            external, internal = parts
        else:
            external = internal = parts[0]
        result.append(
            {"external": external, "internal": internal, "type": type_.strip()}
        )
    return result
