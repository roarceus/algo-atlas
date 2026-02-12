"""Tests for the LeetCode scraper module."""

from unittest.mock import patch

from algo_atlas.core.scraper import (
    _get_code_snippet,
    extract_test_cases,
    get_problem_slug,
    scrape_problem,
    validate_leetcode_url,
)


class TestValidateLeetcodeUrl:
    """Tests for validate_leetcode_url function."""

    def test_valid_url_with_trailing_slash(self):
        """Test valid URL with trailing slash."""
        url = "https://leetcode.com/problems/two-sum/"
        assert validate_leetcode_url(url) is True

    def test_valid_url_without_trailing_slash(self):
        """Test valid URL without trailing slash."""
        url = "https://leetcode.com/problems/two-sum"
        assert validate_leetcode_url(url) is True

    def test_valid_url_with_www(self):
        """Test valid URL with www prefix."""
        url = "https://www.leetcode.com/problems/two-sum/"
        assert validate_leetcode_url(url) is True

    def test_valid_url_http(self):
        """Test valid URL with http (not https)."""
        url = "http://leetcode.com/problems/two-sum/"
        assert validate_leetcode_url(url) is True

    def test_invalid_url_wrong_domain(self):
        """Test invalid URL with wrong domain."""
        url = "https://google.com/problems/two-sum/"
        assert validate_leetcode_url(url) is False

    def test_invalid_url_missing_problems(self):
        """Test invalid URL missing /problems/ path."""
        url = "https://leetcode.com/two-sum/"
        assert validate_leetcode_url(url) is False

    def test_invalid_url_empty(self):
        """Test empty URL."""
        assert validate_leetcode_url("") is False

    def test_invalid_url_random_string(self):
        """Test random string."""
        assert validate_leetcode_url("not a url") is False


class TestGetProblemSlug:
    """Tests for get_problem_slug function."""

    def test_extract_slug_basic(self):
        """Test basic slug extraction."""
        url = "https://leetcode.com/problems/two-sum/"
        assert get_problem_slug(url) == "two-sum"

    def test_extract_slug_with_hyphens(self):
        """Test slug extraction with multiple hyphens."""
        url = "https://leetcode.com/problems/longest-substring-without-repeating-characters/"
        assert get_problem_slug(url) == "longest-substring-without-repeating-characters"

    def test_extract_slug_no_trailing_slash(self):
        """Test slug extraction without trailing slash."""
        url = "https://leetcode.com/problems/add-two-numbers"
        assert get_problem_slug(url) == "add-two-numbers"

    def test_extract_slug_invalid_url(self):
        """Test slug extraction from invalid URL."""
        url = "https://google.com/search"
        assert get_problem_slug(url) is None


class TestExtractTestCases:
    """Tests for extract_test_cases function."""

    def test_extract_basic(self):
        """Test basic test case extraction."""
        testcases = "[2,7,11,15]\n9\n[3,2,4]\n6"
        result = extract_test_cases(testcases)
        assert result == ["[2,7,11,15]", "9", "[3,2,4]", "6"]

    def test_extract_empty(self):
        """Test extraction from empty string."""
        assert extract_test_cases("") == []

    def test_extract_with_whitespace(self):
        """Test extraction with extra whitespace."""
        testcases = "  [1,2,3]  \n  5  \n"
        result = extract_test_cases(testcases)
        assert result == ["[1,2,3]", "5"]


class TestGetCodeSnippet:
    """Tests for _get_code_snippet function."""

    def test_default_returns_python3(self, mock_graphql_response):
        """Test default (no language) returns python3 snippet."""
        snippets = mock_graphql_response["data"]["question"]["codeSnippets"]
        result = _get_code_snippet(snippets)
        assert "class Solution" in result

    def test_explicit_python3(self, mock_graphql_response):
        """Test explicit python3 returns python snippet."""
        snippets = mock_graphql_response["data"]["question"]["codeSnippets"]
        result = _get_code_snippet(snippets, language="python3")
        assert "class Solution" in result

    def test_javascript_snippet(self, mock_graphql_response):
        """Test javascript returns JS snippet."""
        snippets = mock_graphql_response["data"]["question"]["codeSnippets"]
        result = _get_code_snippet(snippets, language="javascript")
        assert "var twoSum" in result

    def test_unknown_language_returns_empty(self, mock_graphql_response):
        """Test unknown language returns empty string."""
        snippets = mock_graphql_response["data"]["question"]["codeSnippets"]
        result = _get_code_snippet(snippets, language="haskell")
        assert result == ""

    def test_empty_snippets(self):
        """Test empty snippets list returns empty string."""
        assert _get_code_snippet([]) == ""
        assert _get_code_snippet([], language="python3") == ""


class TestScrapeProblem:
    """Tests for scrape_problem function."""

    def test_scrape_invalid_url(self):
        """Test scraping with invalid URL returns None."""
        result = scrape_problem("https://google.com/test")
        assert result is None

    @patch("algo_atlas.core.scraper._make_request")
    def test_scrape_success(self, mock_request, mock_graphql_response):
        """Test successful problem scraping."""
        mock_request.return_value = mock_graphql_response["data"]["question"]

        result = scrape_problem("https://leetcode.com/problems/two-sum/")

        assert result is not None
        assert result.number == 1
        assert result.title == "Two Sum"
        assert result.difficulty == "Easy"
        assert "Array" in result.topic_tags

    @patch("algo_atlas.core.scraper._make_request")
    def test_scrape_preserves_code_snippets_raw(self, mock_request, mock_graphql_response):
        """Test that scraping preserves raw code snippets."""
        mock_request.return_value = mock_graphql_response["data"]["question"]

        result = scrape_problem("https://leetcode.com/problems/two-sum/")
        assert result is not None
        assert len(result.code_snippets_raw) == 2
        slugs = [s["langSlug"] for s in result.code_snippets_raw]
        assert "python3" in slugs
        assert "javascript" in slugs

    @patch("algo_atlas.core.scraper._make_request")
    def test_scrape_with_language(self, mock_request, mock_graphql_response):
        """Test scraping with explicit language selects correct snippet."""
        mock_request.return_value = mock_graphql_response["data"]["question"]

        result = scrape_problem(
            "https://leetcode.com/problems/two-sum/", language="javascript"
        )
        assert result is not None
        assert "var twoSum" in result.code_snippet

    @patch("algo_atlas.core.scraper._make_request")
    def test_scrape_failure(self, mock_request):
        """Test scraping failure returns None."""
        mock_request.return_value = None

        result = scrape_problem("https://leetcode.com/problems/two-sum/")
        assert result is None
