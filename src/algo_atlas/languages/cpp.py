"""C++ language support for AlgoAtlas."""

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
                import shutil as sh
                sh.rmtree(tmp_dir, ignore_errors=True)

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
        """Run a single test case by compiling and running via g++."""
        raise NotImplementedError
