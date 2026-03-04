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
        hints=[
            "A really brute force way would be to search for all possible pairs of numbers but that would be too slow."
        ],
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
def valid_js_solution():
    """Valid Two Sum solution in JavaScript."""
    return """
var twoSum = function(nums, target) {
    const map = new Map();
    for (let i = 0; i < nums.length; i++) {
        const complement = target - nums[i];
        if (map.has(complement)) {
            return [map.get(complement), i];
        }
        map.set(nums[i], i);
    }
    return [];
};
"""


@pytest.fixture
def invalid_js_syntax():
    """JavaScript code with syntax error."""
    return """
var twoSum = function(nums, target) {
    return [
};
"""


@pytest.fixture
def wrong_js_solution():
    """JavaScript solution that returns wrong results."""
    return """
var twoSum = function(nums, target) {
    return [0, 0];
};
"""


@pytest.fixture
def valid_ts_solution():
    """Valid Two Sum solution in TypeScript."""
    return """
function twoSum(nums: number[], target: number): number[] {
    const map = new Map<number, number>();
    for (let i = 0; i < nums.length; i++) {
        const complement = target - nums[i];
        if (map.has(complement)) {
            return [map.get(complement)!, i];
        }
        map.set(nums[i], i);
    }
    return [];
}
"""


@pytest.fixture
def invalid_ts_syntax():
    """TypeScript code with syntax error."""
    return """
function twoSum(nums: number[] {
    return [];
}
"""


@pytest.fixture
def wrong_ts_solution():
    """TypeScript solution that returns wrong results."""
    return """
function twoSum(nums: number[], target: number): number[] {
    return [0, 0];
}
"""


@pytest.fixture
def valid_java_solution():
    """Valid Two Sum solution in Java."""
    return """
import java.util.*;
class Solution {
    public int[] twoSum(int[] nums, int target) {
        Map<Integer,Integer> map = new HashMap<>();
        for (int i = 0; i < nums.length; i++) {
            int comp = target - nums[i];
            if (map.containsKey(comp)) return new int[]{map.get(comp), i};
            map.put(nums[i], i);
        }
        return new int[]{};
    }
}
"""


@pytest.fixture
def invalid_java_syntax():
    """Java code with syntax error."""
    return """
class Solution {
    public int[] twoSum(int[] nums, int target)
        return new int[]{0, 1};
    }
}
"""


@pytest.fixture
def wrong_java_solution():
    """Java solution that returns wrong results."""
    return """
class Solution {
    public int[] twoSum(int[] nums, int target) {
        return new int[]{0, 0};
    }
}
"""


@pytest.fixture
def valid_c_solution():
    """Valid climbStairs solution in C."""
    return """int climbStairs(int n) {
    if (n <= 2) return n;
    int a = 1, b = 2;
    for (int i = 3; i <= n; i++) {
        int c = a + b;
        a = b;
        b = c;
    }
    return b;
}
"""


@pytest.fixture
def invalid_c_syntax():
    """C code with syntax error."""
    return """int climbStairs(int n) {
    return n
"""


@pytest.fixture
def wrong_c_solution():
    """C solution that returns wrong results."""
    return """int climbStairs(int n) {
    return 0;
}
"""


@pytest.fixture
def valid_go_solution():
    """Valid climbStairs solution in Go."""
    return """func climbStairs(n int) int {
    if n <= 2 {
        return n
    }
    a, b := 1, 2
    for i := 3; i <= n; i++ {
        a, b = b, a+b
    }
    return b
}
"""


@pytest.fixture
def invalid_go_syntax():
    """Go code with syntax error."""
    return """func climbStairs(n int) int {
    return n
"""


@pytest.fixture
def wrong_go_solution():
    """Go solution that returns wrong results."""
    return """func climbStairs(n int) int {
    return 0
}
"""


@pytest.fixture
def valid_rust_solution():
    """Valid climbStairs solution in Rust."""
    return """impl Solution {
    pub fn climb_stairs(n: i32) -> i32 {
        if n <= 2 {
            return n;
        }
        let (mut a, mut b) = (1, 2);
        for _ in 3..=n {
            let c = a + b;
            a = b;
            b = c;
        }
        b
    }
}
"""


@pytest.fixture
def invalid_rust_syntax():
    """Rust code with syntax error."""
    return """impl Solution {
    pub fn climb_stairs(n: i32) -> i32 {
        return n
"""


@pytest.fixture
def wrong_rust_solution():
    """Rust solution that returns wrong results."""
    return """impl Solution {
    pub fn climb_stairs(n: i32) -> i32 {
        0
    }
}
"""


@pytest.fixture
def valid_cpp_solution():
    """Valid Two Sum solution in C++."""
    return """class Solution {
public:
    vector<int> twoSum(vector<int>& nums, int target) {
        unordered_map<int, int> seen;
        for (int i = 0; i < (int)nums.size(); i++) {
            int comp = target - nums[i];
            if (seen.count(comp)) return {seen[comp], i};
            seen[nums[i]] = i;
        }
        return {};
    }
};
"""


@pytest.fixture
def invalid_cpp_syntax():
    """C++ code with syntax error."""
    return """class Solution {
public:
    vector<int> twoSum(vector<int>& nums, int target) {
        return {0, 1}
    }
};
"""


