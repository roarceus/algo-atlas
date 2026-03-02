"""C language support for AlgoAtlas."""

import json
import re
import shutil
import subprocess
import sys
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

# C keywords and type names that must not be mistaken for a function name
_C_KEYWORDS = frozenset(
    {
        "if",
        "else",
        "for",
        "while",
        "do",
        "switch",
        "case",
        "break",
        "continue",
        "return",
        "goto",
        "sizeof",
        "typedef",
        "struct",
        "union",
        "enum",
        "const",
        "static",
        "extern",
        "volatile",
        "register",
        "int",
        "long",
        "short",
        "char",
        "float",
        "double",
        "void",
        "bool",
        "unsigned",
        "signed",
        "main",
    }
)

# Matches a top-level C function definition (line must start with a word char,
# not a preprocessor directive).
# Return type may be multi-word (e.g. "long long") or include a pointer
# (e.g. "int*", "struct ListNode*") — the non-greedy [\w\s*]*? handles all cases.
# group(1) = function name, group(2) = raw params string.
# Requiring [^;{]*\{ at the end excludes forward declarations (which end with ;).
_FUNC_PATTERN = re.compile(
    r"^(?!#)"  # line start, not a preprocessor directive
    r"(?:[\w*][\w\s*]*?\s)"  # return type (non-greedy, ends with a space)
    r"(\w+)\s*"  # function name
    r"\(([^)]*)\)"  # params
    r"[^;{]*\{",  # up to opening brace (definition, not prototype)
    re.MULTILINE,
)

# Same as _FUNC_PATTERN but also captures the return type as group(1).
# group(1) = return type, group(2) = function name, group(3) = params.
_FUNC_FULL_PATTERN = re.compile(
    r"^(?!#)"
    r"([\w*][\w\s*]*?)\s+"  # return type (captured, non-greedy)
    r"(\w+)\s*"  # function name
    r"\(([^)]*)\)"  # params
    r"[^;{]*\{",  # up to opening brace
    re.MULTILINE,
)

