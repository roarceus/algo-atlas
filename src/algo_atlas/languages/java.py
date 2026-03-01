"""Java language support for AlgoAtlas."""

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
        return shutil.which("javac") is not None and shutil.which("java") is not None

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
                        msg = parts[colon_idx + 1 :].strip()
                        if msg.startswith("error:"):
                            msg = msg[len("error:") :].strip()
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
    _METHOD_PATTERN = re.compile(r"public\s+\S+\s+(\w+)\s*\(([^)]*)\)")

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
        """Run a single test case by compiling and running via javac/java."""
        if timeout is None:
            settings = get_settings()
            timeout = settings.verifier.execution_timeout

        if not self.can_run_tests():
            return TestResult(
                passed=False,
                input_args=input_args,
                expected=expected_output,
                actual=None,
                error="javac not found. Install JDK from https://jdk.java.net/",
            )

        method_name = self.extract_method_name(code)
        if method_name is None:
            return TestResult(
                passed=False,
                input_args=input_args,
                expected=expected_output,
                actual=None,
                error="Could not find solution method",
            )

        tmp_dir = None
        try:
            tmp_dir = tempfile.mkdtemp()
            tmp = Path(tmp_dir)

            # Write solution and harness
            (tmp / "Solution.java").write_text(code, encoding="utf-8")
            harness = self._build_test_harness(method_name, input_args)
            (tmp / "Main.java").write_text(harness, encoding="utf-8")

            # Compile both files
            compile_result = subprocess.run(
                ["javac", "Solution.java", "Main.java"],
                capture_output=True,
                text=True,
                timeout=15,
                cwd=tmp_dir,
            )

            if compile_result.returncode != 0:
                return TestResult(
                    passed=False,
                    input_args=input_args,
                    expected=expected_output,
                    actual=None,
                    error=compile_result.stderr.strip() or "Compilation failed",
                )

            # Run
            run_result = subprocess.run(
                ["java", "Main"],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=tmp_dir,
            )

            stdout = run_result.stdout.strip()
            output = None
            if stdout:
                try:
                    output = json.loads(stdout)
                except json.JSONDecodeError:
                    pass

            if output is None:
                error_msg = run_result.stderr.strip() or stdout
                return TestResult(
                    passed=False,
                    input_args=input_args,
                    expected=expected_output,
                    actual=None,
                    error=error_msg or "java execution failed",
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
                error="javac not found. Install JDK from https://jdk.java.net/",
            )
        except subprocess.TimeoutExpired:
            return TestResult(
                passed=False,
                input_args=input_args,
                expected=expected_output,
                actual=None,
                error=f"Execution timed out after {timeout}s",
            )
        except Exception as e:
            return TestResult(
                passed=False,
                input_args=input_args,
                expected=expected_output,
                actual=None,
                error=str(e),
            )
        finally:
            if tmp_dir:
                import shutil as sh

                sh.rmtree(tmp_dir, ignore_errors=True)

    @staticmethod
    def _build_test_harness(method_name: str, input_args: list[Any]) -> str:
        """Build a Main.java harness that calls the solution and prints JSON.

        Converts Python input_args to Java literals based on value type.
        Includes a toJson() helper for common LeetCode return types.
        """
        java_args = ", ".join(
            JavaLanguage._python_to_java_literal(arg) for arg in input_args
        )

        return f"""\
import java.util.*;

public class Main {{
    public static void main(String[] args) {{
        Solution sol = new Solution();
        try {{
            Object result = sol.{method_name}({java_args});
            System.out.print("{{\\"result\\":" + toJson(result) + "}}");
        }} catch (Exception e) {{
            String msg = e.getMessage() == null ? e.getClass().getSimpleName() : e.getMessage();
            System.out.print("{{\\"error\\":\\"" + msg.replace("\\\\", "\\\\\\\\").replace("\\"", "\\\\\\"") + "\\"}}");
            System.exit(1);
        }}
    }}

    static String toJson(Object obj) {{
        if (obj == null) return "null";
        if (obj instanceof Boolean) return String.valueOf(obj);
        if (obj instanceof Number) return String.valueOf(obj);
        if (obj instanceof String) {{
            return "\\"" + ((String) obj).replace("\\\\", "\\\\\\\\").replace("\\"", "\\\\\\"") + "\\"";
        }}
        if (obj instanceof int[]) {{
            int[] arr = (int[]) obj;
            StringBuilder sb = new StringBuilder("[");
            for (int i = 0; i < arr.length; i++) {{
                if (i > 0) sb.append(",");
                sb.append(arr[i]);
            }}
            return sb.append("]").toString();
        }}
        if (obj instanceof boolean[]) {{
            boolean[] arr = (boolean[]) obj;
            StringBuilder sb = new StringBuilder("[");
            for (int i = 0; i < arr.length; i++) {{
                if (i > 0) sb.append(",");
                sb.append(arr[i]);
            }}
            return sb.append("]").toString();
        }}
        if (obj instanceof int[][]) {{
            int[][] arr = (int[][]) obj;
            StringBuilder sb = new StringBuilder("[");
            for (int i = 0; i < arr.length; i++) {{
                if (i > 0) sb.append(",");
                sb.append("[");
                for (int j = 0; j < arr[i].length; j++) {{
                    if (j > 0) sb.append(",");
                    sb.append(arr[i][j]);
                }}
                sb.append("]");
            }}
            return sb.append("]").toString();
        }}
        if (obj instanceof List) {{
            List<?> list = (List<?>) obj;
            StringBuilder sb = new StringBuilder("[");
            for (int i = 0; i < list.size(); i++) {{
                if (i > 0) sb.append(",");
                sb.append(toJson(list.get(i)));
            }}
            return sb.append("]").toString();
        }}
        return "\\"" + obj.toString() + "\\"";
    }}
}}
"""

    @staticmethod
    def _python_to_java_literal(value: Any) -> str:
        """Convert a Python value to a Java literal string.

        Handles the most common LeetCode argument types:
        int, bool, str, list of int, list of str, list of list of int.
        """
        if value is None:
            return "null"
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, int):
            return str(value)
        if isinstance(value, float):
            return str(value)
        if isinstance(value, str):
            escaped = value.replace("\\", "\\\\").replace('"', '\\"')
            return f'"{escaped}"'
        if isinstance(value, list):
            if not value:
                return "new int[]{}"
            if all(isinstance(x, bool) for x in value):
                elems = ", ".join("true" if x else "false" for x in value)
                return f"new boolean[]{{{elems}}}"
            if all(isinstance(x, int) for x in value):
                elems = ", ".join(str(x) for x in value)
                return f"new int[]{{{elems}}}"
            if all(isinstance(x, str) for x in value):
                elems = ", ".join(
                    f'"{x.replace(chr(92), chr(92)*2).replace(chr(34), chr(92)+chr(34))}"'
                    for x in value
                )
                return f"new String[]{{{elems}}}"
            if all(isinstance(x, list) for x in value):
                rows = ", ".join(
                    "new int[]{" + ", ".join(str(i) for i in row) + "}" for row in value
                )
                return f"new int[][]{{{rows}}}"
        return str(value)
