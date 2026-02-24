"""Go language support for AlgoAtlas."""

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

# Package declaration prepended to user code for syntax checking.
# Using a non-main package avoids the "func main is undeclared" error.
_GO_PACKAGE = "package solution\n\n"

# Minimal go.mod for the temp module used during syntax checking.
_GO_MOD = "module solution\n\ngo 1.18\n"

# Go function names that must not be mistaken for the solution method.
_GO_KEYWORDS = frozenset({"main", "init"})

# Matches a top-level Go function definition.
# group(1) = function name, group(2) = raw params string.
# Params are bounded by the first closing paren; Go types never use parens
# inside a parameter list (slices use [], maps use []), so [^)]* is safe.
_FUNC_PATTERN = re.compile(
    r"^func\s+"       # 'func' keyword at line start
    r"(\w+)\s*"       # group(1) = function name
    r"\(([^)]*)\)",   # group(2) = raw params string
    re.MULTILINE,
)


class GoLanguage(LanguageSupport):
    """Go language support using the go toolchain."""

    def info(self) -> LanguageInfo:
        return LanguageInfo(
            name="Go",
            slug="go",
            file_extension=".go",
            solution_filename="solution.go",
            code_fence="go",
            leetcode_slugs=["golang"],
        )

    def can_run_tests(self) -> bool:
        """Check if the go toolchain is available."""
        return shutil.which("go") is not None

    def check_syntax(self, code: str) -> SyntaxResult:
        """Check Go syntax by compiling in a temporary module with go build.

        Writes a minimal go.mod and a solution.go (package solution + user
        code) into a temp directory, then runs 'go build .' to catch syntax
        and type errors.
        """
        if not code.strip():
            return SyntaxResult(valid=True)

        if not self.can_run_tests():
            return SyntaxResult(
                valid=False,
                error_message="go not found. Install Go from https://go.dev/",
            )

        tmp_dir = None
        try:
            tmp_dir = tempfile.mkdtemp()
            tmp_path = Path(tmp_dir)
            (tmp_path / "go.mod").write_text(_GO_MOD, encoding="utf-8")
            (tmp_path / "solution.go").write_text(
                _GO_PACKAGE + code, encoding="utf-8"
            )

            result = subprocess.run(
                ["go", "build", "."],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=str(tmp_path),
            )

            if result.returncode == 0:
                return SyntaxResult(valid=True)

            stderr = result.stderr.strip()
            error_msg = stderr
            error_line = None

            # go build error format: "./solution.go:<line>:<col>: <message>"
            for line in stderr.split("\n"):
                if "solution.go:" in line:
                    parts = line.split("solution.go:", 1)[1]
                    colon_idx = parts.find(":")
                    if colon_idx > 0:
                        try:
                            raw_line = int(parts[:colon_idx])
                            preamble_lines = _GO_PACKAGE.count("\n")
                            error_line = max(1, raw_line - preamble_lines)
                        except ValueError:
                            pass
                        rest = parts[colon_idx + 1:].strip()
                        # skip column number
                        col_end = rest.find(":")
                        if col_end > 0:
                            rest = rest[col_end + 1:].strip()
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
                error_message="go not found. Install Go from https://go.dev/",
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
        """Extract the main function name from a LeetCode Go solution.

        Looks for the first top-level func definition whose name is not
        a reserved entry-point name (main, init).
        """
        for m in _FUNC_PATTERN.finditer(code):
            name = m.group(1)
            if name not in _GO_KEYWORDS:
                return name
        return None

    def count_method_params(self, code: str) -> int:
        """Count parameters in the Go solution function.

        Go types never contain commas (slices use [], maps use [key]val),
        so a plain comma split on the params string is correct.
        """
        for m in _FUNC_PATTERN.finditer(code):
            name = m.group(1)
            if name not in _GO_KEYWORDS:
                params_str = m.group(2).strip()
                if not params_str:
                    return 0
                return len([p for p in params_str.split(",") if p.strip()])
        return 0

    def run_test_case(
        self,
        code: str,
        input_args: list[Any],
        expected_output: Any,
        timeout: Optional[int] = None,
    ) -> TestResult:
        """Run a single test case against the Go solution."""
        return TestResult(
            passed=False,
            input_args=input_args,
            expected=expected_output,
            actual=None,
            error="Not implemented",
        )