# C helpers injected into the test harness for JSON-safe output.
_C_PRINT_HELPERS = r"""
static void _print_int_array(int* arr, int size) {
    printf("[");
    for (int i = 0; i < size; i++) {
        if (i) printf(",");
        printf("%d", arr[i]);
    }
    printf("]");
}
static void _print_str(const char* s) {
    printf("\"");
    for (; *s; s++) {
        if (*s == '"') printf("\\\"");
        else if (*s == '\\') printf("\\\\");
        else printf("%c", *s);
    }
    printf("\"");
}
"""

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
                        rest = parts[colon_idx + 1 :].strip()
                        col_end = rest.find(":")
                        if col_end > 0:
                            rest = rest[col_end + 1 :].strip()
                        if rest.startswith("error:"):
                            rest = rest[len("error:") :].strip()
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
        """Extract the main function name from a LeetCode C solution.

        Looks for the first top-level function definition whose name is
        not a C keyword or type name (e.g. not 'main', 'int', 'long').
        """
        for m in _FUNC_PATTERN.finditer(code):
            name = m.group(1)
            if name not in _C_KEYWORDS:
                return name
        return None

    def count_method_params(self, code: str) -> int:
        """Count parameters in the C solution function.

        C has no template types with commas, so a plain comma split is correct.
        Treats 'void' as zero params (e.g. 'int answer(void)').
        """
        for m in _FUNC_PATTERN.finditer(code):
            name = m.group(1)
            if name not in _C_KEYWORDS:
                params_str = m.group(2).strip()
                if not params_str or params_str == "void":
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
        """Run a single test case by compiling and executing via gcc.

        Builds a single .c file (preamble + helpers + user code + main),
        compiles with gcc -std=c11, runs the binary, and parses JSON stdout.
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
                error="Could not extract method name from C solution",
            )

        tmp_dir = None
        try:
            tmp_dir = tempfile.mkdtemp()
            src_path = Path(tmp_dir) / "solution.c"
            src_path.write_text(
                self._build_test_harness(code, method_name, input_args),
                encoding="utf-8",
            )

            bin_name = "solution.exe" if sys.platform == "win32" else "solution"
            bin_path = Path(tmp_dir) / bin_name

            compile_result = subprocess.run(
                ["gcc", "-std=c11", "-O0", "-o", str(bin_path), str(src_path)],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if compile_result.returncode != 0:
                return TestResult(
                    passed=False,
                    input_args=input_args,
                    expected=expected_output,
                    actual=None,
                    error=f"Compilation error: {compile_result.stderr.strip()}",
                )

            run_result = subprocess.run(
                [str(bin_path)],
                capture_output=True,
                text=True,
                timeout=timeout,
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
                error="gcc not found. Install GCC from https://gcc.gnu.org/",
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
        """Build a complete .c file: preamble + helpers + solution + main.

        Handles the LeetCode C param convention where:
        - int* array params are followed by int fooSize params (auto-derived)
        - int* returnSize is an output param passed as &returnSize
        """
        # Find return type and params from the function signature
        return_type = "int"
        params_str = ""
        for m in _FUNC_FULL_PATTERN.finditer(code):
            if m.group(2) == method_name:
                return_type = m.group(1).strip()
                params_str = m.group(3).strip()
                break

        c_params = self._parse_c_params(params_str)

        # Identify array params and their corresponding size params
        array_param_names = {
            p["name"] for p in c_params if p["is_ptr"] and p["name"] != "returnSize"
        }
        # Maps "numsSize" -> "nums" for auto-size injection
        size_param_of = {
            p["name"]: p["name"][:-4]
            for p in c_params
            if not p["is_ptr"]
            and p["name"].endswith("Size")
            and p["name"][:-4] in array_param_names
        }

        # User params are those not auto-derived (not size params, not returnSize)
        user_params = [
            p["name"]
            for p in c_params
            if p["name"] != "returnSize" and p["name"] not in size_param_of
        ]

        # Generate variable declarations
        decls = []
        for i, pname in enumerate(user_params):
            if i >= len(input_args):
                break
            val = input_args[i]
            if isinstance(val, list):
                inner = ", ".join(self._python_to_c_scalar(x) for x in val)
                decls.append(f"int {pname}[] = {{{inner}}};")
                decls.append(f"int {pname}Size = {len(val)};")
            elif isinstance(val, bool):
                decls.append(f"int {pname} = {1 if val else 0};")
            elif isinstance(val, int):
                decls.append(f"int {pname} = {val};")
            elif isinstance(val, str):
                escaped = val.replace("\\", "\\\\").replace('"', '\\"')
                decls.append(f'char* {pname} = "{escaped}";')

        is_ptr_return = "*" in return_type and "char" not in return_type
        if is_ptr_return:
            decls.append("int returnSize = 0;")

        # Build the call argument list
        call_args = []
        for p in c_params:
            name = p["name"]
            if name == "returnSize":
                call_args.append("&returnSize")
            elif name in size_param_of:
                call_args.append(f"{size_param_of[name]}Size")
            else:
                call_args.append(name)

        # Choose result type and serialization snippet
        is_str_return = "char" in return_type and "*" in return_type
        is_bool_return = return_type.strip() == "bool"
        is_void_return = return_type.strip() == "void"

        if is_ptr_return:
            result_decl = f"{return_type.rstrip()}* result"
            if not return_type.endswith("*"):
                result_decl = f"{return_type}* result"
            serialize = (
                '    printf("{\\"result\\":");\n'
                "    _print_int_array(result, returnSize);\n"
                '    printf("}\\n");'
            )
        elif is_str_return:
            result_decl = "char* result"
            serialize = (
                '    printf("{\\"result\\":");\n'
                "    _print_str(result);\n"
                '    printf("}\\n");'
            )
        elif is_bool_return:
            result_decl = "bool result"
            serialize = '    printf("{\\"result\\":%s}\\n", result ? "true" : "false");'
        elif is_void_return:
            result_decl = None
            serialize = '    printf("{\\"result\\":null}\\n");'
        elif "double" in return_type or "float" in return_type:
            result_decl = f"{return_type} result"
            serialize = '    printf("{\\"result\\":%g}\\n", result);'
        else:
            result_decl = f"{return_type} result"
            serialize = '    printf("{\\"result\\":%d}\\n", result);'

        args_str = ", ".join(call_args)
        decl_code = "\n    ".join(decls)
        if is_void_return:
            call_line = f"    {method_name}({args_str});"
        else:
            call_line = f"    {result_decl} = {method_name}({args_str});"

        main_fn = (
            "int main() {\n"
            f"    {decl_code}\n"
            f"{call_line}\n"
            f"{serialize}\n"
            "    return 0;\n"
            "}\n"
        )
        return _C_PREAMBLE + _C_PRINT_HELPERS + code + "\n\n" + main_fn

    @staticmethod
    def _parse_c_params(params_str: str) -> list[dict]:
        """Parse a C parameter list into a list of {name, is_ptr} dicts."""
        params = []
        for p in params_str.split(","):
            p = p.strip()
            if not p or p == "void":
                continue
            # Name is the last token; strip leading * to get bare name
            tokens = p.split()
            raw_name = tokens[-1].lstrip("*")
            is_ptr = "*" in p
            params.append({"name": raw_name, "is_ptr": is_ptr})
        return params

    @staticmethod
    def _python_to_c_scalar(value: Any) -> str:
        """Convert a Python scalar to a C literal for array initializers."""
        if isinstance(value, bool):
            return "1" if value else "0"
        if isinstance(value, int):
            return str(value)
        if isinstance(value, float):
            return repr(value)
        if isinstance(value, str):
            escaped = value.replace("\\", "\\\\").replace('"', '\\"')
            return f'"{escaped}"'
        return str(value)
