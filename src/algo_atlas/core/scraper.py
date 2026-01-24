"""LeetCode problem scraper using GraphQL API."""

import random
import re
import time
from dataclasses import dataclass
from typing import Optional
from html import unescape

import requests

from algo_atlas.config.settings import get_settings

# LeetCode GraphQL endpoint
LEETCODE_GRAPHQL_URL = "https://leetcode.com/graphql"

# User agents for rotation
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

# GraphQL query for problem details
PROBLEM_QUERY = """
query getProblem($titleSlug: String!) {
    question(titleSlug: $titleSlug) {
        questionId
        questionFrontendId
        title
        titleSlug
        difficulty
        content
        exampleTestcases
        codeSnippets {
            lang
            langSlug
            code
        }
        topicTags {
            name
            slug
        }
        hints
    }
}
"""


@dataclass
class ProblemData:
    """Container for scraped problem data."""

    number: int
    title: str
    slug: str
    difficulty: str
    description: str
    examples: list[dict]
    constraints: list[str]
    test_cases: list[str]
    code_snippet: str
    topic_tags: list[str]
    hints: list[str]


def validate_leetcode_url(url: str) -> bool:
    """Validate if URL is a valid LeetCode problem URL.

    Args:
        url: URL to validate.

    Returns:
        True if valid LeetCode problem URL, False otherwise.
    """
    pattern = r"^https?://(www\.)?leetcode\.com/problems/[\w-]+/?$"
    return bool(re.match(pattern, url))


def get_problem_slug(url: str) -> Optional[str]:
    """Extract problem slug from LeetCode URL.

    Args:
        url: LeetCode problem URL.

    Returns:
        Problem slug if valid URL, None otherwise.
    """
    pattern = r"leetcode\.com/problems/([\w-]+)"
    match = re.search(pattern, url)
    return match.group(1) if match else None


def _get_random_user_agent() -> str:
    """Get a random user agent for request rotation."""
    return random.choice(USER_AGENTS)


def _make_request(
    slug: str,
    timeout: int = 30,
    max_retries: int = 3,
    retry_delay: int = 2,
) -> Optional[dict]:
    """Make GraphQL request with retry logic and exponential backoff.

    Args:
        slug: Problem slug.
        timeout: Request timeout in seconds.
        max_retries: Maximum retry attempts.
        retry_delay: Base delay between retries in seconds.

    Returns:
        Response data dict if successful, None otherwise.
    """
    headers = {
        "Content-Type": "application/json",
        "User-Agent": _get_random_user_agent(),
        "Referer": f"https://leetcode.com/problems/{slug}/",
    }

    payload = {
        "query": PROBLEM_QUERY,
        "variables": {"titleSlug": slug},
    }

    for attempt in range(max_retries):
        try:
            response = requests.post(
                LEETCODE_GRAPHQL_URL,
                json=payload,
                headers=headers,
                timeout=timeout,
            )
            response.raise_for_status()

            data = response.json()
            if "errors" in data:
                return None

            return data.get("data", {}).get("question")

        except requests.RequestException:
            if attempt < max_retries - 1:
                # Exponential backoff
                wait_time = retry_delay * (2 ** attempt)
                time.sleep(wait_time)
            continue

    return None


def _parse_html_content(html: str) -> tuple[str, list[dict], list[str]]:
    """Parse HTML content to extract description, examples, and constraints.

    Args:
        html: Raw HTML content from LeetCode.

    Returns:
        Tuple of (description, examples, constraints).
    """
    # Unescape HTML entities
    html = unescape(html)

    # Remove HTML tags for plain text description
    description = re.sub(r"<[^>]+>", "", html)
    description = re.sub(r"\n{3,}", "\n\n", description)
    description = description.strip()

    # Extract examples
    examples = []
    example_pattern = r"Example\s*(\d+)[:\s]*(.*?)(?=Example\s*\d+|Constraints|$)"
    example_matches = re.findall(example_pattern, html, re.DOTALL | re.IGNORECASE)

    for num, content in example_matches:
        # Clean up the content
        content = re.sub(r"<[^>]+>", "", content)
        content = content.strip()

        # Try to extract input/output
        input_match = re.search(r"Input:\s*(.+?)(?=Output:|$)", content, re.DOTALL)
        output_match = re.search(r"Output:\s*(.+?)(?=Explanation:|$)", content, re.DOTALL)
        explanation_match = re.search(r"Explanation:\s*(.+?)$", content, re.DOTALL)

        example = {
            "number": int(num),
            "input": input_match.group(1).strip() if input_match else "",
            "output": output_match.group(1).strip() if output_match else "",
            "explanation": explanation_match.group(1).strip() if explanation_match else "",
        }
        examples.append(example)

    # Extract constraints
    constraints = []
    constraint_pattern = r"Constraints:</strong></p>\s*<ul>(.*?)</ul>"
    constraint_match = re.search(constraint_pattern, html, re.DOTALL)

    if constraint_match:
        constraint_items = re.findall(r"<li>(.*?)</li>", constraint_match.group(1))
        for item in constraint_items:
            # Clean HTML and decode entities
            clean = re.sub(r"<[^>]+>", "", item)
            clean = clean.strip()
            if clean:
                constraints.append(clean)

    return description, examples, constraints


def extract_test_cases(example_testcases: str) -> list[str]:
    """Extract test cases from LeetCode example testcases string.

    Args:
        example_testcases: Raw testcases string from GraphQL response.

    Returns:
        List of individual test case strings.
    """
    if not example_testcases:
        return []

    # Split by newlines and filter empty lines
    cases = [case.strip() for case in example_testcases.strip().split("\n") if case.strip()]
    return cases


def _get_python_snippet(code_snippets: list[dict]) -> str:
    """Extract Python3 code snippet from available snippets.

    Args:
        code_snippets: List of code snippet dicts.

    Returns:
        Python3 code snippet or empty string.
    """
    for snippet in code_snippets:
        if snippet.get("langSlug") == "python3":
            return snippet.get("code", "")

    # Fallback to python if python3 not available
    for snippet in code_snippets:
        if snippet.get("langSlug") == "python":
            return snippet.get("code", "")

    return ""


def scrape_problem(url: str) -> Optional[ProblemData]:
    """Scrape LeetCode problem data from URL.

    Args:
        url: LeetCode problem URL.

    Returns:
        ProblemData if successful, None otherwise.
    """
    if not validate_leetcode_url(url):
        return None

    slug = get_problem_slug(url)
    if not slug:
        return None

    settings = get_settings()
    data = _make_request(
        slug=slug,
        timeout=settings.leetcode.timeout,
        max_retries=settings.leetcode.max_retries,
        retry_delay=settings.leetcode.retry_delay,
    )

    if not data:
        return None

    # Parse content
    content = data.get("content", "") or ""
    description, examples, constraints = _parse_html_content(content)

    # Extract other fields
    code_snippets = data.get("codeSnippets", []) or []
    topic_tags = [tag.get("name", "") for tag in (data.get("topicTags", []) or [])]
    hints = data.get("hints", []) or []
    test_cases = extract_test_cases(data.get("exampleTestcases", ""))

    return ProblemData(
        number=int(data.get("questionFrontendId", 0)),
        title=data.get("title", ""),
        slug=data.get("titleSlug", slug),
        difficulty=data.get("difficulty", ""),
        description=description,
        examples=examples,
        constraints=constraints,
        test_cases=test_cases,
        code_snippet=_get_python_snippet(code_snippets),
        topic_tags=topic_tags,
        hints=hints,
    )
