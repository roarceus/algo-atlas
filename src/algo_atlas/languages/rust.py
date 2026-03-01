"""Rust language support for AlgoAtlas."""

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

# Method names inside impl Solution that are not the LeetCode solution.
_RUST_KEYWORDS = frozenset({"new", "default", "clone", "fmt", "from", "into"})

# Matches a `pub fn` inside impl Solution.
# group(1) = method name, group(2) = raw params string.
# [^)]* works for LeetCode params because Rust generic types use <> not ().
_METHOD_PATTERN = re.compile(
    r"\bpub\s+fn\s+"
    r"(\w+)\s*"  # group(1) = method name
    r"\(([^)]*)\)",  # group(2) = raw params string
    re.MULTILINE,
)

# Same as _METHOD_PATTERN but also captures the return type as group(3).
# group(1) = method name, group(2) = params, group(3) = return type (optional).
_METHOD_FULL_PATTERN = re.compile(
    r"\bpub\s+fn\s+"
    r"(\w+)\s*"  # group(1) = method name
    r"\(([^)]*)\)"  # group(2) = params
    r"(?:\s*->\s*([^{]+?))?"  # group(3) = return type (optional, before {)
    r"\s*\{",
    re.MULTILINE,
)

# Prepended to user code for syntax checking.
# `struct Solution;` is required for `impl Solution { ... }` to compile.
# `#![allow(dead_code)]` suppresses warnings about unused methods.
_RUST_PREAMBLE = "#![allow(dead_code)]\nstruct Solution;\n\n"

