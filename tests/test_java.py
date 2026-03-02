"""Tests for Java language support."""

import shutil
from unittest.mock import patch

from algo_atlas.languages import get_language, get_language_by_extension, list_languages
from algo_atlas.languages.base import LanguageSupport
from algo_atlas.languages.java import JavaLanguage


class TestJavaRegistry:
    """Tests for Java in the language registry."""

    def test_get_language_java(self):
        lang = get_language("java")
        assert lang is not None
        assert isinstance(lang, JavaLanguage)

    def test_get_language_by_extension_java(self):
        lang = get_language_by_extension(".java")
        assert lang is not None
        assert isinstance(lang, JavaLanguage)

    def test_list_languages_includes_java(self):
        slugs = [info.slug for info in list_languages()]
        assert "java" in slugs


class TestJavaInfo:
    """Tests for JavaLanguage metadata."""

    def test_info(self):
        lang = JavaLanguage()
        info = lang.info()
        assert info.name == "Java"
        assert info.slug == "java"
        assert info.file_extension == ".java"
        assert info.solution_filename == "Solution.java"
        assert info.code_fence == "java"
        assert "java" in info.leetcode_slugs

    def test_is_language_support(self):
        assert isinstance(JavaLanguage(), LanguageSupport)

    def test_can_run_tests_reflects_jdk(self):
        lang = JavaLanguage()
        has_jdk = shutil.which("javac") is not None and shutil.which("java") is not None
        assert lang.can_run_tests() is has_jdk


class TestJavaCheckSyntax:
    """Tests for JavaLanguage.check_syntax()."""

    def test_valid_syntax(self, valid_java_solution):
        lang = JavaLanguage()
        result = lang.check_syntax(valid_java_solution)
        assert result.valid is True
        assert result.error_message is None

    def test_invalid_syntax(self, invalid_java_syntax):
        lang = JavaLanguage()
        result = lang.check_syntax(invalid_java_syntax)
        assert result.valid is False
        assert result.error_message is not None

    def test_empty_code(self):
        lang = JavaLanguage()
        result = lang.check_syntax("")
        assert result.valid is True

    def test_jdk_not_found(self):
        lang = JavaLanguage()
        with patch("shutil.which", return_value=None):
            result = lang.check_syntax("class Solution {}")
        assert result.valid is False
        assert "javac not found" in result.error_message


class TestJavaExtractMethodName:
    """Tests for JavaLanguage.extract_method_name()."""

    def test_int_array_return(self):
        lang = JavaLanguage()
        code = "class Solution { public int[] twoSum(int[] nums, int target) { return null; } }"
        assert lang.extract_method_name(code) == "twoSum"

    def test_boolean_return(self):
        lang = JavaLanguage()
        code = "class Solution { public boolean isPalindrome(int x) { return true; } }"
        assert lang.extract_method_name(code) == "isPalindrome"

    def test_generic_return_type(self):
        lang = JavaLanguage()
        code = "class Solution { public List<Integer> solve(int n) { return null; } }"
        assert lang.extract_method_name(code) == "solve"

    def test_skips_constructor(self):
        lang = JavaLanguage()
        code = "class Solution { public Solution() {} public int[] twoSum(int[] nums, int t) { return null; } }"
        assert lang.extract_method_name(code) == "twoSum"

    def test_no_method(self):
        lang = JavaLanguage()
        assert lang.extract_method_name("class Solution {}") is None


class TestJavaCountMethodParams:
    """Tests for JavaLanguage.count_method_params()."""

    def test_two_params(self):
        lang = JavaLanguage()
        code = "class Solution { public int[] twoSum(int[] nums, int target) { return null; } }"
        assert lang.count_method_params(code) == 2

    def test_one_param(self):
        lang = JavaLanguage()
        code = "class Solution { public boolean isPalindrome(int x) { return true; } }"
        assert lang.count_method_params(code) == 1

    def test_zero_params(self):
        lang = JavaLanguage()
        code = "class Solution { public int answer() { return 42; } }"
        assert lang.count_method_params(code) == 0

    def test_no_method(self):
        lang = JavaLanguage()
        assert lang.count_method_params("class Solution {}") == 0


class TestJavaRunTestCase:
    """Tests for JavaLanguage.run_test_case()."""

    def test_passing_test(self, valid_java_solution):
        lang = JavaLanguage()
        result = lang.run_test_case(
            code=valid_java_solution,
            input_args=[[2, 7, 11, 15], 9],
            expected_output=[0, 1],
        )
        assert result.passed is True
        assert result.actual == [0, 1]

    def test_failing_test(self, wrong_java_solution):
        lang = JavaLanguage()
        result = lang.run_test_case(
            code=wrong_java_solution,
            input_args=[[2, 7, 11, 15], 9],
            expected_output=[0, 1],
        )
        assert result.passed is False
        assert result.actual == [0, 0]

    def test_missing_method(self):
        lang = JavaLanguage()
        result = lang.run_test_case(
            code="class Solution {}",
            input_args=[1],
            expected_output=1,
        )
        assert result.passed is False
        assert "Could not find solution method" in result.error

    def test_runtime_error(self):
        lang = JavaLanguage()
        code = 'class Solution { public int boom() { throw new RuntimeException("kaboom"); } }'
        result = lang.run_test_case(code=code, input_args=[], expected_output=None)
        assert result.passed is False
        assert result.error is not None

    def test_jdk_not_found(self, valid_java_solution):
        lang = JavaLanguage()
        with patch("shutil.which", return_value=None):
            result = lang.run_test_case(
                code=valid_java_solution,
                input_args=[[1], 1],
                expected_output=[0],
            )
        assert result.passed is False
        assert "javac not found" in result.error
