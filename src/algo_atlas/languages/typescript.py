"""TypeScript language support for AlgoAtlas."""

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


class TypeScriptLanguage(LanguageSupport):
    """TypeScript language support using tsx (Node.js)."""

    def info(self) -> LanguageInfo:
        return LanguageInfo(
            name="TypeScript",
            slug="typescript",
            file_extension=".ts",
            solution_filename="solution.ts",
            code_fence="typescript",
            leetcode_slugs=["typescript"],
        )

    def _tsx_cmd(self) -> list[str]:
        """Return the command to invoke tsx.

        Prefers globally-installed tsx, falls back to npx tsx.
        Uses shutil.which() for full path resolution (needed on Windows
        where npx is a .cmd file).
        """
        tsx_path = shutil.which("tsx")
        if tsx_path:
            return [tsx_path]
        npx_path = shutil.which("npx")
        if npx_path:
            return [npx_path, "--yes", "tsx"]
        return ["tsx"]

    def can_run_tests(self) -> bool:
        """Check if tsx or npx is available."""
        return shutil.which("tsx") is not None or shutil.which("npx") is not None

    def check_syntax(self, code: str) -> SyntaxResult:
        """Check TypeScript syntax by running through tsx.

        tsx (esbuild) strips type annotations and checks syntax.
        Since LeetCode solutions are function definitions, running
        them is safe (defines the function, then exits).
        """
        if not self.can_run_tests():
            return SyntaxResult(
                valid=False,
                error_message=(
                    "tsx not found. Install with: npm install -g tsx"
                ),
            )

        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(
                suffix=".ts", mode="w", encoding="utf-8", delete=False,
            ) as f:
                f.write(code)
                tmp_path = f.name

            result = subprocess.run(
                [*self._tsx_cmd(), tmp_path],
                capture_output=True,
                text=True,
                timeout=15,
            )

            Path(tmp_path).unlink(missing_ok=True)

            if result.returncode == 0:
                return SyntaxResult(valid=True)

            stderr = result.stderr.strip()
            error_msg = stderr
            error_line = None

            # esbuild/tsx format: "<file>:<line>:<col>: ERROR: <message>"
            for line in stderr.split("\n"):
                if ".ts:" in line and "ERROR:" in line:
                    # Extract line number and message
                    after_ts = line.split(".ts:", 1)[1]
                    parts = after_ts.split(":", 2)
                    if len(parts) >= 3:
                        try:
                            error_line = int(parts[0])
                        except ValueError:
                            pass
                        msg_part = parts[2].strip()
                        if msg_part.startswith("ERROR:"):
                            msg_part = msg_part[len("ERROR:"):].strip()
                        error_msg = msg_part
                    break

            return SyntaxResult(
                valid=False,
                error_message=error_msg,
                error_line=error_line,
            )

        except FileNotFoundError:
            return SyntaxResult(
                valid=False,
                error_message=(
                    "tsx not found. Install with: npm install -g tsx"
                ),
            )
        except subprocess.TimeoutExpired:
            if tmp_path:
                Path(tmp_path).unlink(missing_ok=True)
            return SyntaxResult(
                valid=False,
                error_message="Syntax check timed out",
            )

    def extract_method_name(self, code: str) -> Optional[str]:
        """Extract the main function name — stub for Commit 2."""
        return None

    def count_method_params(self, code: str) -> int:
        """Count parameters — stub for Commit 2."""
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
            error="TypeScript test execution not yet implemented",
        )
