"""JavaScript language support for AlgoAtlas."""

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

    # Patterns for LeetCode JS function signatures
    _FUNC_PATTERNS = [
        # var/let/const name = function(params) {
        re.compile(
            r"(?:var|let|const)\s+(\w+)\s*=\s*function\s*\(([^)]*)\)"
        ),
        # function name(params) {
        re.compile(
            r"function\s+(\w+)\s*\(([^)]*)\)"
        ),
        # var/let/const name = (params) =>
        re.compile(
            r"(?:var|let|const)\s+(\w+)\s*=\s*\(([^)]*)\)\s*=>"
        ),
        # var/let/const name = param =>  (single param arrow, no parens)
        re.compile(
            r"(?:var|let|const)\s+(\w+)\s*=\s*(\w+)\s*=>"
        ),
    ]

    def extract_method_name(self, code: str) -> Optional[str]:
        """Extract the main function name from LeetCode JS solution.

        Supports: var/let/const name = function(...), function name(...),
        arrow functions with var/let/const.
        """
        for pattern in self._FUNC_PATTERNS:
            match = pattern.search(code)
            if match:
                return match.group(1)
        return None

    def count_method_params(self, code: str) -> int:
        """Count parameters in the JS solution function."""
        for pattern in self._FUNC_PATTERNS:
            match = pattern.search(code)
            if match:
                params_str = match.group(2).strip()
                if not params_str:
                    return 0
                # For single-param arrow (no parens), group(2) is the param name
                if pattern == self._FUNC_PATTERNS[3]:
                    return 1
                return len([p.strip() for p in params_str.split(",") if p.strip()])
        return 0

    def run_test_case(
        self,
        code: str,
        input_args: list[Any],
        expected_output: Any,
        timeout: Optional[int] = None,
    ) -> TestResult:
        """Run a single test case by writing a temp .js file and running with Node."""
        if timeout is None:
            settings = get_settings()
            timeout = settings.verifier.execution_timeout

        if not self.can_run_tests():
            return TestResult(
                passed=False,
                input_args=input_args,
                expected=expected_output,
                actual=None,
                error="Node.js not found. Install from https://nodejs.org/",
            )

        # Extract function name from the solution code
        func_name = self.extract_method_name(code)
        if func_name is None:
            return TestResult(
                passed=False,
                input_args=input_args,
                expected=expected_output,
                actual=None,
                error="Could not find solution function",
            )

        # Build the test harness script
        harness = self._build_test_harness(code, func_name, input_args)

        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(
                suffix=".js", mode="w", encoding="utf-8", delete=False,
            ) as f:
                f.write(harness)
                tmp_path = f.name

            result = subprocess.run(
                ["node", tmp_path],
                capture_output=True,
                text=True,
                timeout=timeout,
            )

            Path(tmp_path).unlink(missing_ok=True)

            if result.returncode != 0:
                error_msg = result.stderr.strip() or result.stdout.strip()
                return TestResult(
                    passed=False,
                    input_args=input_args,
                    expected=expected_output,
                    actual=None,
                    error=error_msg or "Node.js execution failed",
                )

            # Parse the JSON output from the harness
            try:
                output = json.loads(result.stdout.strip())
            except json.JSONDecodeError:
                return TestResult(
                    passed=False,
                    input_args=input_args,
                    expected=expected_output,
                    actual=None,
                    error=f"Could not parse output: {result.stdout.strip()}",
                )

            if "error" in output:
                return TestResult(
                    passed=False,
                    input_args=input_args,
                    expected=expected_output,
                    actual=None,
                    error=output["error"],
                )

            from algo_atlas.core.verifier import _compare_results

            actual = output["result"]
            passed = _compare_results(expected_output, actual)

            return TestResult(
                passed=passed,
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
                error="Node.js not found. Install from https://nodejs.org/",
            )
        except subprocess.TimeoutExpired:
            if tmp_path:
                Path(tmp_path).unlink(missing_ok=True)
            return TestResult(
                passed=False,
                input_args=input_args,
                expected=expected_output,
                actual=None,
                error=f"Execution timed out after {timeout}s",
            )
        except Exception as e:
            if tmp_path:
                Path(tmp_path).unlink(missing_ok=True)
            return TestResult(
                passed=False,
                input_args=input_args,
                expected=expected_output,
                actual=None,
                error=str(e),
            )

    @staticmethod
    def _build_test_harness(
        code: str, func_name: str, input_args: list[Any],
    ) -> str:
        """Build a JavaScript test harness script.

        The harness includes the solution code, calls the function with
        the given arguments, and prints a JSON object with the result.
        """
        # Serialize each argument to a JS literal via JSON
        js_args = ", ".join(json.dumps(arg) for arg in input_args)

        # Wrap in a try/catch to capture runtime errors as JSON
        return (
            f"{code}\n\n"
            f"try {{\n"
            f"  const __result = {func_name}({js_args});\n"
            f'  process.stdout.write(JSON.stringify({{ "result": __result }}));\n'
            f"}} catch (__err) {{\n"
            f'  process.stdout.write(JSON.stringify({{ "error": __err.message }}));\n'
            f"  process.exit(1);\n"
            f"}}\n"
        )
