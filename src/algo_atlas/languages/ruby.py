"""Ruby language support for AlgoAtlas."""

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


class RubyLanguage(LanguageSupport):
    """Ruby language support using ruby."""

    def info(self) -> LanguageInfo:
        return LanguageInfo(
            name="Ruby",
            slug="ruby",
            file_extension=".rb",
            solution_filename="solution.rb",
            code_fence="ruby",
            leetcode_slugs=["ruby"],
        )

    def can_run_tests(self) -> bool:
        return shutil.which("ruby") is not None

    def check_syntax(self, code: str) -> SyntaxResult:
        if not shutil.which("ruby"):
            return SyntaxResult(valid=False, error_message="ruby not found")
        if not code.strip():
            return SyntaxResult(valid=True)
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "solution.rb"
            src.write_text(code, encoding="utf-8")
            proc = subprocess.run(
                ["ruby", "-c", str(src)],
                capture_output=True,
                text=True,
            )
            if proc.returncode == 0:
                return SyntaxResult(valid=True)
            msg = (proc.stdout + proc.stderr).strip()
            return SyntaxResult(valid=False, error_message=msg)

    def extract_method_name(self, code: str) -> Optional[str]:
        return None

    def count_method_params(self, code: str) -> int:
        return 0

    def run_test_case(
        self, code: str, input_args: list, expected_output: Any
    ) -> TestResult:
        return TestResult(
            passed=False,
            input_args=input_args,
            expected=expected_output,
            actual=None,
            error="not implemented",
        )
