"""Tests for TypeScript language support."""

import shutil
from unittest.mock import patch

from algo_atlas.languages import get_language, get_language_by_extension, list_languages
from algo_atlas.languages.base import LanguageSupport
from algo_atlas.languages.typescript import TypeScriptLanguage

# ---------------------------------------------------------------------------
# Registry integration
# ---------------------------------------------------------------------------


class TestTypeScriptRegistry:
    """Tests for TypeScript in the language registry."""

    def test_get_language_typescript(self):
        lang = get_language("typescript")
        assert lang is not None
        assert isinstance(lang, TypeScriptLanguage)

    def test_get_language_by_extension_ts(self):
        lang = get_language_by_extension(".ts")
        assert lang is not None
        assert isinstance(lang, TypeScriptLanguage)

    def test_list_languages_includes_ts(self):
        slugs = [info.slug for info in list_languages()]
        assert "typescript" in slugs


# ---------------------------------------------------------------------------
# LanguageInfo metadata
# ---------------------------------------------------------------------------


class TestTypeScriptInfo:
    """Tests for TypeScriptLanguage metadata."""

    def test_info(self):
        lang = TypeScriptLanguage()
        info = lang.info()
        assert info.name == "TypeScript"
        assert info.slug == "typescript"
        assert info.file_extension == ".ts"
        assert info.solution_filename == "solution.ts"
        assert info.code_fence == "typescript"
        assert "typescript" in info.leetcode_slugs

    def test_is_language_support(self):
        lang = TypeScriptLanguage()
        assert isinstance(lang, LanguageSupport)

    def test_can_run_tests_reflects_runtime(self):
        lang = TypeScriptLanguage()
        has_runtime = shutil.which("tsx") is not None or shutil.which("npx") is not None
        assert lang.can_run_tests() is has_runtime


# ---------------------------------------------------------------------------
# check_syntax
# ---------------------------------------------------------------------------


class TestTypeScriptCheckSyntax:
    """Tests for TypeScriptLanguage.check_syntax()."""

    def test_valid_syntax(self, valid_ts_solution):
        lang = TypeScriptLanguage()
        result = lang.check_syntax(valid_ts_solution)
        assert result.valid is True
        assert result.error_message is None

    def test_invalid_syntax(self, invalid_ts_syntax):
        lang = TypeScriptLanguage()
        result = lang.check_syntax(invalid_ts_syntax)
        assert result.valid is False
        assert result.error_message is not None

    def test_empty_code(self):
        lang = TypeScriptLanguage()
        result = lang.check_syntax("")
        assert result.valid is True

    def test_runtime_not_found(self):
        lang = TypeScriptLanguage()
        with patch("shutil.which", return_value=None):
            result = lang.check_syntax("const x: number = 1;")
        assert result.valid is False
        assert "tsx not found" in result.error_message


# ---------------------------------------------------------------------------
# extract_method_name
# ---------------------------------------------------------------------------


class TestTypeScriptExtractMethodName:
    """Tests for TypeScriptLanguage.extract_method_name()."""

    def test_function_declaration_with_types(self):
        lang = TypeScriptLanguage()
        code = (
            "function twoSum(nums: number[], target: number): number[] { return []; }"
        )
        assert lang.extract_method_name(code) == "twoSum"

    def test_var_function_expression(self):
        lang = TypeScriptLanguage()
        code = "var isPalindrome = function(x: number): boolean { return true; };"
        assert lang.extract_method_name(code) == "isPalindrome"

    def test_const_arrow_with_return_type(self):
        lang = TypeScriptLanguage()
        code = "const addTwo = (a: number, b: number): number => a + b;"
        assert lang.extract_method_name(code) == "addTwo"

    def test_let_arrow_no_parens(self):
        lang = TypeScriptLanguage()
        code = "let double = x => x * 2;"
        assert lang.extract_method_name(code) == "double"

    def test_no_function_found(self):
        lang = TypeScriptLanguage()
        assert lang.extract_method_name("// just a comment") is None


# ---------------------------------------------------------------------------
# count_method_params
# ---------------------------------------------------------------------------


class TestTypeScriptCountMethodParams:
    """Tests for TypeScriptLanguage.count_method_params()."""

    def test_two_params_with_types(self):
        lang = TypeScriptLanguage()
        code = (
            "function twoSum(nums: number[], target: number): number[] { return []; }"
        )
        assert lang.count_method_params(code) == 2

    def test_one_param_arrow_no_parens(self):
        lang = TypeScriptLanguage()
        code = "let double = x => x * 2;"
        assert lang.count_method_params(code) == 1

    def test_zero_params(self):
        lang = TypeScriptLanguage()
        code = "function solve(): number { return 42; }"
        assert lang.count_method_params(code) == 0

    def test_no_function(self):
        lang = TypeScriptLanguage()
        assert lang.count_method_params("// nothing here") == 0


# ---------------------------------------------------------------------------
# run_test_case
# ---------------------------------------------------------------------------


class TestTypeScriptRunTestCase:
    """Tests for TypeScriptLanguage.run_test_case()."""

    def test_passing_test(self, valid_ts_solution):
        lang = TypeScriptLanguage()
        result = lang.run_test_case(
            code=valid_ts_solution,
            input_args=[[2, 7, 11, 15], 9],
            expected_output=[0, 1],
        )
        assert result.passed is True
        assert result.actual == [0, 1]

    def test_failing_test(self, wrong_ts_solution):
        lang = TypeScriptLanguage()
        result = lang.run_test_case(
            code=wrong_ts_solution,
            input_args=[[2, 7, 11, 15], 9],
            expected_output=[0, 1],
        )
        assert result.passed is False
        assert result.actual == [0, 0]

    def test_missing_function(self):
        lang = TypeScriptLanguage()
        result = lang.run_test_case(
            code="// empty",
            input_args=[1],
            expected_output=1,
        )
        assert result.passed is False
        assert "Could not find solution function" in result.error

    def test_runtime_error(self):
        lang = TypeScriptLanguage()
        code = "function boom(): void { throw new Error('kaboom'); }"
        result = lang.run_test_case(
            code=code,
            input_args=[],
            expected_output=None,
        )
        assert result.passed is False
        assert result.error is not None

    def test_runtime_not_found(self, valid_ts_solution):
        lang = TypeScriptLanguage()
        with patch("shutil.which", return_value=None):
            result = lang.run_test_case(
                code=valid_ts_solution,
                input_args=[[1], 1],
                expected_output=[0],
            )
        assert result.passed is False
        assert "tsx not found" in result.error
