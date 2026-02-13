"""Tests for JavaScript language support."""

import shutil
from unittest.mock import patch

from algo_atlas.languages import get_language, get_language_by_extension, list_languages
from algo_atlas.languages.base import LanguageSupport
from algo_atlas.languages.javascript import JavaScriptLanguage


# ---------------------------------------------------------------------------
# Registry integration
# ---------------------------------------------------------------------------

class TestJavaScriptRegistry:
    """Tests for JavaScript in the language registry."""

    def test_get_language_javascript(self):
        lang = get_language("javascript")
        assert lang is not None
        assert isinstance(lang, JavaScriptLanguage)

    def test_get_language_by_extension_js(self):
        lang = get_language_by_extension(".js")
        assert lang is not None
        assert isinstance(lang, JavaScriptLanguage)

    def test_list_languages_includes_js(self):
        slugs = [info.slug for info in list_languages()]
        assert "javascript" in slugs


# ---------------------------------------------------------------------------
# LanguageInfo metadata
# ---------------------------------------------------------------------------

class TestJavaScriptInfo:
    """Tests for JavaScriptLanguage metadata."""

    def test_info(self):
        lang = JavaScriptLanguage()
        info = lang.info()
        assert info.name == "JavaScript"
        assert info.slug == "javascript"
        assert info.file_extension == ".js"
        assert info.solution_filename == "solution.js"
        assert info.code_fence == "javascript"
        assert "javascript" in info.leetcode_slugs

    def test_is_language_support(self):
        lang = JavaScriptLanguage()
        assert isinstance(lang, LanguageSupport)

    def test_can_run_tests_reflects_node(self):
        lang = JavaScriptLanguage()
        has_node = shutil.which("node") is not None
        assert lang.can_run_tests() is has_node


# ---------------------------------------------------------------------------
# check_syntax
# ---------------------------------------------------------------------------

class TestJavaScriptCheckSyntax:
    """Tests for JavaScriptLanguage.check_syntax()."""

    def test_valid_syntax(self, valid_js_solution):
        lang = JavaScriptLanguage()
        result = lang.check_syntax(valid_js_solution)
        assert result.valid is True
        assert result.error_message is None

    def test_invalid_syntax(self, invalid_js_syntax):
        lang = JavaScriptLanguage()
        result = lang.check_syntax(invalid_js_syntax)
        assert result.valid is False
        assert result.error_message is not None

    def test_empty_code(self):
        lang = JavaScriptLanguage()
        result = lang.check_syntax("")
        assert result.valid is True

    def test_node_not_found(self):
        lang = JavaScriptLanguage()
        with patch("shutil.which", return_value=None):
            result = lang.check_syntax("var x = 1;")
        assert result.valid is False
        assert "Node.js not found" in result.error_message


# ---------------------------------------------------------------------------
# extract_method_name
# ---------------------------------------------------------------------------

class TestJavaScriptExtractMethodName:
    """Tests for JavaScriptLanguage.extract_method_name()."""

    def test_var_function_expression(self):
        lang = JavaScriptLanguage()
        code = "var twoSum = function(nums, target) { };"
        assert lang.extract_method_name(code) == "twoSum"

    def test_function_declaration(self):
        lang = JavaScriptLanguage()
        code = "function isPalindrome(x) { return true; }"
        assert lang.extract_method_name(code) == "isPalindrome"

    def test_const_arrow_with_parens(self):
        lang = JavaScriptLanguage()
        code = "const addTwo = (a, b) => a + b;"
        assert lang.extract_method_name(code) == "addTwo"

    def test_let_arrow_no_parens(self):
        lang = JavaScriptLanguage()
        code = "let double = x => x * 2;"
        assert lang.extract_method_name(code) == "double"

    def test_no_function_found(self):
        lang = JavaScriptLanguage()
        assert lang.extract_method_name("// just a comment") is None


# ---------------------------------------------------------------------------
# count_method_params
# ---------------------------------------------------------------------------

class TestJavaScriptCountMethodParams:
    """Tests for JavaScriptLanguage.count_method_params()."""

    def test_two_params(self):
        lang = JavaScriptLanguage()
        code = "var twoSum = function(nums, target) { };"
        assert lang.count_method_params(code) == 2

    def test_one_param_arrow_no_parens(self):
        lang = JavaScriptLanguage()
        code = "let double = x => x * 2;"
        assert lang.count_method_params(code) == 1

    def test_zero_params(self):
        lang = JavaScriptLanguage()
        code = "function solve() { return 42; }"
        assert lang.count_method_params(code) == 0

    def test_no_function(self):
        lang = JavaScriptLanguage()
        assert lang.count_method_params("// nothing here") == 0


# ---------------------------------------------------------------------------
# run_test_case
# ---------------------------------------------------------------------------

class TestJavaScriptRunTestCase:
    """Tests for JavaScriptLanguage.run_test_case()."""

    def test_passing_test(self, valid_js_solution):
        lang = JavaScriptLanguage()
        result = lang.run_test_case(
            code=valid_js_solution,
            input_args=[[2, 7, 11, 15], 9],
            expected_output=[0, 1],
        )
        assert result.passed is True
        assert result.actual == [0, 1]

    def test_failing_test(self, wrong_js_solution):
        lang = JavaScriptLanguage()
        result = lang.run_test_case(
            code=wrong_js_solution,
            input_args=[[2, 7, 11, 15], 9],
            expected_output=[0, 1],
        )
        assert result.passed is False
        assert result.actual == [0, 0]

    def test_missing_function(self):
        lang = JavaScriptLanguage()
        result = lang.run_test_case(
            code="// empty",
            input_args=[1],
            expected_output=1,
        )
        assert result.passed is False
        assert "Could not find solution function" in result.error

    def test_runtime_error(self):
        lang = JavaScriptLanguage()
        code = "function boom() { throw new Error('kaboom'); }"
        result = lang.run_test_case(
            code=code,
            input_args=[],
            expected_output=None,
        )
        assert result.passed is False
        assert result.error is not None

    def test_node_not_found(self, valid_js_solution):
        lang = JavaScriptLanguage()
        with patch("shutil.which", return_value=None):
            result = lang.run_test_case(
                code=valid_js_solution,
                input_args=[[1], 1],
                expected_output=[0],
            )
        assert result.passed is False
        assert "Node.js not found" in result.error
