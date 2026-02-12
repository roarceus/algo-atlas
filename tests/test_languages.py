"""Tests for the language support registry and PythonLanguage."""

from algo_atlas.languages import (
    default_language,
    get_language,
    get_language_by_extension,
    list_languages,
)
from algo_atlas.languages.base import LanguageSupport
from algo_atlas.languages.python import PythonLanguage


class TestRegistry:
    """Tests for the language registry."""

    def test_get_language_python3(self):
        """Test retrieving Python by primary slug."""
        lang = get_language("python3")
        assert lang is not None
        assert isinstance(lang, PythonLanguage)

    def test_get_language_python_alias(self):
        """Test retrieving Python by alias slug."""
        lang = get_language("python")
        assert lang is not None
        assert isinstance(lang, PythonLanguage)

    def test_get_language_unknown(self):
        """Test retrieving unknown language returns None."""
        assert get_language("brainfuck") is None

    def test_get_language_by_extension_py(self):
        """Test retrieving Python by .py extension."""
        lang = get_language_by_extension(".py")
        assert lang is not None
        assert isinstance(lang, PythonLanguage)

    def test_get_language_by_extension_unknown(self):
        """Test retrieving unknown extension returns None."""
        assert get_language_by_extension(".bf") is None

    def test_list_languages(self):
        """Test listing all registered languages."""
        langs = list_languages()
        assert len(langs) >= 1
        slugs = [info.slug for info in langs]
        assert "python3" in slugs

    def test_default_language(self):
        """Test default language is Python."""
        lang = default_language()
        assert isinstance(lang, PythonLanguage)
        assert lang.info().slug == "python3"


class TestPythonLanguageInfo:
    """Tests for PythonLanguage metadata."""

    def test_info(self):
        """Test PythonLanguage info returns correct metadata."""
        lang = PythonLanguage()
        info = lang.info()
        assert info.name == "Python"
        assert info.slug == "python3"
        assert info.file_extension == ".py"
        assert info.solution_filename == "solution.py"
        assert info.code_fence == "python"
        assert "python3" in info.leetcode_slugs
        assert "python" in info.leetcode_slugs

    def test_is_language_support(self):
        """Test PythonLanguage is a LanguageSupport instance."""
        lang = PythonLanguage()
        assert isinstance(lang, LanguageSupport)

    def test_can_run_tests(self):
        """Test Python can always run tests."""
        lang = PythonLanguage()
        assert lang.can_run_tests() is True


class TestPythonCheckSyntax:
    """Tests for PythonLanguage.check_syntax()."""

    def test_valid_syntax(self, valid_solution):
        lang = PythonLanguage()
        result = lang.check_syntax(valid_solution)
        assert result.valid is True
        assert result.error_message is None

    def test_invalid_syntax(self, invalid_syntax_solution):
        lang = PythonLanguage()
        result = lang.check_syntax(invalid_syntax_solution)
        assert result.valid is False
        assert result.error_message is not None

    def test_empty_code(self):
        lang = PythonLanguage()
        result = lang.check_syntax("")
        assert result.valid is True


class TestPythonExtractMethodName:
    """Tests for PythonLanguage.extract_method_name()."""

    def test_extract_from_solution(self, valid_solution):
        lang = PythonLanguage()
        name = lang.extract_method_name(valid_solution)
        assert name == "twoSum"

    def test_extract_skips_private(self):
        lang = PythonLanguage()
        code = """class Solution:
    def _helper(self): pass
    def solve(self, x): return x
"""
        assert lang.extract_method_name(code) == "solve"

    def test_extract_from_invalid_syntax(self, invalid_syntax_solution):
        lang = PythonLanguage()
        assert lang.extract_method_name(invalid_syntax_solution) is None

    def test_extract_no_solution_class(self):
        lang = PythonLanguage()
        assert lang.extract_method_name("def foo(): pass") is None


class TestPythonCountMethodParams:
    """Tests for PythonLanguage.count_method_params()."""

    def test_two_params(self, valid_solution):
        lang = PythonLanguage()
        assert lang.count_method_params(valid_solution) == 2

    def test_one_param(self):
        lang = PythonLanguage()
        code = """class Solution:
    def solve(self, x): return x
"""
        assert lang.count_method_params(code) == 1

    def test_no_solution_class(self):
        lang = PythonLanguage()
        assert lang.count_method_params("x = 1") == 0


class TestPythonRunTestCase:
    """Tests for PythonLanguage.run_test_case()."""

    def test_passing_test(self, valid_solution):
        lang = PythonLanguage()
        result = lang.run_test_case(
            code=valid_solution,
            input_args=[[2, 7, 11, 15], 9],
            expected_output=[0, 1],
        )
        assert result.passed is True
        assert result.actual == [0, 1]

    def test_failing_test(self, wrong_solution):
        lang = PythonLanguage()
        result = lang.run_test_case(
            code=wrong_solution,
            input_args=[[2, 7, 11, 15], 9],
            expected_output=[0, 1],
        )
        assert result.passed is False

    def test_missing_solution_class(self):
        lang = PythonLanguage()
        result = lang.run_test_case(
            code="def foo(): pass",
            input_args=[1],
            expected_output=1,
        )
        assert result.passed is False
        assert "Solution" in result.error