@pytest.fixture
def wrong_cpp_solution():
    """C++ solution that returns wrong results."""
    return """class Solution {
public:
    vector<int> twoSum(vector<int>& nums, int target) {
        return {0, 0};
    }
};
"""


@pytest.fixture
def valid_cs_solution():
    """Valid Two Sum solution in C#."""
    return """\
class Solution {
    public int[] TwoSum(int[] nums, int target) {
        var map = new Dictionary<int, int>();
        for (int i = 0; i < nums.Length; i++) {
            int comp = target - nums[i];
            if (map.ContainsKey(comp)) return new int[] { map[comp], i };
            map[nums[i]] = i;
        }
        return new int[]{};
    }
}
"""


@pytest.fixture
def invalid_cs_syntax():
    """C# code with syntax error."""
    return """\
class Solution {
    public int[] TwoSum(int[] nums, int target)
        return new int[]{0, 1};
    }
}
"""


@pytest.fixture
def wrong_cs_solution():
    """C# solution that returns wrong results."""
    return """\
class Solution {
    public int[] TwoSum(int[] nums, int target) {
        return new int[]{0, 0};
    }
}
"""


@pytest.fixture
def valid_kotlin_solution():
    """Valid Two Sum solution in Kotlin."""
    return """\
class Solution {
    fun twoSum(nums: IntArray, target: Int): IntArray {
        val map = HashMap<Int, Int>()
        for (i in nums.indices) {
            val comp = target - nums[i]
            if (map.containsKey(comp)) return intArrayOf(map[comp]!!, i)
            map[nums[i]] = i
        }
        return intArrayOf()
    }
}
"""


@pytest.fixture
def invalid_kotlin_syntax():
    """Kotlin code with syntax error."""
    return """\
class Solution {
    fun twoSum(nums: IntArray, target: Int): IntArray
        return intArrayOf(0, 1)
    }
}
"""


@pytest.fixture
def wrong_kotlin_solution():
    """Kotlin solution that returns wrong results."""
    return """\
class Solution {
    fun twoSum(nums: IntArray, target: Int): IntArray {
        return intArrayOf(0, 0)
    }
}
"""


@pytest.fixture
def valid_swift_solution():
    """Valid Two Sum solution in Swift."""
    return """\
class Solution {
    func twoSum(_ nums: [Int], _ target: Int) -> [Int] {
        var map = [Int: Int]()
        for (i, num) in nums.enumerated() {
            if let j = map[target - num] { return [j, i] }
            map[num] = i
        }
        return []
    }
}
"""


@pytest.fixture
def invalid_swift_syntax():
    """Swift code with syntax error."""
    return """\
class Solution {
    func twoSum(_ nums: [Int], _ target: Int) -> [Int]
        return [0, 1]
    }
}
"""


@pytest.fixture
def wrong_swift_solution():
    """Swift solution that returns wrong results."""
    return """\
class Solution {
    func twoSum(_ nums: [Int], _ target: Int) -> [Int] {
        return [0, 0]
    }
}
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
                    {
                        "lang": "TypeScript",
                        "langSlug": "typescript",
                        "code": "function twoSum(nums: number[], target: number): number[] {\n    \n};",
                    },
                    {
                        "lang": "Java",
                        "langSlug": "java",
                        "code": "class Solution {\n    public int[] twoSum(int[] nums, int target) {\n        \n    }\n}",
                    },
                    {
                        "lang": "C++",
                        "langSlug": "cpp",
                        "code": "class Solution {\npublic:\n    vector<int> twoSum(vector<int>& nums, int target) {\n        \n    }\n};",
                    },
                    {
                        "lang": "C",
                        "langSlug": "c",
                        "code": "int* twoSum(int* nums, int numsSize, int target, int* returnSize) {\n    \n}",
                    },
                    {
                        "lang": "Go",
                        "langSlug": "golang",
                        "code": "func twoSum(nums []int, target int) []int {\n    \n}",
                    },
                    {
                        "lang": "Rust",
                        "langSlug": "rust",
                        "code": "impl Solution {\n    pub fn two_sum(nums: Vec<i32>, target: i32) -> Vec<i32> {\n        \n    }\n}",
                    },
                    {
                        "lang": "C#",
                        "langSlug": "csharp",
                        "code": "public class Solution {\n    public int[] TwoSum(int[] nums, int target) {\n        \n    }\n}",
                    },
                    {
                        "lang": "Kotlin",
                        "langSlug": "kotlin",
                        "code": "class Solution {\n    fun twoSum(nums: IntArray, target: Int): IntArray {\n        \n    }\n}",
                    },
                    {
                        "lang": "Swift",
                        "langSlug": "swift",
                        "code": "class Solution {\n    func twoSum(_ nums: [Int], _ target: Int) -> [Int] {\n        \n    }\n}",
                    },
                ],
                "topicTags": [
                    {"name": "Array", "slug": "array"},
                    {"name": "Hash Table", "slug": "hash-table"},
                ],
                "hints": [
                    "A really brute force way would be to search for all possible pairs."
                ],
            }
        }
    }
