"""C language support for AlgoAtlas."""

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

# Common LeetCode C includes
_C_PREAMBLE = """\
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>
#include <math.h>
#include <limits.h>
"""


class CLanguage(LanguageSupport):
    """C language support using gcc."""

    def info(self) -> LanguageInfo:
        return LanguageInfo(
            name="C",
            slug="c",
            file_extension=".c",
            solution_filename="solution.c",
            code_fence="c",
            leetcode_slugs=["c"],
        )

    def can_run_tests(self) -> bool:
        """Check if gcc is available."""
        return shutil.which("gcc") is not None

    def check_syntax(self, code: str) -> SyntaxResult:
        """Check C syntax using gcc -fsyntax-only -std=c11.

        Writes the code (with preamble) to a temp .c file and runs
        gcc -fsyntax-only. If it succeeds, syntax is valid.
        """
        if not code.strip():
            return SyntaxResult(valid=True)

        if not self.can_run_tests():
            return SyntaxResult(
                valid=False,
                error_message="gcc not found. Install GCC from https://gcc.gnu.org/",
            )

        tmp_dir = None
        try:
            tmp_dir = tempfile.mkdtemp()
            src_path = Path(tmp_dir) / "solution.c"
            src_path.write_text(_C_PREAMBLE + code, encoding="utf-8")

            result = subprocess.run(
                ["gcc", "-fsyntax-only", "-std=c11", str(src_path)],
                capture_output=True,
                text=True,
                timeout=15,
            )

            if result.returncode == 0:
                return SyntaxResult(valid=True)

            stderr = result.stderr.strip()
            error_msg = stderr
            error_line = None

            # gcc error format: "solution.c:5:3: error: ..."
            for line in stderr.split("\n"):
                if "solution.c:" in line and "error:" in line:
                    parts = line.split("solution.c:", 1)[1]
                    colon_idx = parts.find(":")
                    if colon_idx > 0:
                        try:
                            raw_line = int(parts[:colon_idx])
                            preamble_lines = _C_PREAMBLE.count("\n")
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
                error_message="gcc not found. Install GCC from https://gcc.gnu.org/",
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
        """Extract the main function name from a LeetCode C solution."""
        raise NotImplementedError

    def count_method_params(self, code: str) -> int:
        """Count parameters in the C solution function."""
        raise NotImplementedError

    def run_test_case(
        self,
        code: str,
        input_args: list[Any],
        expected_output: Any,
        timeout: Optional[int] = None,
    ) -> TestResult:
        """Run a single test case by compiling and running via gcc."""
        raise NotImplementedError
