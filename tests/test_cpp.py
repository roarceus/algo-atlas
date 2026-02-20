"""Tests for C++ language support."""

import shutil
from unittest.mock import patch

from algo_atlas.languages import get_language, get_language_by_extension, list_languages
from algo_atlas.languages.base import LanguageSupport
from algo_atlas.languages.cpp import CppLanguage


class TestCppRegistry:
    """Tests for C++ in the language registry."""

    def test_get_language_cpp(self):
        lang = get_language("cpp")
        assert lang is not None
        assert isinstance(lang, CppLanguage)

    def test_get_language_by_extension_cpp(self):
        lang = get_language_by_extension(".cpp")
        assert lang is not None
        assert isinstance(lang, CppLanguage)

    def test_list_languages_includes_cpp(self):
        slugs = [info.slug for info in list_languages()]
        assert "cpp" in slugs


class TestCppInfo:
    """Tests for CppLanguage metadata."""

    def test_info(self):
        lang = CppLanguage()
        info = lang.info()
        assert info.name == "C++"
        assert info.slug == "cpp"
        assert info.file_extension == ".cpp"
        assert info.solution_filename == "solution.cpp"
        assert info.code_fence == "cpp"
        assert "cpp" in info.leetcode_slugs

    def test_is_language_support(self):
        assert isinstance(CppLanguage(), LanguageSupport)

    def test_can_run_tests_reflects_gpp(self):
        lang = CppLanguage()
        has_gpp = shutil.which("g++") is not None
        assert lang.can_run_tests() is has_gpp


class TestCppCheckSyntax:
    """Tests for CppLanguage.check_syntax()."""

    def test_valid_syntax(self, valid_cpp_solution):
        lang = CppLanguage()
        result = lang.check_syntax(valid_cpp_solution)
        assert result.valid is True
        assert result.error_message is None

    def test_invalid_syntax(self, invalid_cpp_syntax):
        lang = CppLanguage()
        result = lang.check_syntax(invalid_cpp_syntax)
        assert result.valid is False
        assert result.error_message is not None

    def test_empty_code(self):
        lang = CppLanguage()
        result = lang.check_syntax("")
        assert result.valid is True

    def test_gpp_not_found(self):
        lang = CppLanguage()
        with patch("shutil.which", return_value=None):
            result = lang.check_syntax("class Solution {};")
        assert result.valid is False
        assert "g++ not found" in result.error_message


class TestCppExtractMethodName:
    """Tests for CppLanguage.extract_method_name()."""

    def test_int_return(self):
        lang = CppLanguage()
        code = "class Solution {\npublic:\n    int add(int a, int b) { return a + b; }\n};"
        assert lang.extract_method_name(code) == "add"

    def test_vector_return(self):
        lang = CppLanguage()
        code = "class Solution {\npublic:\n    vector<int> twoSum(vector<int>& nums, int t) { return {}; }\n};"
        assert lang.extract_method_name(code) == "twoSum"

    def test_long_long_return(self):
        lang = CppLanguage()
        code = "class Solution {\npublic:\n    long long maximumSum(vector<int>& nums) { return 0; }\n};"
        assert lang.extract_method_name(code) == "maximumSum"

    def test_pointer_return(self):
        lang = CppLanguage()
        code = "class Solution {\npublic:\n    ListNode* addTwoNumbers(ListNode* l1, ListNode* l2) { return nullptr; }\n};"
        assert lang.extract_method_name(code) == "addTwoNumbers"

    def test_no_method(self):
        lang = CppLanguage()
        assert lang.extract_method_name("class Solution {};") is None


class TestCppCountMethodParams:
    """Tests for CppLanguage.count_method_params()."""

    def test_two_params(self):
        lang = CppLanguage()
        code = "class Solution {\npublic:\n    int twoSum(vector<int>& nums, int target) { return 0; }\n};"
        assert lang.count_method_params(code) == 2

    def test_one_param(self):
        lang = CppLanguage()
        code = "class Solution {\npublic:\n    bool isPalindrome(int x) { return true; }\n};"
        assert lang.count_method_params(code) == 1

    def test_zero_params(self):
        lang = CppLanguage()
        code = "class Solution {\npublic:\n    int answer() { return 42; }\n};"
        assert lang.count_method_params(code) == 0

    def test_template_param_with_comma(self):
        lang = CppLanguage()
        # unordered_map<string, int> has a comma inside the template — must count as 1 param
        code = "class Solution {\npublic:\n    int count(unordered_map<string, int>& m, int t) { return 0; }\n};"
        assert lang.count_method_params(code) == 2


class TestCppRunTestCase:
    """Tests for CppLanguage.run_test_case()."""

    def test_passing_test(self, valid_cpp_solution):
        lang = CppLanguage()
        result = lang.run_test_case(
            code=valid_cpp_solution,
            input_args=[[2, 7, 11, 15], 9],
            expected_output=[0, 1],
        )
        assert result.passed is True
        assert result.actual == [0, 1]

    def test_failing_test(self, wrong_cpp_solution):
        lang = CppLanguage()
        result = lang.run_test_case(
            code=wrong_cpp_solution,
            input_args=[[2, 7, 11, 15], 9],
            expected_output=[0, 1],
        )
        assert result.passed is False
        assert result.actual == [0, 0]

    def test_missing_method(self):
        lang = CppLanguage()
        result = lang.run_test_case(
            code="class Solution {};",
            input_args=[1],
            expected_output=1,
        )
        assert result.passed is False
        assert "Could not extract method name" in result.error

    def test_runtime_error(self):
        lang = CppLanguage()
        code = "class Solution {\npublic:\n    int boom() { throw runtime_error(\"kaboom\"); }\n};"
        result = lang.run_test_case(code=code, input_args=[], expected_output=None)
        assert result.passed is False
        assert result.error is not None

    def test_gpp_not_found(self, valid_cpp_solution):
        lang = CppLanguage()
        with patch("subprocess.run", side_effect=FileNotFoundError):
            result = lang.run_test_case(
                code=valid_cpp_solution,
                input_args=[[1], 1],
                expected_output=[0],
            )
        assert result.passed is False
        assert "g++ not found" in result.error
