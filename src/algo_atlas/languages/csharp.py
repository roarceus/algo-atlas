"""C# language support for AlgoAtlas."""

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

# Matches a public method inside class Solution.
# group(1) = method name, group(2) = raw params string.
# \S+ matches the return type as a single non-whitespace token, which covers
# int, bool, string, int[], IList<int>, IList<IList<int>>, etc.
_METHOD_PATTERN = re.compile(
    r"public\s+\S+\s+(\w+)\s*\(([^)]*)\)"
)

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
        """Run a single test case against the C# solution."""
        return TestResult(
            passed=False,
            input_args=input_args,
            expected=expected_output,
            actual=None,
            error="Not implemented",
        )
