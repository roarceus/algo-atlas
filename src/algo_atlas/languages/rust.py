"""Rust language support for AlgoAtlas."""

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

# Method names inside impl Solution that are not the LeetCode solution.
_RUST_KEYWORDS = frozenset({"new", "default", "clone", "fmt", "from", "into"})

# Matches a `pub fn` inside impl Solution.
# group(1) = method name, group(2) = raw params string.
# [^)]* works for LeetCode params because Rust generic types use <> not ().
_METHOD_PATTERN = re.compile(
    r"\bpub\s+fn\s+"
    r"(\w+)\s*"       # group(1) = method name
    r"\(([^)]*)\)",   # group(2) = raw params string
    re.MULTILINE,
)

# Prepended to user code for syntax checking.
# `struct Solution;` is required for `impl Solution { ... }` to compile.
# `#![allow(dead_code)]` suppresses warnings about unused methods.
_RUST_PREAMBLE = "#![allow(dead_code)]\nstruct Solution;\n\n"


class RustLanguage(LanguageSupport):
    """Rust language support using rustc."""

    def info(self) -> LanguageInfo:
        return LanguageInfo(
            name="Rust",
            slug="rust",
            file_extension=".rs",
            solution_filename="solution.rs",
            code_fence="rust",
            leetcode_slugs=["rust"],
        )

    def can_run_tests(self) -> bool:
        """Check if rustc is available."""
        return shutil.which("rustc") is not None

    def check_syntax(self, code: str) -> SyntaxResult:
        """Check Rust syntax by compiling as a library with rustc.

        Writes a temp .rs file (preamble + user code) and runs
        'rustc --edition 2021 --crate-type lib --emit=metadata'
        to catch syntax and type errors without producing a binary.
        """
        if not code.strip():
            return SyntaxResult(valid=True)

        if not self.can_run_tests():
            return SyntaxResult(
                valid=False,
                error_message="rustc not found. Install Rust from https://rustup.rs/",
            )

        tmp_dir = None
        try:
            tmp_dir = tempfile.mkdtemp()
            tmp_path = Path(tmp_dir)
            src_path = tmp_path / "solution.rs"
            src_path.write_text(_RUST_PREAMBLE + code, encoding="utf-8")
            meta_path = tmp_path / "solution.rmeta"

            result = subprocess.run(
                [
                    "rustc",
                    "--edition", "2021",
                    "--crate-type", "lib",
                    "--emit=metadata",
                    "-o", str(meta_path),
                    str(src_path),
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                return SyntaxResult(valid=True)

            stderr = result.stderr.strip()
            error_msg = stderr
            error_line = None

            # rustc error format:
            #   error[Exxxx]: <message>
            #    --> solution.rs:<line>:<col>
            preamble_lines = _RUST_PREAMBLE.count("\n")
            lines = stderr.split("\n")
            for i, line in enumerate(lines):
                if line.startswith("error"):
                    msg = line.split(":", 1)[1].strip() if ":" in line else line
                    # Look ahead for the location line
                    for j in range(i + 1, min(i + 4, len(lines))):
                        loc = lines[j].strip()
                        if loc.startswith("--> ") and "solution.rs:" in loc:
                            parts = loc.split("solution.rs:", 1)[1]
                            col_idx = parts.find(":")
                            if col_idx > 0:
                                try:
                                    raw_line = int(parts[:col_idx])
                                    error_line = max(1, raw_line - preamble_lines)
                                except ValueError:
                                    pass
                            break
                    error_msg = msg
                    break

            return SyntaxResult(
                valid=False,
                error_message=error_msg,
                error_line=error_line,
            )

        except FileNotFoundError:
            return SyntaxResult(
                valid=False,
                error_message="rustc not found. Install Rust from https://rustup.rs/",
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
        """Extract the main method name from a LeetCode Rust solution.

        Looks for the first `pub fn` whose name is not a common utility
        method (new, clone, etc.).
        """
        for m in _METHOD_PATTERN.finditer(code):
            name = m.group(1)
            if name not in _RUST_KEYWORDS:
                return name
        return None

    def count_method_params(self, code: str) -> int:
        """Count parameters in the Rust solution method.

        Splits the param list by top-level commas (ignoring commas inside
        angle brackets, e.g. Vec<i32> or HashMap<i32, i32>), then excludes
        &self / &mut self receiver params.
        """
        for m in _METHOD_PATTERN.finditer(code):
            name = m.group(1)
            if name not in _RUST_KEYWORDS:
                params_str = m.group(2).strip()
                if not params_str:
                    return 0
                parts = self._split_rust_params(params_str)
                # Exclude &self / &mut self receiver
                parts = [
                    p for p in parts
                    if not p.lstrip("&").strip().startswith("self")
                    and not p.lstrip("&").strip().startswith("mut self")
                ]
                return len(parts)
        return 0

    @staticmethod
    def _split_rust_params(params_str: str) -> list[str]:
        """Split a Rust param list by top-level commas only.

        Commas inside angle brackets (e.g. HashMap<i32, i32>) are ignored.
        """
        params: list[str] = []
        current: list[str] = []
        depth = 0
        for ch in params_str:
            if ch == "<":
                depth += 1
                current.append(ch)
            elif ch == ">":
                depth -= 1
                current.append(ch)
            elif ch == "," and depth == 0:
                params.append("".join(current).strip())
                current = []
            else:
                current.append(ch)
        if current:
            params.append("".join(current).strip())
        return [p for p in params if p]

    def run_test_case(
        self,
        code: str,
        input_args: list[Any],
        expected_output: Any,
        timeout: Optional[int] = None,
    ) -> TestResult:
        """Run a single test case against the Rust solution."""
        return TestResult(
            passed=False,
            input_args=input_args,
            expected=expected_output,
            actual=None,
            error="Not implemented",
        )
