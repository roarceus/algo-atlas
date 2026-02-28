"""C# language support for AlgoAtlas."""

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

# Matches a public method inside class Solution.
# group(1) = method name, group(2) = raw params string.
# \S+ matches the return type as a single non-whitespace token, which covers
# int, bool, string, int[], IList<int>, IList<IList<int>>, etc.
_METHOD_PATTERN = re.compile(
    r"public\s+\S+\s+(\w+)\s*\(([^)]*)\)"
)

# Same as _METHOD_PATTERN but also captures the return type as group(1).
# group(1) = return type, group(2) = method name, group(3) = params.
_METHOD_FULL_PATTERN = re.compile(
    r"public\s+(\S+)\s+(\w+)\s*\(([^)]*)\)"
)

# Minimal .csproj for the test harness (executable — needs a Main).
_CS_CSPROJ_EXE = """\
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <OutputType>Exe</OutputType>
    <TargetFramework>net6.0</TargetFramework>
    <AssemblyName>solution</AssemblyName>
    <Nullable>enable</Nullable>
  </PropertyGroup>
</Project>
"""

# Common using directives prepended to user code.
_CS_PREAMBLE = """\
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
"""

# Minimal .csproj for syntax checking (library — no Main required).
_CS_CSPROJ_LIB = """\
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <OutputType>Library</OutputType>
    <TargetFramework>net6.0</TargetFramework>
    <Nullable>enable</Nullable>
  </PropertyGroup>
</Project>
"""


