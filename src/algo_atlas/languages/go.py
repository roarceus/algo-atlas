"""Go language support for AlgoAtlas."""

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

# Same as _FUNC_PATTERN but also captures the return type as group(3).
# group(1) = function name, group(2) = params, group(3) = return type.
# The return type is everything between the closing param paren and the '{'.
_FUNC_FULL_PATTERN = re.compile(
    r"^func\s+"
    r"(\w+)\s*"           # group(1) = function name
    r"\(([^)]*)\)"        # group(2) = params
    r"\s*(.*?)\s*\{",     # group(3) = return type (may be empty for void)
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
        """Run a single test case by compiling and executing via go run.

        Writes solution.go (package main + user code) and main.go (harness)
        into a temp module directory, then runs 'go run .' and parses JSON
        stdout.
        """
        if timeout is None:
            timeout = get_settings().verifier.execution_timeout

        method_name = self.extract_method_name(code)
        if not method_name:
            return TestResult(
                passed=False,
                input_args=input_args,
                expected=expected_output,
                actual=None,
                error="Could not extract method name from Go solution",
            )

        tmp_dir = None
        try:
            tmp_dir = tempfile.mkdtemp()
            tmp_path = Path(tmp_dir)
            (tmp_path / "go.mod").write_text(_GO_MOD, encoding="utf-8")
            (tmp_path / "solution.go").write_text(
                "package main\n\n" + code, encoding="utf-8"
            )
            (tmp_path / "main.go").write_text(
                self._build_test_harness(code, method_name, input_args),
                encoding="utf-8",
            )

            run_result = subprocess.run(
                ["go", "run", "."],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(tmp_path),
            )

            stdout = run_result.stdout.strip()
            try:
                data = json.loads(stdout)
            except (json.JSONDecodeError, ValueError):
                detail = run_result.stderr.strip() or stdout or "No output"
                return TestResult(
                    passed=False,
                    input_args=input_args,
                    expected=expected_output,
                    actual=None,
                    error=f"Runtime error: {detail}",
                )

            if "error" in data:
                return TestResult(
                    passed=False,
                    input_args=input_args,
                    expected=expected_output,
                    actual=None,
                    error=data["error"],
                )

            actual = data.get("result")
            return TestResult(
                passed=actual == expected_output,
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
                error="go not found. Install Go from https://go.dev/",
            )
        except subprocess.TimeoutExpired:
            return TestResult(
                passed=False,
                input_args=input_args,
                expected=expected_output,
                actual=None,
                error="Execution timed out",
            )
        finally:
            if tmp_dir:
                shutil.rmtree(tmp_dir, ignore_errors=True)

    def _build_test_harness(
        self, code: str, method_name: str, input_args: list[Any]
    ) -> str:
        """Build main.go: imports + func main that calls the solution.

        The harness uses encoding/json to serialize any return type —
        int, []int, string, bool, float64, [][]int, etc. — without needing
        manual print helpers.
        """
        # Extract return type and param list from the function signature
        return_type = "int"
        params_str = ""
        for m in _FUNC_FULL_PATTERN.finditer(code):
            if m.group(1) == method_name:
                params_str = m.group(2).strip()
                return_type = m.group(3).strip()
                break

        go_params = self._parse_go_params(params_str)

        # Declare variables for each parameter
        decls = []
        call_args = []
        for i, param in enumerate(go_params):
            if i >= len(input_args):
                break
            name = param["name"]
            go_type = param["type"]
            lit = self._python_to_go_literal(input_args[i], go_type)
            decls.append(f"{name} := {lit}")
            call_args.append(name)

        args_str = ", ".join(call_args)
        decl_code = "\n\t".join(decls) if decls else ""

        is_void = not return_type
        if is_void:
            call_line = f"{method_name}({args_str})"
            serialize = 'fmt.Printf("{\\\"result\\\":null}\\n")'
        else:
            call_line = f"result := {method_name}({args_str})"
            serialize = (
                "out, _ := json.Marshal(result)\n"
                '\tfmt.Printf("{\\\"result\\\":%s}\\n", string(out))'
            )

        body = ""
        if decl_code:
            body += f"\t{decl_code}\n"
        body += f"\t{call_line}\n"
        body += f"\t{serialize}\n"

        return (
            "package main\n\n"
            "import (\n"
            '\t"encoding/json"\n'
            '\t"fmt"\n'
            ")\n\n"
            "func main() {\n"
            f"{body}"
            "}\n"
        )

    @staticmethod
    def _parse_go_params(params_str: str) -> list[dict]:
        """Parse a Go parameter list into [{name, type}] dicts.

        Handles simple 'name type' pairs (e.g. 'nums []int, target int').
        Params with only a name token (grouped form like 'a, b int') are
        skipped for the first element — the typed element is still captured.
        """
        params = []
        for p in params_str.split(","):
            p = p.strip()
            if not p:
                continue
            tokens = p.split()
            if len(tokens) >= 2:
                name = tokens[0]
                go_type = " ".join(tokens[1:])
                params.append({"name": name, "type": go_type})
        return params

    @staticmethod
    def _python_to_go_literal(value: Any, go_type: str) -> str:
        """Convert a Python value to a Go literal matching go_type."""
        if go_type == "bool":
            return "true" if value else "false"
        if go_type in ("int", "int32", "int64"):
            return str(int(value))
        if go_type in ("float64", "float32"):
            return repr(float(value))
        if go_type == "string":
            escaped = str(value).replace("\\", "\\\\").replace('"', '\\"')
            return f'"{escaped}"'
        if go_type.startswith("[]"):
            elem_type = go_type[2:]
            if isinstance(value, list):
                elements = ", ".join(
                    GoLanguage._python_to_go_literal(v, elem_type) for v in value
                )
                return f"{go_type}{{{elements}}}"
            return f"{go_type}{{}}"
        # Fallback for unrecognised types (e.g. *TreeNode)
        return str(value)
