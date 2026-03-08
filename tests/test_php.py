"""Tests for PHP language support."""

import shutil
from unittest.mock import patch

from algo_atlas.languages import get_language, get_language_by_extension, list_languages
from algo_atlas.languages.base import LanguageSupport
from algo_atlas.languages.php import PHPLanguage


class TestPHPRegistry:
    """Tests for PHP in the language registry."""

    def test_get_language_php(self):
        lang = get_language("php")
        assert lang is not None
        assert isinstance(lang, PHPLanguage)

    def test_get_language_by_extension_php(self):
        lang = get_language_by_extension(".php")
        assert lang is not None
        assert isinstance(lang, PHPLanguage)

    def test_list_languages_includes_php(self):
        slugs = [info.slug for info in list_languages()]
        assert "php" in slugs


class TestPHPInfo:
    """Tests for PHPLanguage metadata."""

    def test_info(self):
        lang = PHPLanguage()
        info = lang.info()
        assert info.name == "PHP"
        assert info.slug == "php"
        assert info.file_extension == ".php"
        assert info.solution_filename == "solution.php"
        assert info.code_fence == "php"
        assert "php" in info.leetcode_slugs

    def test_is_language_support(self):
        assert isinstance(PHPLanguage(), LanguageSupport)

    def test_can_run_tests_reflects_php(self):
        lang = PHPLanguage()
        has_php = shutil.which("php") is not None
        assert lang.can_run_tests() is has_php


class TestPHPCheckSyntax:
    """Tests for PHPLanguage.check_syntax()."""

    def test_valid_syntax(self, valid_php_solution):
        lang = PHPLanguage()
        result = lang.check_syntax(valid_php_solution)
        assert result.valid is True
        assert result.error_message is None

    def test_invalid_syntax(self, invalid_php_syntax):
        lang = PHPLanguage()
        result = lang.check_syntax(invalid_php_syntax)
        assert result.valid is False
        assert result.error_message is not None

    def test_empty_code(self):
        lang = PHPLanguage()
        result = lang.check_syntax("")
        assert result.valid is True

    def test_php_not_found(self):
        lang = PHPLanguage()
        with patch("shutil.which", return_value=None):
            result = lang.check_syntax(
                "<?php\nclass Solution {\n    function solve($n) { return $n; }\n}"
            )
        assert result.valid is False
        assert "php not found" in result.error_message


class TestPHPExtractMethodName:
    """Tests for PHPLanguage.extract_method_name()."""

    def test_simple(self):
        lang = PHPLanguage()
        code = "<?php\nclass Solution {\n    function solve($n) { return $n; }\n}"
        assert lang.extract_method_name(code) == "solve"

    def test_public_function(self):
        lang = PHPLanguage()
        code = "<?php\nclass Solution {\n    public function twoSum($nums, $target) { return []; }\n}"
        assert lang.extract_method_name(code) == "twoSum"

    def test_skips_construct(self):
        lang = PHPLanguage()
        code = (
            "<?php\nclass Solution {\n"
            "    public function __construct() {}\n"
            "    public function solve($n) { return $n; }\n"
            "}"
        )
        assert lang.extract_method_name(code) == "solve"

    def test_no_method(self):
        lang = PHPLanguage()
        assert lang.extract_method_name("<?php\nclass Foo {}") is None

    def test_camel_case(self):
        lang = PHPLanguage()
        code = "<?php\nclass Solution {\n    function maxProfit($prices) { return 0; }\n}"
        assert lang.extract_method_name(code) == "maxProfit"


class TestPHPCountMethodParams:
    """Tests for PHPLanguage.count_method_params()."""

    def test_one_param(self):
        lang = PHPLanguage()
        code = "<?php\nclass Solution {\n    function climbStairs($n) { return $n; }\n}"
        assert lang.count_method_params(code) == 1

    def test_two_params(self):
        lang = PHPLanguage()
        code = "<?php\nclass Solution {\n    function twoSum($nums, $target) { return []; }\n}"
        assert lang.count_method_params(code) == 2

    def test_typed_params(self):
        lang = PHPLanguage()
        code = "<?php\nclass Solution {\n    function twoSum(array $nums, int $target): array { return []; }\n}"
        assert lang.count_method_params(code) == 2

    def test_no_match(self):
        lang = PHPLanguage()
        assert lang.count_method_params("<?php\nclass Foo {}") == 0


class TestPHPRunTestCase:
    """Tests for PHPLanguage.run_test_case()."""

    def test_passing_test(self, valid_php_solution):
        lang = PHPLanguage()
        result = lang.run_test_case(
            code=valid_php_solution,
            input_args=[[2, 7, 11, 15], 9],
            expected_output=[0, 1],
        )
        assert result.passed is True
        assert result.actual == [0, 1]

    def test_failing_test(self, wrong_php_solution):
        lang = PHPLanguage()
        result = lang.run_test_case(
            code=wrong_php_solution,
            input_args=[[2, 7, 11, 15], 9],
            expected_output=[0, 1],
        )
        assert result.passed is False
        assert result.actual == [0, 0]

    def test_missing_method(self):
        lang = PHPLanguage()
        result = lang.run_test_case(
            code="<?php\nclass Foo {}",
            input_args=[1],
            expected_output=1,
        )
        assert result.passed is False
        assert "Could not extract method name" in result.error

    def test_runtime_error(self):
        lang = PHPLanguage()
        code = (
            "<?php\nclass Solution {\n"
            "    function boom($n) {\n"
            "        throw new Exception('kaboom');\n"
            "    }\n"
            "}"
        )
        result = lang.run_test_case(code=code, input_args=[1], expected_output=0)
        assert result.passed is False
        assert result.error is not None

    def test_php_not_found(self, valid_php_solution):
        lang = PHPLanguage()
        with patch("shutil.which", return_value=None):
            result = lang.run_test_case(
                code=valid_php_solution,
                input_args=[[2, 7, 11, 15], 9],
                expected_output=[0, 1],
            )
        assert result.passed is False
        assert "php not found" in result.error
