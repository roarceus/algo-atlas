"""C++ language support for AlgoAtlas."""

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
        """Extract the main method name from a LeetCode C++ solution."""
        raise NotImplementedError

    def count_method_params(self, code: str) -> int:
        """Count parameters in the C++ solution method."""
        raise NotImplementedError

    def run_test_case(
        self,
        code: str,
        input_args: list[Any],
        expected_output: Any,
        timeout: Optional[int] = None,
    ) -> TestResult:
        """Run a single test case by compiling and running via g++."""
        raise NotImplementedError
