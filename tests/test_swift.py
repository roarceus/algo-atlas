"""Tests for Swift language support."""

import shutil
from unittest.mock import patch

from algo_atlas.languages import get_language, get_language_by_extension, list_languages
from algo_atlas.languages.base import LanguageSupport
from algo_atlas.languages.swift import SwiftLanguage


class TestSwiftRegistry:
    """Tests for Swift in the language registry."""

    def test_get_language_swift(self):
        lang = get_language("swift")
        assert lang is not None
        assert isinstance(lang, SwiftLanguage)

    def test_get_language_by_extension_swift(self):
        lang = get_language_by_extension(".swift")
        assert lang is not None
        assert isinstance(lang, SwiftLanguage)

    def test_list_languages_includes_swift(self):
        slugs = [info.slug for info in list_languages()]
        assert "swift" in slugs


class TestSwiftInfo:
    """Tests for SwiftLanguage metadata."""

    def test_info(self):
        lang = SwiftLanguage()
        info = lang.info()
        assert info.name == "Swift"
        assert info.slug == "swift"
        assert info.file_extension == ".swift"
        assert info.solution_filename == "solution.swift"
        assert info.code_fence == "swift"
        assert "swift" in info.leetcode_slugs

    def test_is_language_support(self):
        assert isinstance(SwiftLanguage(), LanguageSupport)

    def test_can_run_tests_reflects_swiftc(self):
        lang = SwiftLanguage()
        has_swiftc = shutil.which("swiftc") is not None
        assert lang.can_run_tests() is has_swiftc


class TestSwiftCheckSyntax:
    """Tests for SwiftLanguage.check_syntax()."""

    def test_valid_syntax(self, valid_swift_solution):
        lang = SwiftLanguage()
        result = lang.check_syntax(valid_swift_solution)
        assert result.valid is True
        assert result.error_message is None

    def test_invalid_syntax(self, invalid_swift_syntax):
        lang = SwiftLanguage()
        result = lang.check_syntax(invalid_swift_syntax)
        assert result.valid is False
        assert result.error_message is not None

    def test_empty_code(self):
        lang = SwiftLanguage()
        result = lang.check_syntax("")
        assert result.valid is True

    def test_swiftc_not_found(self):
        lang = SwiftLanguage()
        with patch("shutil.which", return_value=None):
            result = lang.check_syntax(
                "class Solution { func solve(_ n: Int) -> Int { return n } }"
            )
        assert result.valid is False
        assert "swiftc not found" in result.error_message


class TestSwiftExtractMethodName:
    """Tests for SwiftLanguage.extract_method_name()."""

    def test_simple(self):
        lang = SwiftLanguage()
        code = "class Solution {\n    func solve(_ n: Int) -> Int { return n }\n}"
        assert lang.extract_method_name(code) == "solve"

    def test_array_return(self):
        lang = SwiftLanguage()
        code = "class Solution {\n    func twoSum(_ nums: [Int], _ target: Int) -> [Int] { return [] }\n}"
        assert lang.extract_method_name(code) == "twoSum"

    def test_bool_return(self):
        lang = SwiftLanguage()
        code = "class Solution {\n    func isPalindrome(_ s: String) -> Bool { return true }\n}"
        assert lang.extract_method_name(code) == "isPalindrome"

    def test_skips_init(self):
        lang = SwiftLanguage()
        code = (
            "class Solution {\n"
            "    init() {}\n"
            "    func solve(_ n: Int) -> Int { return n }\n"
            "}"
        )
        assert lang.extract_method_name(code) == "solve"

    def test_no_method(self):
        lang = SwiftLanguage()
        assert lang.extract_method_name("class Foo {}") is None


class TestSwiftCountMethodParams:
    """Tests for SwiftLanguage.count_method_params()."""

    def test_one_param(self):
        lang = SwiftLanguage()
        code = "class Solution {\n    func climbStairs(_ n: Int) -> Int { return n }\n}"
        assert lang.count_method_params(code) == 1

    def test_two_params(self):
        lang = SwiftLanguage()
        code = "class Solution {\n    func twoSum(_ nums: [Int], _ target: Int) -> [Int] { return [] }\n}"
        assert lang.count_method_params(code) == 2

    def test_nested_array_param(self):
        lang = SwiftLanguage()
        # [[Int]] contains commas at depth > 0 — must count as 1 param
        code = (
            "class Solution {\n"
            "    func spiralOrder(_ matrix: [[Int]]) -> [Int] { return [] }\n"
            "}"
        )
        assert lang.count_method_params(code) == 1

    def test_no_match(self):
        lang = SwiftLanguage()
        assert lang.count_method_params("class Foo {}") == 0


class TestSwiftRunTestCase:
    """Tests for SwiftLanguage.run_test_case()."""

    def test_passing_test(self, valid_swift_solution):
        lang = SwiftLanguage()
        result = lang.run_test_case(
            code=valid_swift_solution,
            input_args=[[2, 7, 11, 15], 9],
            expected_output=[0, 1],
        )
        assert result.passed is True
        assert result.actual == [0, 1]

    def test_failing_test(self, wrong_swift_solution):
        lang = SwiftLanguage()
        result = lang.run_test_case(
            code=wrong_swift_solution,
            input_args=[[2, 7, 11, 15], 9],
            expected_output=[0, 1],
        )
        assert result.passed is False
        assert result.actual == [0, 0]

    def test_missing_method(self):
        lang = SwiftLanguage()
        result = lang.run_test_case(
            code="class Foo {}",
            input_args=[1],
            expected_output=1,
        )
        assert result.passed is False
        assert "Could not extract method name" in result.error

    def test_runtime_error(self):
        lang = SwiftLanguage()
        code = (
            "class Solution {\n"
            "    func boom(_ n: Int) -> Int {\n"
            '        fatalError("kaboom")\n'
            "    }\n"
            "}"
        )
        result = lang.run_test_case(code=code, input_args=[1], expected_output=0)
        assert result.passed is False
        assert result.error is not None

    def test_swiftc_not_found(self, valid_swift_solution):
        lang = SwiftLanguage()
        with patch("subprocess.run", side_effect=FileNotFoundError):
            result = lang.run_test_case(
                code=valid_swift_solution,
                input_args=[[2, 7, 11, 15], 9],
                expected_output=[0, 1],
            )
        assert result.passed is False
        assert "swiftc not found" in result.error
