"""C++ language support for AlgoAtlas."""

import json
import re
import shutil
import subprocess
import sys
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

# Common LeetCode C++ includes
_CPP_PREAMBLE = """\
#include <vector>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <map>
#include <set>
#include <queue>
#include <stack>
#include <algorithm>
#include <numeric>
#include <climits>
#include <cmath>
#include <sstream>
using namespace std;
"""


# Overloaded toJson helpers for manual JSON serialisation in the test harness.
# Uses C++ function overloading so toJson(sol.method(...)) resolves at compile time.
# The template handles vector<T> and vector<vector<T>> recursively.
_CPP_TO_JSON = r"""
string toJson(bool val) { return val ? "true" : "false"; }
string toJson(int val) { return to_string(val); }
string toJson(long long val) { return to_string(val); }
string toJson(double val) { return to_string(val); }
string toJson(float val) { return to_string(val); }
string toJson(const string& val) {
    string r = "\"";
    for (char c : val) {
        if (c == '"') r += "\\\"";
        else if (c == '\\') r += "\\\\";
        else r += c;
    }
    return r + "\"";
}
template<typename T>
string toJson(const vector<T>& val) {
    string r = "[";
    for (size_t i = 0; i < val.size(); i++) {
        if (i) r += ",";
        r += toJson(val[i]);
    }
    return r + "]";
}
"""

# C++ keywords that may appear as `keyword(...)` — not method names
_CPP_KEYWORDS = frozenset({"if", "for", "while", "switch", "catch", "return"})

# Matches a method definition inside class Solution (must be indented).
# Captures: group(1) = method name, group(2) = raw params string.
# Return type may include spaces (e.g. "long long"), templates (e.g. "vector<int>"),
# pointers ("ListNode*") — handled by the non-greedy [\w<>\[\]*&,:\s]+? match.
# Requiring [^{]*\{ at the end filters out plain function calls.
_METHOD_PATTERN = re.compile(
    r"^[ \t]+"                     # indented line
    r"(?!//)"                      # not a comment
    r"(?:[\w<>\[\]*&,:\s]+?)\s+"   # return type (non-greedy, handles long long)
    r"(\w+)\s*"                    # method name
    r"\(([^)]*)\)"                 # params
    r"[^{]*\{",                    # up to opening brace (method definition)
    re.MULTILINE,
)


