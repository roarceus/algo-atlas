"""Tests for C# language support."""

import shutil
from unittest.mock import patch

from algo_atlas.languages import get_language, get_language_by_extension, list_languages
from algo_atlas.languages.base import LanguageSupport
from algo_atlas.languages.csharp import CSharpLanguage


class TestCSharpRegistry:
    """Tests for C# in the language registry."""

    def test_get_language_csharp(self):
        lang = get_language("csharp")
        assert lang is not None
        assert isinstance(lang, CSharpLanguage)

    def test_get_language_by_extension_csharp(self):
        lang = get_language_by_extension(".cs")
        assert lang is not None
        assert isinstance(lang, CSharpLanguage)

    def test_list_languages_includes_csharp(self):
        slugs = [info.slug for info in list_languages()]
        assert "csharp" in slugs


class TestCSharpInfo:
    """Tests for CSharpLanguage metadata."""

    def test_info(self):
        lang = CSharpLanguage()
        info = lang.info()
        assert info.name == "C#"
        assert info.slug == "csharp"
        assert info.file_extension == ".cs"
        assert info.solution_filename == "solution.cs"
        assert info.code_fence == "csharp"
        assert "csharp" in info.leetcode_slugs

    def test_is_language_support(self):
        assert isinstance(CSharpLanguage(), LanguageSupport)

    def test_can_run_tests_reflects_dotnet(self):
        lang = CSharpLanguage()
        has_dotnet = shutil.which("dotnet") is not None
        assert lang.can_run_tests() is has_dotnet


class TestCSharpCheckSyntax:
    """Tests for CSharpLanguage.check_syntax()."""

    def test_valid_syntax(self, valid_cs_solution):
        lang = CSharpLanguage()
        result = lang.check_syntax(valid_cs_solution)
        assert result.valid is True
        assert result.error_message is None

    def test_invalid_syntax(self, invalid_cs_syntax):
        lang = CSharpLanguage()
        result = lang.check_syntax(invalid_cs_syntax)
        assert result.valid is False
        assert result.error_message is not None

    def test_empty_code(self):
        lang = CSharpLanguage()
        result = lang.check_syntax("")
        assert result.valid is True

    def test_dotnet_not_found(self):
        lang = CSharpLanguage()
        with patch("shutil.which", return_value=None):
            result = lang.check_syntax(
                "class Solution { public int F() { return 0; } }"
            )
        assert result.valid is False
        assert "dotnet not found" in result.error_message


class TestCSharpExtractMethodName:
    """Tests for CSharpLanguage.extract_method_name()."""

    def test_simple(self):
        lang = CSharpLanguage()
        code = "class Solution {\n    public int Solve(int n) { return n; }\n}"
        assert lang.extract_method_name(code) == "Solve"

    def test_ilist_return(self):
        lang = CSharpLanguage()
        code = "class Solution {\n    public IList<int> TwoSum(int[] nums, int target) { return null; }\n}"
        assert lang.extract_method_name(code) == "TwoSum"

    def test_void_method(self):
        lang = CSharpLanguage()
        code = "class Solution {\n    public void Process(string s) { }\n}"
        assert lang.extract_method_name(code) == "Process"

    def test_skips_constructor(self):
        lang = CSharpLanguage()
        code = (
            "class Solution {\n"
            "    public Solution() { }\n"
            "    public int Solve(int n) { return n; }\n"
            "}"
        )
        assert lang.extract_method_name(code) == "Solve"

    def test_no_method(self):
        lang = CSharpLanguage()
        assert lang.extract_method_name("class Foo {}") is None


class TestCSharpCountMethodParams:
    """Tests for CSharpLanguage.count_method_params()."""

    def test_one_param(self):
        lang = CSharpLanguage()
        code = "class Solution {\n    public int Solve(int n) { return n; }\n}"
        assert lang.count_method_params(code) == 1

    def test_two_params(self):
        lang = CSharpLanguage()
        code = "class Solution {\n    public int[] TwoSum(int[] nums, int target) { return null; }\n}"
        assert lang.count_method_params(code) == 2

    def test_dict_param_with_comma(self):
        lang = CSharpLanguage()
        # Dictionary<string, int> has a comma inside <> — must count as 1 param
        code = (
            "class Solution {\n"
            "    public int Count(Dictionary<string, int> map, int k) { return 0; }\n"
            "}"
        )
        assert lang.count_method_params(code) == 2

    def test_no_match(self):
        lang = CSharpLanguage()
        assert lang.count_method_params("class Foo {}") == 0


class TestCSharpRunTestCase:
    """Tests for CSharpLanguage.run_test_case()."""

    def test_passing_test(self, valid_cs_solution):
        lang = CSharpLanguage()
        result = lang.run_test_case(
            code=valid_cs_solution,
            input_args=[[2, 7, 11, 15], 9],
            expected_output=[0, 1],
        )
        assert result.passed is True
        assert result.actual == [0, 1]

    def test_failing_test(self, wrong_cs_solution):
        lang = CSharpLanguage()
        result = lang.run_test_case(
            code=wrong_cs_solution,
            input_args=[[2, 7, 11, 15], 9],
            expected_output=[0, 1],
        )
        assert result.passed is False
        assert result.actual == [0, 0]

    def test_missing_method(self):
        lang = CSharpLanguage()
        result = lang.run_test_case(
            code="class Foo {}",
            input_args=[1],
            expected_output=1,
        )
        assert result.passed is False
        assert "Could not extract method name" in result.error

    def test_runtime_error(self):
        lang = CSharpLanguage()
        code = (
            "class Solution {\n"
            "    public int Boom(int n) {\n"
            '        throw new System.Exception("kaboom");\n'
            "    }\n"
            "}"
        )
        result = lang.run_test_case(code=code, input_args=[1], expected_output=0)
        assert result.passed is False
        assert result.error is not None

    def test_dotnet_not_found(self, valid_cs_solution):
        lang = CSharpLanguage()
        with patch("subprocess.run", side_effect=FileNotFoundError):
            result = lang.run_test_case(
                code=valid_cs_solution,
                input_args=[[2, 7, 11, 15], 9],
                expected_output=[0, 1],
            )
        assert result.passed is False
        assert "dotnet not found" in result.error
