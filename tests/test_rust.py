"""Tests for Rust language support."""

import shutil
from unittest.mock import patch

from algo_atlas.languages import get_language, get_language_by_extension, list_languages
from algo_atlas.languages.base import LanguageSupport
from algo_atlas.languages.rust import RustLanguage


class TestRustRegistry:
    """Tests for Rust in the language registry."""

    def test_get_language_rust(self):
        lang = get_language("rust")
        assert lang is not None
        assert isinstance(lang, RustLanguage)

    def test_get_language_by_extension_rust(self):
        lang = get_language_by_extension(".rs")
        assert lang is not None
        assert isinstance(lang, RustLanguage)

    def test_list_languages_includes_rust(self):
        slugs = [info.slug for info in list_languages()]
        assert "rust" in slugs


class TestRustInfo:
    """Tests for RustLanguage metadata."""

    def test_info(self):
        lang = RustLanguage()
        info = lang.info()
        assert info.name == "Rust"
        assert info.slug == "rust"
        assert info.file_extension == ".rs"
        assert info.solution_filename == "solution.rs"
        assert info.code_fence == "rust"
        assert "rust" in info.leetcode_slugs

    def test_is_language_support(self):
        assert isinstance(RustLanguage(), LanguageSupport)

    def test_can_run_tests_reflects_rustc(self):
        lang = RustLanguage()
        has_rustc = shutil.which("rustc") is not None
        assert lang.can_run_tests() is has_rustc


class TestRustCheckSyntax:
    """Tests for RustLanguage.check_syntax()."""

    def test_valid_syntax(self, valid_rust_solution):
        lang = RustLanguage()
        result = lang.check_syntax(valid_rust_solution)
        assert result.valid is True
        assert result.error_message is None

    def test_invalid_syntax(self, invalid_rust_syntax):
        lang = RustLanguage()
        result = lang.check_syntax(invalid_rust_syntax)
        assert result.valid is False
        assert result.error_message is not None

    def test_empty_code(self):
        lang = RustLanguage()
        result = lang.check_syntax("")
        assert result.valid is True

    def test_rustc_not_found(self):
        lang = RustLanguage()
        with patch("shutil.which", return_value=None):
            result = lang.check_syntax("impl Solution { pub fn f() {} }")
        assert result.valid is False
        assert "rustc not found" in result.error_message


class TestRustExtractMethodName:
    """Tests for RustLanguage.extract_method_name()."""

    def test_simple(self):
        lang = RustLanguage()
        code = "impl Solution {\n    pub fn climb_stairs(n: i32) -> i32 { n }\n}"
        assert lang.extract_method_name(code) == "climb_stairs"

    def test_vec_return(self):
        lang = RustLanguage()
        code = "impl Solution {\n    pub fn two_sum(nums: Vec<i32>, target: i32) -> Vec<i32> { vec![] }\n}"
        assert lang.extract_method_name(code) == "two_sum"

    def test_bool_return(self):
        lang = RustLanguage()
        code = "impl Solution {\n    pub fn is_palindrome(s: String) -> bool { true }\n}"
        assert lang.extract_method_name(code) == "is_palindrome"

    def test_skips_new(self):
        lang = RustLanguage()
        code = "impl Solution {\n    pub fn new() -> Self { Self }\n    pub fn solve(n: i32) -> i32 { n }\n}"
        assert lang.extract_method_name(code) == "solve"

    def test_no_method(self):
        lang = RustLanguage()
        assert lang.extract_method_name("struct Solution;") is None


class TestRustCountMethodParams:
    """Tests for RustLanguage.count_method_params()."""

    def test_one_param(self):
        lang = RustLanguage()
        code = "impl Solution {\n    pub fn climb_stairs(n: i32) -> i32 { n }\n}"
        assert lang.count_method_params(code) == 1

    def test_two_params(self):
        lang = RustLanguage()
        code = "impl Solution {\n    pub fn two_sum(nums: Vec<i32>, target: i32) -> Vec<i32> { vec![] }\n}"
        assert lang.count_method_params(code) == 2

    def test_generic_param_with_comma(self):
        lang = RustLanguage()
        # HashMap<i32, i32> has a comma inside <> — must count as 1 param
        code = "impl Solution {\n    pub fn count(map: std::collections::HashMap<i32, i32>, k: i32) -> i32 { 0 }\n}"
        assert lang.count_method_params(code) == 2

    def test_no_match(self):
        lang = RustLanguage()
        assert lang.count_method_params("struct Solution;") == 0


class TestRustRunTestCase:
    """Tests for RustLanguage.run_test_case()."""

    def test_passing_test(self, valid_rust_solution):
        lang = RustLanguage()
        result = lang.run_test_case(
            code=valid_rust_solution,
            input_args=[5],
            expected_output=8,
        )
        assert result.passed is True
        assert result.actual == 8

    def test_failing_test(self, wrong_rust_solution):
        lang = RustLanguage()
        result = lang.run_test_case(
            code=wrong_rust_solution,
            input_args=[5],
            expected_output=8,
        )
        assert result.passed is False
        assert result.actual == 0

    def test_missing_method(self):
        lang = RustLanguage()
        result = lang.run_test_case(
            code="struct Solution;",
            input_args=[1],
            expected_output=1,
        )
        assert result.passed is False
        assert "Could not extract method name" in result.error

    def test_runtime_error(self):
        lang = RustLanguage()
        code = "impl Solution {\n    pub fn boom(n: i32) -> i32 { panic!(\"kaboom\"); }\n}"
        result = lang.run_test_case(code=code, input_args=[1], expected_output=0)
        assert result.passed is False
        assert result.error is not None

    def test_rustc_not_found(self, valid_rust_solution):
        lang = RustLanguage()
        with patch("subprocess.run", side_effect=FileNotFoundError):
            result = lang.run_test_case(
                code=valid_rust_solution,
                input_args=[5],
                expected_output=8,
            )
        assert result.passed is False
        assert "rustc not found" in result.error
