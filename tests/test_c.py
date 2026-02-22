"""Tests for C language support."""

import shutil
from unittest.mock import patch

from algo_atlas.languages import get_language, get_language_by_extension, list_languages
from algo_atlas.languages.base import LanguageSupport
from algo_atlas.languages.c import CLanguage


class TestCRegistry:
    """Tests for C in the language registry."""

    def test_get_language_c(self):
        lang = get_language("c")
        assert lang is not None
        assert isinstance(lang, CLanguage)

    def test_get_language_by_extension_c(self):
        lang = get_language_by_extension(".c")
        assert lang is not None
        assert isinstance(lang, CLanguage)

    def test_list_languages_includes_c(self):
        slugs = [info.slug for info in list_languages()]
        assert "c" in slugs


class TestCInfo:
    """Tests for CLanguage metadata."""

    def test_info(self):
        lang = CLanguage()
        info = lang.info()
        assert info.name == "C"
        assert info.slug == "c"
        assert info.file_extension == ".c"
        assert info.solution_filename == "solution.c"
        assert info.code_fence == "c"
        assert "c" in info.leetcode_slugs

    def test_is_language_support(self):
        assert isinstance(CLanguage(), LanguageSupport)

    def test_can_run_tests_reflects_gcc(self):
        lang = CLanguage()
        has_gcc = shutil.which("gcc") is not None
        assert lang.can_run_tests() is has_gcc


class TestCCheckSyntax:
    """Tests for CLanguage.check_syntax()."""

    def test_valid_syntax(self, valid_c_solution):
        lang = CLanguage()
        result = lang.check_syntax(valid_c_solution)
        assert result.valid is True
        assert result.error_message is None

    def test_invalid_syntax(self, invalid_c_syntax):
        lang = CLanguage()
        result = lang.check_syntax(invalid_c_syntax)
        assert result.valid is False
        assert result.error_message is not None

    def test_empty_code(self):
        lang = CLanguage()
        result = lang.check_syntax("")
        assert result.valid is True

    def test_gcc_not_found(self):
        lang = CLanguage()
        with patch("shutil.which", return_value=None):
            result = lang.check_syntax("int f() { return 0; }")
        assert result.valid is False
        assert "gcc not found" in result.error_message


class TestCExtractMethodName:
    """Tests for CLanguage.extract_method_name()."""

    def test_int_return(self):
        lang = CLanguage()
        code = "int climbStairs(int n) { return n; }"
        assert lang.extract_method_name(code) == "climbStairs"

    def test_pointer_return(self):
        lang = CLanguage()
        code = "int* twoSum(int* nums, int numsSize, int target, int* returnSize) { return NULL; }"
        assert lang.extract_method_name(code) == "twoSum"

    def test_long_long_return(self):
        lang = CLanguage()
        code = "long long maxSubArray(int* nums, int numsSize) { return 0; }"
        assert lang.extract_method_name(code) == "maxSubArray"

    def test_skips_main(self):
        lang = CLanguage()
        code = "int main() { return 0; }\nint solve(int n) { return n; }"
        assert lang.extract_method_name(code) == "solve"

    def test_no_function(self):
        lang = CLanguage()
        assert lang.extract_method_name("int x = 42;") is None


class TestCCountMethodParams:
    """Tests for CLanguage.count_method_params()."""

    def test_one_param(self):
        lang = CLanguage()
        code = "int climbStairs(int n) { return n; }"
        assert lang.count_method_params(code) == 1

    def test_two_params(self):
        lang = CLanguage()
        code = "int add(int a, int b) { return a + b; }"
        assert lang.count_method_params(code) == 2

    def test_void_param_is_zero(self):
        lang = CLanguage()
        code = "int answer(void) { return 42; }"
        assert lang.count_method_params(code) == 0

    def test_no_match(self):
        lang = CLanguage()
        assert lang.count_method_params("int x = 5;") == 0


class TestCRunTestCase:
    """Tests for CLanguage.run_test_case()."""

    def test_passing_test(self, valid_c_solution):
        lang = CLanguage()
        result = lang.run_test_case(
            code=valid_c_solution,
            input_args=[5],
            expected_output=8,
        )
        assert result.passed is True
        assert result.actual == 8

    def test_failing_test(self, wrong_c_solution):
        lang = CLanguage()
        result = lang.run_test_case(
            code=wrong_c_solution,
            input_args=[5],
            expected_output=8,
        )
        assert result.passed is False
        assert result.actual == 0

    def test_missing_method(self):
        lang = CLanguage()
        result = lang.run_test_case(
            code="int x = 1;",
            input_args=[1],
            expected_output=1,
        )
        assert result.passed is False
        assert "Could not extract method name" in result.error

    def test_runtime_error(self):
        lang = CLanguage()
        code = "int boom(int n) { abort(); return 0; }"
        result = lang.run_test_case(code=code, input_args=[1], expected_output=0)
        assert result.passed is False
        assert result.error is not None

    def test_gcc_not_found(self, valid_c_solution):
        lang = CLanguage()
        with patch("subprocess.run", side_effect=FileNotFoundError):
            result = lang.run_test_case(
                code=valid_c_solution,
                input_args=[5],
                expected_output=8,
            )
        assert result.passed is False
        assert "gcc not found" in result.error
