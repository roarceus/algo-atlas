"""Tests for Ruby language support."""

import shutil
from unittest.mock import patch

from algo_atlas.languages import get_language, get_language_by_extension, list_languages
from algo_atlas.languages.base import LanguageSupport
from algo_atlas.languages.ruby import RubyLanguage


class TestRubyRegistry:
    """Tests for Ruby in the language registry."""

    def test_get_language_ruby(self):
        lang = get_language("ruby")
        assert lang is not None
        assert isinstance(lang, RubyLanguage)

    def test_get_language_by_extension_ruby(self):
        lang = get_language_by_extension(".rb")
        assert lang is not None
        assert isinstance(lang, RubyLanguage)

    def test_list_languages_includes_ruby(self):
        slugs = [info.slug for info in list_languages()]
        assert "ruby" in slugs


class TestRubyInfo:
    """Tests for RubyLanguage metadata."""

    def test_info(self):
        lang = RubyLanguage()
        info = lang.info()
        assert info.name == "Ruby"
        assert info.slug == "ruby"
        assert info.file_extension == ".rb"
        assert info.solution_filename == "solution.rb"
        assert info.code_fence == "ruby"
        assert "ruby" in info.leetcode_slugs

    def test_is_language_support(self):
        assert isinstance(RubyLanguage(), LanguageSupport)

    def test_can_run_tests_reflects_ruby(self):
        lang = RubyLanguage()
        has_ruby = shutil.which("ruby") is not None
        assert lang.can_run_tests() is has_ruby


class TestRubyCheckSyntax:
    """Tests for RubyLanguage.check_syntax()."""

    def test_valid_syntax(self, valid_ruby_solution):
        lang = RubyLanguage()
        result = lang.check_syntax(valid_ruby_solution)
        assert result.valid is True
        assert result.error_message is None

    def test_invalid_syntax(self, invalid_ruby_syntax):
        lang = RubyLanguage()
        result = lang.check_syntax(invalid_ruby_syntax)
        assert result.valid is False
        assert result.error_message is not None

    def test_empty_code(self):
        lang = RubyLanguage()
        result = lang.check_syntax("")
        assert result.valid is True

    def test_ruby_not_found(self):
        lang = RubyLanguage()
        with patch("shutil.which", return_value=None):
            result = lang.check_syntax(
                "class Solution\n  def solve(n)\n    n\n  end\nend"
            )
        assert result.valid is False
        assert "ruby not found" in result.error_message


class TestRubyExtractMethodName:
    """Tests for RubyLanguage.extract_method_name()."""

    def test_simple(self):
        lang = RubyLanguage()
        code = "class Solution\n  def solve(n)\n    n\n  end\nend"
        assert lang.extract_method_name(code) == "solve"

    def test_snake_case(self):
        lang = RubyLanguage()
        code = "class Solution\n  def two_sum(nums, target)\n    []\n  end\nend"
        assert lang.extract_method_name(code) == "two_sum"

    def test_skips_initialize(self):
        lang = RubyLanguage()
        code = (
            "class Solution\n"
            "  def initialize\n"
            "  end\n"
            "  def solve(n)\n"
            "    n\n"
            "  end\n"
            "end"
        )
        assert lang.extract_method_name(code) == "solve"

    def test_no_method(self):
        lang = RubyLanguage()
        assert lang.extract_method_name("class Foo\nend") is None

    def test_predicate_method(self):
        lang = RubyLanguage()
        code = "class Solution\n  def is_palindrome(s)\n    true\n  end\nend"
        assert lang.extract_method_name(code) == "is_palindrome"


class TestRubyCountMethodParams:
    """Tests for RubyLanguage.count_method_params()."""

    def test_one_param(self):
        lang = RubyLanguage()
        code = "class Solution\n  def climb_stairs(n)\n    n\n  end\nend"
        assert lang.count_method_params(code) == 1

    def test_two_params(self):
        lang = RubyLanguage()
        code = "class Solution\n  def two_sum(nums, target)\n    []\n  end\nend"
        assert lang.count_method_params(code) == 2

    def test_three_params(self):
        lang = RubyLanguage()
        code = "class Solution\n  def solve(a, b, c)\n    0\n  end\nend"
        assert lang.count_method_params(code) == 3

    def test_no_match(self):
        lang = RubyLanguage()
        assert lang.count_method_params("class Foo\nend") == 0


class TestRubyRunTestCase:
    """Tests for RubyLanguage.run_test_case()."""

    def test_passing_test(self, valid_ruby_solution):
        lang = RubyLanguage()
        result = lang.run_test_case(
            code=valid_ruby_solution,
            input_args=[[2, 7, 11, 15], 9],
            expected_output=[0, 1],
        )
        assert result.passed is True
        assert result.actual == [0, 1]

    def test_failing_test(self, wrong_ruby_solution):
        lang = RubyLanguage()
        result = lang.run_test_case(
            code=wrong_ruby_solution,
            input_args=[[2, 7, 11, 15], 9],
            expected_output=[0, 1],
        )
        assert result.passed is False
        assert result.actual == [0, 0]

    def test_missing_method(self):
        lang = RubyLanguage()
        result = lang.run_test_case(
            code="class Foo\nend",
            input_args=[1],
            expected_output=1,
        )
        assert result.passed is False
        assert "Could not extract method name" in result.error

    def test_runtime_error(self):
        lang = RubyLanguage()
        code = (
            "class Solution\n" "  def boom(n)\n" "    raise 'kaboom'\n" "  end\n" "end"
        )
        result = lang.run_test_case(code=code, input_args=[1], expected_output=0)
        assert result.passed is False
        assert result.error is not None

    def test_ruby_not_found(self, valid_ruby_solution):
        lang = RubyLanguage()
        with patch("shutil.which", return_value=None):
            result = lang.run_test_case(
                code=valid_ruby_solution,
                input_args=[[2, 7, 11, 15], 9],
                expected_output=[0, 1],
            )
        assert result.passed is False
        assert "ruby not found" in result.error