# Rust JSON helper functions injected into the test harness.
# Using a char-by-char approach avoids complex escape sequences in _json_str.
_RUST_JSON_HELPERS = r"""
fn _json_str(s: &str) -> String {
    let mut out = String::from("\"");
    for c in s.chars() {
        match c {
            '"' => out.push_str("\\\""),
            '\\' => out.push_str("\\\\"),
            _ => out.push(c),
        }
    }
    out.push('"');
    out
}
fn _json_vec_i32(v: &[i32]) -> String {
    format!("[{}]", v.iter().map(|x| x.to_string()).collect::<Vec<_>>().join(","))
}
fn _json_vec_i64(v: &[i64]) -> String {
    format!("[{}]", v.iter().map(|x| x.to_string()).collect::<Vec<_>>().join(","))
}
fn _json_vec_str(v: &[String]) -> String {
    let parts: Vec<String> = v.iter().map(|s| _json_str(s)).collect();
    format!("[{}]", parts.join(","))
}
fn _json_vec_vec_i32(v: &[Vec<i32>]) -> String {
    let parts: Vec<String> = v.iter().map(|row| _json_vec_i32(row)).collect();
    format!("[{}]", parts.join(","))
}
"""


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
                    "--edition",
                    "2021",
                    "--crate-type",
                    "lib",
                    "--emit=metadata",
                    "-o",
                    str(meta_path),
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
                    p
                    for p in parts
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
        """Run a single test case by compiling and executing via rustc.

        Writes a single solution.rs (preamble + user code + JSON helpers +
        main), compiles with 'rustc --edition 2021', runs the binary, and
        parses JSON stdout.
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
                error="Could not extract method name from Rust solution",
            )

        tmp_dir = None
        try:
            tmp_dir = tempfile.mkdtemp()
            tmp_path = Path(tmp_dir)
            src_path = tmp_path / "solution.rs"
            src_path.write_text(
                self._build_test_harness(code, method_name, input_args),
                encoding="utf-8",
            )

            bin_name = "solution.exe" if sys.platform == "win32" else "solution"
            bin_path = tmp_path / bin_name

            compile_result = subprocess.run(
                [
                    "rustc",
                    "--edition",
                    "2021",
                    "-o",
                    str(bin_path),
                    str(src_path),
                ],
                capture_output=True,
                text=True,
                timeout=60,
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
                error="rustc not found. Install Rust from https://rustup.rs/",
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
        """Build a complete solution.rs: preamble + user code + helpers + main.

        Detects the return type from the function signature and emits the
        appropriate println! for JSON output.
        """
        return_type = "i32"
        params_str = ""
        for m in _METHOD_FULL_PATTERN.finditer(code):
            if m.group(1) == method_name:
                params_str = m.group(2).strip()
                return_type = (m.group(3) or "").strip()
                break

        rust_params = self._parse_rust_params(params_str)

        decls = []
        call_args = []
        for i, param in enumerate(rust_params):
            if i >= len(input_args):
                break
            name = param["name"]
            rust_type = param["type"]
            lit = self._python_to_rust_literal(input_args[i], rust_type)
            decls.append(f"    let {name}: {rust_type} = {lit};")
            call_args.append(name)

        args_str = ", ".join(call_args)
        decl_code = "\n".join(decls)

        is_void = not return_type
        if is_void:
            call_line = f"    Solution::{method_name}({args_str});"
            serialize = '    println!("{{\\"result\\":null}}");'
        else:
            call_line = f"    let result = Solution::{method_name}({args_str});"
            serialize = self._get_serialize_snippet(return_type)

        body = ""
        if decl_code:
            body += decl_code + "\n"
        body += call_line + "\n"
        body += serialize + "\n"

        return (
            "#![allow(dead_code, unused_variables, unused_mut)]\n"
            "struct Solution;\n\n" + code + "\n" + _RUST_JSON_HELPERS + "\n"
            "fn main() {\n" + body + "}\n"
        )

    @staticmethod
    def _get_serialize_snippet(return_type: str) -> str:
        """Return the println! statement for the given Rust return type."""
        rt = return_type.strip()
        if rt in ("i32", "i64", "u32", "u64", "usize", "f64", "f32", "bool"):
            return '    println!("{{\\"result\\":{}}}", result);'
        if rt == "String":
            return '    println!("{{\\"result\\":{}}}", _json_str(&result));'
        if rt in ("Vec<i32>", "Vec<u32>"):
            return '    println!("{{\\"result\\":{}}}", _json_vec_i32(&result));'
        if rt in ("Vec<i64>", "Vec<u64>"):
            return '    println!("{{\\"result\\":{}}}", _json_vec_i64(&result));'
        if rt == "Vec<String>":
            return '    println!("{{\\"result\\":{}}}", _json_vec_str(&result));'
        if rt == "Vec<Vec<i32>>":
            return '    println!("{{\\"result\\":{}}}", _json_vec_vec_i32(&result));'
        # Fallback: Rust Debug format (not JSON-safe but better than nothing)
        return '    println!("{{\\"result\\":{:?}}}", result);'

    @staticmethod
    def _parse_rust_params(params_str: str) -> list[dict]:
        """Parse a Rust param list into [{name, type}] dicts.

        Skips &self / &mut self receiver params. Strips leading & from
        reference params so the variable name is usable in the harness.
        """
        params = []
        for p in RustLanguage._split_rust_params(params_str):
            p = p.strip()
            stripped = p.lstrip("&").lstrip("mut").strip()
            if stripped == "self" or stripped.startswith("self "):
                continue
            colon_idx = p.find(":")
            if colon_idx < 0:
                continue
            name = p[:colon_idx].strip().lstrip("&").lstrip("mut").strip()
            rust_type = p[colon_idx + 1 :].strip().lstrip("&").lstrip("mut").strip()
            if name:
                params.append({"name": name, "type": rust_type})
        return params

    @staticmethod
    def _python_to_rust_literal(value: Any, rust_type: str) -> str:
        """Convert a Python value to a Rust literal matching rust_type."""
        rt = rust_type.strip()
        if rt == "bool":
            return "true" if value else "false"
        if rt in ("i32", "u32", "usize", "u8", "i8", "u16", "i16"):
            return str(int(value))
        if rt in ("i64", "u64"):
            return f"{int(value)}i64"
        if rt in ("f64",):
            return repr(float(value))
        if rt in ("f32",):
            return f"{float(value)}f32"
        if rt == "String":
            escaped = str(value).replace("\\", "\\\\").replace('"', '\\"')
            return f'String::from("{escaped}")'
        if rt in ("Vec<i32>", "Vec<u32>"):
            if isinstance(value, list):
                return "vec![{}]".format(", ".join(str(int(x)) for x in value))
            return "vec![]"
        if rt in ("Vec<i64>", "Vec<u64>"):
            if isinstance(value, list):
                return "vec![{}]".format(", ".join(f"{int(x)}i64" for x in value))
            return "vec![]"
        if rt == "Vec<f64>":
            if isinstance(value, list):
                return "vec![{}]".format(", ".join(repr(float(x)) for x in value))
            return "vec![]"
        if rt == "Vec<String>":
            if isinstance(value, list):
                parts = [
                    'String::from("{}")'.format(
                        str(x).replace("\\", "\\\\").replace('"', '\\"')
                    )
                    for x in value
                ]
                return "vec![{}]".format(", ".join(parts))
            return "vec![]"
        if rt == "Vec<Vec<i32>>":
            if isinstance(value, list):
                rows = [
                    "vec![{}]".format(", ".join(str(int(x)) for x in row))
                    for row in value
                ]
                return "vec![{}]".format(", ".join(rows))
            return "vec![]"
        return str(value)
