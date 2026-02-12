"""Pytest fixtures for AlgoAtlas tests."""

import pytest

from algo_atlas.core.scraper import ProblemData


@pytest.fixture
def sample_problem():
    """Sample problem data for testing."""
    return ProblemData(
        number=1,
        title="Two Sum",
        slug="two-sum",
        difficulty="Easy",
        description="Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target.",
        examples=[
            {
                "number": 1,
                "input": "[2,7,11,15]\n9",
                "output": "[0,1]",
                "explanation": "Because nums[0] + nums[1] == 9, we return [0, 1].",
            },
            {
                "number": 2,
                "input": "[3,2,4]\n6",
                "output": "[1,2]",
                "explanation": "",
            },
            {
                "number": 3,
                "input": "[3,3]\n6",
                "output": "[0,1]",
                "explanation": "",
            },
        ],
        constraints=[
            "2 <= nums.length <= 10^4",
            "-10^9 <= nums[i] <= 10^9",
            "-10^9 <= target <= 10^9",
            "Only one valid answer exists.",
        ],
        test_cases=["[2,7,11,15]", "9", "[3,2,4]", "6", "[3,3]", "6"],
        code_snippet="class Solution:\n    def twoSum(self, nums: List[int], target: int) -> List[int]:\n        pass",
        topic_tags=["Array", "Hash Table"],
        hints=["A really brute force way would be to search for all possible pairs of numbers but that would be too slow."],
    )


@pytest.fixture
def valid_solution():
    """Valid Two Sum solution."""
    return """
class Solution:
    def twoSum(self, nums, target):
        seen = {}
        for i, n in enumerate(nums):
            if target - n in seen:
                return [seen[target - n], i]
            seen[n] = i
"""


@pytest.fixture
def invalid_syntax_solution():
    """Solution with syntax error."""
    return """
class Solution:
    def twoSum(self, nums, target)
        return []
"""


@pytest.fixture
def wrong_solution():
    """Solution that returns wrong results."""
    return """
class Solution:
    def twoSum(self, nums, target):
        return [0, 0]
"""


@pytest.fixture
def temp_vault(tmp_path):
    """Create a temporary vault directory structure."""
    vault = tmp_path / "test-vault"
    vault.mkdir()
    (vault / "Easy").mkdir()
    (vault / "Medium").mkdir()
    (vault / "Hard").mkdir()
    return vault


@pytest.fixture
def mock_graphql_response():
    """Mock GraphQL response for Two Sum problem."""
    return {
        "data": {
            "question": {
                "questionId": "1",
                "questionFrontendId": "1",
                "title": "Two Sum",
                "titleSlug": "two-sum",
                "difficulty": "Easy",
                "content": '<p>Given an array of integers <code>nums</code>&nbsp;and an integer <code>target</code>, return <em>indices of the two numbers such that they add up to <code>target</code></em>.</p>\n\n<p><strong class="example">Example 1:</strong></p>\n<pre><strong>Input:</strong> nums = [2,7,11,15], target = 9\n<strong>Output:</strong> [0,1]\n<strong>Explanation:</strong> Because nums[0] + nums[1] == 9, we return [0, 1].</pre>',
                "exampleTestcases": "[2,7,11,15]\n9\n[3,2,4]\n6\n[3,3]\n6",
                "codeSnippets": [
                    {
                        "lang": "Python3",
                        "langSlug": "python3",
                        "code": "class Solution:\n    def twoSum(self, nums: List[int], target: int) -> List[int]:\n        pass",
                    },
                    {
                        "lang": "JavaScript",
                        "langSlug": "javascript",
                        "code": "/**\n * @param {number[]} nums\n * @param {number} target\n * @return {number[]}\n */\nvar twoSum = function(nums, target) {\n    \n};",
                    },
                ],
                "topicTags": [
                    {"name": "Array", "slug": "array"},
                    {"name": "Hash Table", "slug": "hash-table"},
                ],
                "hints": ["A really brute force way would be to search for all possible pairs."],
            }
        }
    }