class CSharpLanguage(LanguageSupport):
    """C# language support using the dotnet toolchain."""

    def info(self) -> LanguageInfo:
        return LanguageInfo(
            name="C#",
            slug="csharp",
            file_extension=".cs",
            solution_filename="solution.cs",
            code_fence="csharp",
            leetcode_slugs=["csharp"],
        )

    def can_run_tests(self) -> bool:
        """Check if the dotnet toolchain is available."""
        return shutil.which("dotnet") is not None

    def check_syntax(self, code: str) -> SyntaxResult:
        """Check C# syntax by compiling as a library with dotnet build.

        Writes a minimal .csproj (OutputType=Library) and solution.cs
        (preamble + user code) into a temp directory, then runs
        'dotnet build' to catch syntax and type errors without needing
        a Main entry point.
        """
        if not code.strip():
            return SyntaxResult(valid=True)

        if not self.can_run_tests():
            return SyntaxResult(
                valid=False,
                error_message=(
                    "dotnet not found. Install .NET from https://dotnet.microsoft.com/"
                ),
            )

        tmp_dir = None
        try:
            tmp_dir = tempfile.mkdtemp()
            tmp_path = Path(tmp_dir)
            (tmp_path / "solution.csproj").write_text(_CS_CSPROJ_LIB, encoding="utf-8")
            (tmp_path / "solution.cs").write_text(
                _CS_PREAMBLE + code, encoding="utf-8"
            )

            result = subprocess.run(
                ["dotnet", "build", "--nologo", "-v", "quiet"],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=str(tmp_path),
            )

            if result.returncode == 0:
                return SyntaxResult(valid=True)

            # dotnet build error format:
            # solution.cs(5,15): error CS0103: message [solution.csproj]
            stderr = (result.stderr + result.stdout).strip()
            error_msg = stderr
            error_line = None
            preamble_lines = _CS_PREAMBLE.count("\n")

            for line in stderr.split("\n"):
                if ": error CS" in line and "solution.cs(" in line:
                    try:
                        loc = line.split("solution.cs(", 1)[1]
                        raw_line = int(loc.split(",")[0])
                        error_line = max(1, raw_line - preamble_lines)
                    except (ValueError, IndexError):
                        pass
                    msg_start = line.find("error CS")
                    if msg_start >= 0:
                        msg = line[msg_start:].split("[")[0].strip()
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
                error_message=(
                    "dotnet not found. Install .NET from https://dotnet.microsoft.com/"
                ),
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
        """Extract the main method name from a LeetCode C# solution.

        Looks for the first public method whose name is not 'Solution'
        (the constructor). Uses the same simple pattern as Java since C#
        LeetCode return types never contain whitespace.
        """
        for m in _METHOD_PATTERN.finditer(code):
            name = m.group(1)
            if name != "Solution":
                return name
        return None

    def count_method_params(self, code: str) -> int:
        """Count parameters in the C# solution method.

        Uses angle-bracket-aware comma splitting so generics like
        Dictionary<string, int> count as one parameter.
        """
        for m in _METHOD_PATTERN.finditer(code):
            if m.group(1) != "Solution":
                params_str = m.group(2).strip()
                if not params_str:
                    return 0
                parts = self._split_cs_params(params_str)
                return len(parts)
        return 0

    @staticmethod
    def _split_cs_params(params_str: str) -> list[str]:
        """Split a C# param list by top-level commas only.

        Commas inside angle brackets (e.g. Dictionary<string, int>) are
        ignored so they count as one parameter.
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
        """Run a single test case by compiling and executing via dotnet.

        Writes Solution.cs (preamble + user code) and Program.cs (harness)
        into a temp project directory, compiles with 'dotnet build', then
        runs the output DLL with 'dotnet' and parses JSON stdout.
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
                error="Could not extract method name from C# solution",
            )

        tmp_dir = None
        try:
            tmp_dir = tempfile.mkdtemp()
            tmp_path = Path(tmp_dir)
            out_path = tmp_path / "out"
            out_path.mkdir()

            (tmp_path / "solution.csproj").write_text(
                _CS_CSPROJ_EXE, encoding="utf-8"
            )
            (tmp_path / "Solution.cs").write_text(
                _CS_PREAMBLE + code, encoding="utf-8"
            )
            (tmp_path / "Program.cs").write_text(
                self._build_test_harness(code, method_name, input_args),
                encoding="utf-8",
            )

            compile_result = subprocess.run(
                ["dotnet", "build", "--nologo", "-v", "quiet", "-o", str(out_path)],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=str(tmp_path),
            )
            if compile_result.returncode != 0:
                err = (compile_result.stderr + compile_result.stdout).strip()
                return TestResult(
                    passed=False,
                    input_args=input_args,
                    expected=expected_output,
                    actual=None,
                    error=f"Compilation error: {err}",
                )

            run_result = subprocess.run(
                ["dotnet", str(out_path / "solution.dll")],
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
                error=(
                    "dotnet not found. Install .NET from https://dotnet.microsoft.com/"
                ),
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
        """Build Program.cs: using directives + class Program with Main.

        Uses System.Text.Json.JsonSerializer to serialize any return type
        without manual helpers. Variables are declared with 'var' so C#
        infers the type — int[] satisfies IList<int>, etc.
        """
        return_type = "int"
        params_str = ""
        for m in _METHOD_FULL_PATTERN.finditer(code):
            if m.group(2) == method_name:
                return_type = m.group(1).strip()
                params_str = m.group(3).strip()
                break

        cs_params = self._parse_cs_params(params_str)

        decls = []
        call_args = []
        for i, param in enumerate(cs_params):
            if i >= len(input_args):
                break
            name = param["name"]
            cs_type = param["type"]
            lit = self._python_to_cs_literal(input_args[i], cs_type)
            decls.append(f"        var {name} = {lit};")
            call_args.append(name)

        args_str = ", ".join(call_args)
        decl_code = "\n".join(decls)

        is_void = return_type == "void"
        if is_void:
            call_line = f"        sol.{method_name}({args_str});"
            output_line = '        Console.WriteLine("{\\"result\\":null}");'
        else:
            call_line = f"        var result = sol.{method_name}({args_str});"
            output_line = (
                '        Console.WriteLine("{\\"result\\":" + '
                "JsonSerializer.Serialize(result) + \"}\");"
            )

        body = ""
        if decl_code:
            body += decl_code + "\n"
        body += call_line + "\n"
        body += output_line + "\n"

        return (
            "using System;\n"
            "using System.Text.Json;\n\n"
            "class Program {\n"
            "    static void Main() {\n"
            "        var sol = new Solution();\n"
            + body
            + "    }\n"
            "}\n"
        )

    @staticmethod
    def _parse_cs_params(params_str: str) -> list[dict]:
        """Parse a C# param list into [{name, type}] dicts.

        Uses rsplit to separate the trailing name from the type, which
        handles multi-word types like 'int[]' and 'IList<int>' correctly.
        """
        params = []
        for p in CSharpLanguage._split_cs_params(params_str):
            p = p.strip()
            if not p:
                continue
            parts = p.rsplit(maxsplit=1)
            if len(parts) == 2:
                params.append({"name": parts[1].strip(), "type": parts[0].strip()})
        return params

    @staticmethod
    def _python_to_cs_literal(value: Any, cs_type: str) -> str:
        """Convert a Python value to a C# literal.

        Uses the Python value type rather than the declared C# type so that
        int[] literals work for both int[] and IList<int> parameters.
        """
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, int):
            return str(value)
        if isinstance(value, float):
            return repr(value)
        if isinstance(value, str):
            escaped = value.replace("\\", "\\\\").replace('"', '\\"')
            return f'"{escaped}"'
        if isinstance(value, list):
            if not value:
                return "new int[]{}"
            if all(isinstance(x, bool) for x in value):
                inner = ", ".join("true" if x else "false" for x in value)
                return "new bool[]{" + inner + "}"
            if all(isinstance(x, int) for x in value):
                inner = ", ".join(str(x) for x in value)
                return "new int[]{" + inner + "}"
            if all(isinstance(x, str) for x in value):
                inner = ", ".join(f'"{x}"' for x in value)
                return "new string[]{" + inner + "}"
            if all(isinstance(x, list) for x in value):
                rows = [
                    "new int[]{" + ", ".join(str(int(x)) for x in row) + "}"
                    for row in value
                ]
                return "new int[][]{" + ", ".join(rows) + "}"
        return str(value)
