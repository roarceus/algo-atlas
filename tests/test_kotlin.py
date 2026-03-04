"""Tests for Kotlin language support."""

import shutil
from unittest.mock import patch

from algo_atlas.languages import get_language, get_language_by_extension, list_languages
from algo_atlas.languages.base import LanguageSupport
from algo_atlas.languages.kotlin import KotlinLanguage


class TestKotlinRegistry:
    """Tests for Kotlin in the language registry."""

    def test_get_language_kotlin(self):
        lang = get_language("kotlin")
        assert lang is not None
        assert isinstance(lang, KotlinLanguage)

    def test_get_language_by_extension_kotlin(self):
        lang = get_language_by_extension(".kt")
        assert lang is not None
        assert isinstance(lang, KotlinLanguage)

    def test_list_languages_includes_kotlin(self):
        slugs = [info.slug for info in list_languages()]
        assert "kotlin" in slugs


class TestKotlinInfo:
    """Tests for KotlinLanguage metadata."""

    def test_info(self):
        lang = KotlinLanguage()
        info = lang.info()
        assert info.name == "Kotlin"
        assert info.slug == "kotlin"
        assert info.file_extension == ".kt"
        assert info.solution_filename == "solution.kt"
        assert info.code_fence == "kotlin"
        assert "kotlin" in info.leetcode_slugs

    def test_is_language_support(self):
        assert isinstance(KotlinLanguage(), LanguageSupport)

    def test_can_run_tests_reflects_kotlinc(self):
        lang = KotlinLanguage()
        has_kotlinc = shutil.which("kotlinc") is not None
        assert lang.can_run_tests() is has_kotlinc


class TestKotlinCheckSyntax:
    """Tests for KotlinLanguage.check_syntax()."""

    def test_valid_syntax(self, valid_kotlin_solution):
        lang = KotlinLanguage()
        result = lang.check_syntax(valid_kotlin_solution)
        assert result.valid is True
        assert result.error_message is None

    def test_invalid_syntax(self, invalid_kotlin_syntax):
        lang = KotlinLanguage()
        result = lang.check_syntax(invalid_kotlin_syntax)
        assert result.valid is False
        assert result.error_message is not None

    def test_empty_code(self):
        lang = KotlinLanguage()
        result = lang.check_syntax("")
        assert result.valid is True

    def test_kotlinc_not_found(self):
        lang = KotlinLanguage()
        with patch("shutil.which", return_value=None):
            result = lang.check_syntax(
                "class Solution { fun solve(n: Int): Int { return n } }"
            )
        assert result.valid is False
        assert "kotlinc not found" in result.error_message


class TestKotlinExtractMethodName:
    """Tests for KotlinLanguage.extract_method_name()."""

    def test_simple(self):
        lang = KotlinLanguage()
        code = "class Solution {\n    fun solve(n: Int): Int { return n }\n}"
        assert lang.extract_method_name(code) == "solve"

    def test_inarray_return(self):
        lang = KotlinLanguage()
        code = "class Solution {\n    fun twoSum(nums: IntArray, target: Int): IntArray { return intArrayOf() }\n}"
        assert lang.extract_method_name(code) == "twoSum"

    def test_list_return(self):
        lang = KotlinLanguage()
        code = "class Solution {\n    fun groupAnagrams(strs: Array<String>): List<List<String>> { return listOf() }\n}"
        assert lang.extract_method_name(code) == "groupAnagrams"

    def test_skips_keywords(self):
        lang = KotlinLanguage()
        code = (
            "class Solution {\n"
            '    override fun toString(): String { return "" }\n'
            "    fun solve(n: Int): Int { return n }\n"
            "}"
        )
        assert lang.extract_method_name(code) == "solve"

    def test_no_method(self):
        lang = KotlinLanguage()
        assert lang.extract_method_name("class Foo {}") is None


class TestKotlinCountMethodParams:
    """Tests for KotlinLanguage.count_method_params()."""

    def test_one_param(self):
        lang = KotlinLanguage()
        code = "class Solution {\n    fun climbStairs(n: Int): Int { return n }\n}"
        assert lang.count_method_params(code) == 1

    def test_two_params(self):
        lang = KotlinLanguage()
        code = "class Solution {\n    fun twoSum(nums: IntArray, target: Int): IntArray { return intArrayOf() }\n}"
        assert lang.count_method_params(code) == 2

    def test_generic_param_with_comma(self):
        lang = KotlinLanguage()
        # HashMap<Int, Int> has a comma inside <> — must count as 1 param
        code = (
            "class Solution {\n"
            "    fun count(map: HashMap<Int, Int>, k: Int): Int { return 0 }\n"
            "}"
        )
        assert lang.count_method_params(code) == 2

    def test_no_match(self):
        lang = KotlinLanguage()
        assert lang.count_method_params("class Foo {}") == 0


class TestKotlinRunTestCase:
    """Tests for KotlinLanguage.run_test_case()."""

    def test_passing_test(self, valid_kotlin_solution):
        lang = KotlinLanguage()
        result = lang.run_test_case(
            code=valid_kotlin_solution,
            input_args=[[2, 7, 11, 15], 9],
            expected_output=[0, 1],
        )
        assert result.passed is True
        assert result.actual == [0, 1]

    def test_failing_test(self, wrong_kotlin_solution):
        lang = KotlinLanguage()
        result = lang.run_test_case(
            code=wrong_kotlin_solution,
            input_args=[[2, 7, 11, 15], 9],
            expected_output=[0, 1],
        )
        assert result.passed is False
        assert result.actual == [0, 0]

    def test_missing_method(self):
        lang = KotlinLanguage()
        result = lang.run_test_case(
            code="class Foo {}",
            input_args=[1],
            expected_output=1,
        )
        assert result.passed is False
        assert "Could not extract method name" in result.error

    def test_runtime_error(self):
        lang = KotlinLanguage()
        code = (
            "class Solution {\n"
            "    fun boom(n: Int): Int {\n"
            '        throw RuntimeException("kaboom")\n'
            "    }\n"
            "}"
        )
        result = lang.run_test_case(code=code, input_args=[1], expected_output=0)
        assert result.passed is False
        assert result.error is not None

    def test_kotlinc_not_found(self, valid_kotlin_solution):
        lang = KotlinLanguage()
        with patch("subprocess.run", side_effect=FileNotFoundError):
            result = lang.run_test_case(
                code=valid_kotlin_solution,
                input_args=[[2, 7, 11, 15], 9],
                expected_output=[0, 1],
            )
        assert result.passed is False
        assert "kotlinc not found" in result.error
