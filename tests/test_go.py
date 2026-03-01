"""Tests for Go language support."""

import shutil
from unittest.mock import patch

from algo_atlas.languages import get_language, get_language_by_extension, list_languages
from algo_atlas.languages.base import LanguageSupport
from algo_atlas.languages.go import GoLanguage


class TestGoRegistry:
    """Tests for Go in the language registry."""

    def test_get_language_go(self):
        lang = get_language("go")
        assert lang is not None
        assert isinstance(lang, GoLanguage)

    def test_get_language_by_extension_go(self):
        lang = get_language_by_extension(".go")
        assert lang is not None
        assert isinstance(lang, GoLanguage)

    def test_list_languages_includes_go(self):
        slugs = [info.slug for info in list_languages()]
        assert "go" in slugs


class TestGoInfo:
    """Tests for GoLanguage metadata."""

    def test_info(self):
        lang = GoLanguage()
        info = lang.info()
        assert info.name == "Go"
        assert info.slug == "go"
        assert info.file_extension == ".go"
        assert info.solution_filename == "solution.go"
        assert info.code_fence == "go"
        assert "golang" in info.leetcode_slugs

    def test_is_language_support(self):
        assert isinstance(GoLanguage(), LanguageSupport)

    def test_can_run_tests_reflects_go(self):
        lang = GoLanguage()
        has_go = shutil.which("go") is not None
        assert lang.can_run_tests() is has_go


class TestGoCheckSyntax:
    """Tests for GoLanguage.check_syntax()."""

    def test_valid_syntax(self, valid_go_solution):
        lang = GoLanguage()
        result = lang.check_syntax(valid_go_solution)
        assert result.valid is True
        assert result.error_message is None

    def test_invalid_syntax(self, invalid_go_syntax):
        lang = GoLanguage()
        result = lang.check_syntax(invalid_go_syntax)
        assert result.valid is False
        assert result.error_message is not None

    def test_empty_code(self):
        lang = GoLanguage()
        result = lang.check_syntax("")
        assert result.valid is True

    def test_go_not_found(self):
        lang = GoLanguage()
        with patch("shutil.which", return_value=None):
            result = lang.check_syntax("func f() int { return 0 }")
        assert result.valid is False
        assert "go not found" in result.error_message


class TestGoExtractMethodName:
    """Tests for GoLanguage.extract_method_name()."""

    def test_int_return(self):
        lang = GoLanguage()
        code = "func climbStairs(n int) int { return n }"
        assert lang.extract_method_name(code) == "climbStairs"

    def test_slice_return(self):
        lang = GoLanguage()
        code = "func twoSum(nums []int, target int) []int { return nil }"
        assert lang.extract_method_name(code) == "twoSum"

    def test_bool_return(self):
        lang = GoLanguage()
        code = "func isPalindrome(s string) bool { return true }"
        assert lang.extract_method_name(code) == "isPalindrome"

    def test_skips_main(self):
        lang = GoLanguage()
        code = "func main() {}\nfunc solve(n int) int { return n }"
        assert lang.extract_method_name(code) == "solve"

    def test_no_function(self):
        lang = GoLanguage()
        assert lang.extract_method_name("var x = 42") is None


class TestGoCountMethodParams:
    """Tests for GoLanguage.count_method_params()."""

    def test_one_param(self):
        lang = GoLanguage()
        code = "func climbStairs(n int) int { return n }"
        assert lang.count_method_params(code) == 1

    def test_two_params(self):
        lang = GoLanguage()
        code = "func twoSum(nums []int, target int) []int { return nil }"
        assert lang.count_method_params(code) == 2

    def test_zero_params(self):
        lang = GoLanguage()
        code = "func answer() int { return 42 }"
        assert lang.count_method_params(code) == 0

    def test_no_match(self):
        lang = GoLanguage()
        assert lang.count_method_params("var x = 5") == 0


class TestGoRunTestCase:
    """Tests for GoLanguage.run_test_case()."""

    def test_passing_test(self, valid_go_solution):
        lang = GoLanguage()
        result = lang.run_test_case(
            code=valid_go_solution,
            input_args=[5],
            expected_output=8,
        )
        assert result.passed is True
        assert result.actual == 8

    def test_failing_test(self, wrong_go_solution):
        lang = GoLanguage()
        result = lang.run_test_case(
            code=wrong_go_solution,
            input_args=[5],
            expected_output=8,
        )
        assert result.passed is False
        assert result.actual == 0

    def test_missing_method(self):
        lang = GoLanguage()
        result = lang.run_test_case(
            code="var x = 1",
            input_args=[1],
            expected_output=1,
        )
        assert result.passed is False
        assert "Could not extract method name" in result.error

    def test_runtime_error(self):
        lang = GoLanguage()
        code = 'func boom(n int) int { panic("kaboom") }'
        result = lang.run_test_case(code=code, input_args=[1], expected_output=0)
        assert result.passed is False
        assert result.error is not None

    def test_go_not_found(self, valid_go_solution):
        lang = GoLanguage()
        with patch("subprocess.run", side_effect=FileNotFoundError):
            result = lang.run_test_case(
                code=valid_go_solution,
                input_args=[5],
                expected_output=8,
            )
        assert result.passed is False
        assert "go not found" in result.error
