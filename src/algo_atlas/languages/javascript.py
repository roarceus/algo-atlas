"""JavaScript language support for AlgoAtlas."""

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


class JavaScriptLanguage(LanguageSupport):
    """JavaScript language support using Node.js."""

    def info(self) -> LanguageInfo:
        return LanguageInfo(
            name="JavaScript",
            slug="javascript",
            file_extension=".js",
            solution_filename="solution.js",
            code_fence="javascript",
            leetcode_slugs=["javascript"],
        )

    def can_run_tests(self) -> bool:
        """Check if Node.js is available."""
        return shutil.which("node") is not None

    def check_syntax(self, code: str) -> SyntaxResult:
        """Check JavaScript syntax using node --check."""
        if not self.can_run_tests():
            return SyntaxResult(
                valid=False,
                error_message="Node.js not found. Install from https://nodejs.org/",
            )

        try:
            with tempfile.NamedTemporaryFile(
                suffix=".js", mode="w", encoding="utf-8", delete=False,
            ) as f:
                f.write(code)
                tmp_path = f.name

            result = subprocess.run(
                ["node", "--check", tmp_path],
                capture_output=True,
                text=True,
                timeout=10,
            )

            Path(tmp_path).unlink(missing_ok=True)

            if result.returncode == 0:
                return SyntaxResult(valid=True)

            # Parse error message from stderr
            error_msg = result.stderr.strip()
            error_line = None

            # Node error format: "file.js:3\n  code\n  ^\nSyntaxError: ..."
            for line in error_msg.split("\n"):
                if tmp_path.replace("\\", "/") in line.replace("\\", "/") or (
                    ":" in line and line.split(":")[0].endswith(".js")
                ):
                    parts = line.rsplit(":", 1)
                    if len(parts) == 2:
                        try:
                            error_line = int(parts[1])
                        except ValueError:
                            pass
                    break

            # Extract the SyntaxError message
            for line in error_msg.split("\n"):
                if line.startswith("SyntaxError:"):
                    error_msg = line
                    break

            return SyntaxResult(
                valid=False,
                error_message=error_msg,
                error_line=error_line,
            )

        except FileNotFoundError:
            return SyntaxResult(
                valid=False,
                error_message="Node.js not found. Install from https://nodejs.org/",
            )
        except subprocess.TimeoutExpired:
            Path(tmp_path).unlink(missing_ok=True)
            return SyntaxResult(
                valid=False,
                error_message="Syntax check timed out",
            )

    def extract_method_name(self, code: str) -> Optional[str]:
        """Extract method name — stub for Commit 2."""
        return None

    def count_method_params(self, code: str) -> int:
        """Count method params — stub for Commit 2."""
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
            error="JavaScript test execution not yet implemented",
        )