class CppLanguage(LanguageSupport):
    """C++ language support using g++."""

    def info(self) -> LanguageInfo:
        return LanguageInfo(
            name="C++",
            slug="cpp",
            file_extension=".cpp",
            solution_filename="solution.cpp",
            code_fence="cpp",
            leetcode_slugs=["cpp"],
        )

    def can_run_tests(self) -> bool:
        """Check if g++ is available."""
        return shutil.which("g++") is not None

    def check_syntax(self, code: str) -> SyntaxResult:
        """Check C++ syntax using g++ -fsyntax-only -std=c++17.

        Writes the code (with preamble) to a temp .cpp file and runs
        g++ --syntax-only. If it succeeds, syntax is valid.
        """
        if not code.strip():
            return SyntaxResult(valid=True)

        if not self.can_run_tests():
            return SyntaxResult(
                valid=False,
                error_message="g++ not found. Install GCC from https://gcc.gnu.org/",
            )

        tmp_dir = None
        try:
            tmp_dir = tempfile.mkdtemp()
            src_path = Path(tmp_dir) / "solution.cpp"
            src_path.write_text(_CPP_PREAMBLE + code, encoding="utf-8")

            result = subprocess.run(
                ["g++", "-fsyntax-only", "-std=c++17", str(src_path)],
                capture_output=True,
                text=True,
                timeout=15,
            )

            if result.returncode == 0:
                return SyntaxResult(valid=True)

            stderr = result.stderr.strip()
            error_msg = stderr
            error_line = None

            # g++ error format: "solution.cpp:5:3: error: ..."
            for line in stderr.split("\n"):
                if "solution.cpp:" in line and "error:" in line:
                    parts = line.split("solution.cpp:", 1)[1]
                    colon_idx = parts.find(":")
                    if colon_idx > 0:
                        try:
                            raw_line = int(parts[:colon_idx])
                            preamble_lines = _CPP_PREAMBLE.count("\n")
                            error_line = max(1, raw_line - preamble_lines)
                        except ValueError:
                            pass
                        rest = parts[colon_idx + 1:].strip()
                        col_end = rest.find(":")
                        if col_end > 0:
                            rest = rest[col_end + 1:].strip()
                        if rest.startswith("error:"):
                            rest = rest[len("error:"):].strip()
                        error_msg = rest
                    break

            return SyntaxResult(
                valid=False,
                error_message=error_msg,
                error_line=error_line,
            )

        except FileNotFoundError:
            return SyntaxResult(
                valid=False,
                error_message="g++ not found. Install GCC from https://gcc.gnu.org/",
            )
        except subprocess.TimeoutExpired:
            return SyntaxResult(
                valid=False,
                error_message="Syntax check timed out",
            )
        finally:
            if tmp_dir:
                shutil.rmtree(tmp_dir, ignore_errors=True)

    def extract_method_name(self, code: str) -> Optional[str]:
        """Extract the main method name from a LeetCode C++ solution.

        Looks for the first indented method definition inside class Solution
        that is not a constructor or a C++ control-flow keyword.
        """
        for m in _METHOD_PATTERN.finditer(code):
            name = m.group(1)
            if name != "Solution" and name not in _CPP_KEYWORDS:
                return name
        return None

    def count_method_params(self, code: str) -> int:
        """Count parameters in the C++ solution method.

        Handles template types with commas (e.g. unordered_map<string, int>)
        by only counting commas at angle-bracket depth 0.
        """
        for m in _METHOD_PATTERN.finditer(code):
            name = m.group(1)
            if name != "Solution" and name not in _CPP_KEYWORDS:
                params_str = m.group(2).strip()
                return self._count_cpp_params(params_str)
        return 0

    @staticmethod
    def _count_cpp_params(params_str: str) -> int:
        """Count C++ params, respecting template angle-bracket nesting."""
        if not params_str:
            return 0
        depth = 0
        count = 1
        for ch in params_str:
            if ch == "<":
                depth += 1
            elif ch == ">":
                depth -= 1
            elif ch == "," and depth == 0:
                count += 1
        return count

    def run_test_case(
        self,
        code: str,
        input_args: list[Any],
        expected_output: Any,
        timeout: Optional[int] = None,
    ) -> TestResult:
        """Run a single test case by compiling and executing via g++.

        Builds a single .cpp file (preamble + user code + toJson helpers + main),
        compiles with g++ -std=c++17, runs the binary, and parses JSON from stdout.
        """
        if timeout is None:
            timeout = get_settings().execution_timeout

        method_name = self.extract_method_name(code)
        if not method_name:
            return TestResult(
                passed=False,
                input_args=input_args,
                expected=expected_output,
                actual=None,
                error="Could not extract method name from C++ solution",
            )

        tmp_dir = None
        try:
            tmp_dir = tempfile.mkdtemp()
            src_path = Path(tmp_dir) / "solution.cpp"
            src_path.write_text(
                self._build_test_harness(code, method_name, input_args),
                encoding="utf-8",
            )

            bin_name = "solution.exe" if sys.platform == "win32" else "solution"
            bin_path = Path(tmp_dir) / bin_name

            compile_result = subprocess.run(
                ["g++", "-std=c++17", "-O0", "-o", str(bin_path), str(src_path)],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if compile_result.returncode != 0:
                return TestResult(
                    passed=False,
                    input_args=input_args,
                    expected=expected_output,
                    actual=None,
                    error=f"Compilation error: {compile_result.stderr.strip()}",
                )

            run_result = subprocess.run(
                [str(bin_path)],
                capture_output=True,
                text=True,
                timeout=timeout,
            )

            stdout = run_result.stdout.strip()
            try:
                data = json.loads(stdout)
            except (json.JSONDecodeError, ValueError):
                detail = run_result.stderr.strip() or stdout or "No output"
                return TestResult(
                    passed=False,
                    input_args=input_args,
                    expected=expected_output,
                    actual=None,
                    error=f"Runtime error: {detail}",
                )

            if "error" in data:
                return TestResult(
                    passed=False,
                    input_args=input_args,
                    expected=expected_output,
                    actual=None,
                    error=data["error"],
                )

            actual = data.get("result")
            return TestResult(
                passed=actual == expected_output,
                input_args=input_args,
                expected=expected_output,
                actual=actual,
            )

        except FileNotFoundError:
            return TestResult(
                passed=False,
                input_args=input_args,
                expected=expected_output,
                actual=None,
                error="g++ not found. Install GCC from https://gcc.gnu.org/",
            )
        except subprocess.TimeoutExpired:
            return TestResult(
                passed=False,
                input_args=input_args,
                expected=expected_output,
                actual=None,
                error="Execution timed out",
            )
        finally:
            if tmp_dir:
                shutil.rmtree(tmp_dir, ignore_errors=True)

    def _build_test_harness(
        self, code: str, method_name: str, input_args: list[Any]
    ) -> str:
        """Build a complete .cpp file: preamble + solution + toJson + main."""
        args_str = ", ".join(self._python_to_cpp_literal(a) for a in input_args)
        main_fn = (
            "int main() {\n"
            "    Solution sol;\n"
            "    try {\n"
            f"        auto result = sol.{method_name}({args_str});\n"
            '        cout << "{\\"result\\":" << toJson(result) << "}" << endl;\n'
            "    } catch (const exception& e) {\n"
            '        cout << "{\\"error\\":\\"" << e.what() << "\\"}" << endl;\n'
            "        return 1;\n"
            "    }\n"
            "    return 0;\n"
            "}\n"
        )
        return _CPP_PREAMBLE + code + "\n" + _CPP_TO_JSON + "\n" + main_fn

    @staticmethod
    def _python_to_cpp_literal(value: Any) -> str:
        """Convert a Python value to its C++ literal representation."""
        if value is None:
            return "nullptr"
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, int):
            return str(value)
        if isinstance(value, float):
            return repr(value)
        if isinstance(value, str):
            escaped = value.replace("\\", "\\\\").replace('"', '\\"')
            return f'string("{escaped}")'
        if isinstance(value, list):
            if not value:
                return "vector<int>{}"
            if all(isinstance(x, bool) for x in value):
                inner = ", ".join("true" if x else "false" for x in value)
                return f"vector<bool>{{{inner}}}"
            if all(isinstance(x, int) for x in value):
                inner = ", ".join(str(x) for x in value)
                return f"vector<int>{{{inner}}}"
            if all(isinstance(x, str) for x in value):
                inner = ", ".join(
                    f'string("{x.replace(chr(92), chr(92)*2).replace(chr(34), chr(92)+chr(34))}")'
                    for x in value
                )
                return f"vector<string>{{{inner}}}"
            if all(isinstance(x, list) for x in value):
                rows = ", ".join(
                    "vector<int>{" + ", ".join(str(i) for i in row) + "}"
                    for row in value
                )
                return f"vector<vector<int>>{{{rows}}}"
        return str(value)
