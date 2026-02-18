"""Java language support for AlgoAtlas."""

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


class JavaLanguage(LanguageSupport):
    """Java language support using javac/java."""

    def info(self) -> LanguageInfo:
        return LanguageInfo(
            name="Java",
            slug="java",
            file_extension=".java",
            solution_filename="Solution.java",
            code_fence="java",
            leetcode_slugs=["java"],
        )

    def can_run_tests(self) -> bool:
        """Check if javac and java are available."""
        return (
            shutil.which("javac") is not None
            and shutil.which("java") is not None
        )

    def check_syntax(self, code: str) -> SyntaxResult:
        """Check Java syntax using javac.

        Writes the code to a temp Solution.java file and compiles
        with javac. If compilation succeeds, syntax is valid.
        """
        if not code.strip():
            return SyntaxResult(valid=True)

        if not self.can_run_tests():
            return SyntaxResult(
                valid=False,
                error_message="javac not found. Install JDK from https://jdk.java.net/",
            )

        tmp_dir = None
        try:
            tmp_dir = tempfile.mkdtemp()
            src_path = Path(tmp_dir) / "Solution.java"
            src_path.write_text(code, encoding="utf-8")

            result = subprocess.run(
                ["javac", str(src_path)],
                capture_output=True,
                text=True,
                timeout=15,
            )

            if result.returncode == 0:
                return SyntaxResult(valid=True)

            stderr = result.stderr.strip()
            error_msg = stderr
            error_line = None

            # javac error format: "Solution.java:3: error: ';' expected"
            for line in stderr.split("\n"):
                if "Solution.java:" in line and "error:" in line:
                    parts = line.split("Solution.java:", 1)[1]
                    colon_idx = parts.find(":")
                    if colon_idx > 0:
                        try:
                            error_line = int(parts[:colon_idx])
                        except ValueError:
                            pass
                        msg = parts[colon_idx + 1:].strip()
                        if msg.startswith("error:"):
                            msg = msg[len("error:"):].strip()
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
                error_message="javac not found. Install JDK from https://jdk.java.net/",
            )
        except subprocess.TimeoutExpired:
            return SyntaxResult(
                valid=False,
                error_message="Compilation timed out",
            )
        finally:
            if tmp_dir:
                import shutil as sh
                sh.rmtree(tmp_dir, ignore_errors=True)

    # Pattern for LeetCode Java method signatures inside class Solution.
    # Matches: public <returnType> methodName(<params>)
    # Return type can be multi-word like "int[]", "List<Integer>", etc.
    _METHOD_PATTERN = re.compile(
        r"public\s+\S+\s+(\w+)\s*\(([^)]*)\)"
    )

    def extract_method_name(self, code: str) -> Optional[str]:
        """Extract the main method name from LeetCode Java solution.

        Looks for the first public non-constructor method inside the
        Solution class, matching `public <type> methodName(...)`.
        """
        match = self._METHOD_PATTERN.search(code)
        if match:
            name = match.group(1)
            # Skip constructors (method name == "Solution")
            if name == "Solution":
                # Try to find the next match
                for m in self._METHOD_PATTERN.finditer(code):
                    if m.group(1) != "Solution":
                        return m.group(1)
                return None
            return name
        return None

    def count_method_params(self, code: str) -> int:
        """Count parameters in the Java solution method.

        Each parameter is `type name` separated by commas.
        """
        match = self._METHOD_PATTERN.search(code)
        if match:
            name = match.group(1)
            params_str = match.group(2).strip()
            # Skip constructors
            if name == "Solution":
                for m in self._METHOD_PATTERN.finditer(code):
                    if m.group(1) != "Solution":
                        params_str = m.group(2).strip()
                        break
                else:
                    return 0
            if not params_str:
                return 0
            return len([p.strip() for p in params_str.split(",") if p.strip()])
        return 0

    def run_test_case(
        self,
        code: str,
        input_args: list[Any],
        expected_output: Any,
        timeout: Optional[int] = None,
    ) -> TestResult:
        """Run test case — stub for Commit 3."""
        return TestResult(
            passed=False,
            input_args=input_args,
            expected=expected_output,
            actual=None,
            error="Java test execution not yet implemented",
        )
