"""Tests for the solution verifier module."""

from algo_atlas.core.verifier import (
    check_syntax,
    run_test_case,
    verify_solution,
)


class TestCheckSyntax:
    """Tests for check_syntax function."""

    def test_valid_syntax(self, valid_solution):
        """Test valid Python syntax."""
        result = check_syntax(valid_solution)
        assert result.valid is True
        assert result.error_message is None

    def test_invalid_syntax(self, invalid_syntax_solution):
        """Test invalid Python syntax."""
        result = check_syntax(invalid_syntax_solution)
        assert result.valid is False
        assert result.error_message is not None
        assert result.error_line is not None

    def test_empty_code(self):
        """Test empty code string."""
        result = check_syntax("")
        assert result.valid is True

    def test_simple_valid_code(self):
        """Test simple valid code."""
        code = "x = 1\ny = 2\nprint(x + y)"
        result = check_syntax(code)
        assert result.valid is True

    def test_missing_colon(self):
        """Test missing colon in function definition."""
        code = "def foo()\n    pass"
        result = check_syntax(code)
        assert result.valid is False


class TestRunTestCase:
    """Tests for run_test_case function."""

    def test_passing_test(self, valid_solution):
        """Test a passing test case."""
        result = run_test_case(
            solution_code=valid_solution,
            input_args=[[2, 7, 11, 15], 9],
            expected_output=[0, 1],
        )
        assert result.passed is True
        assert result.actual == [0, 1]
        assert result.error is None

    def test_failing_test(self, wrong_solution):
        """Test a failing test case."""
        result = run_test_case(
            solution_code=wrong_solution,
            input_args=[[2, 7, 11, 15], 9],
            expected_output=[0, 1],
        )
        assert result.passed is False
        assert result.actual == [0, 0]

    def test_syntax_error(self, invalid_syntax_solution):
        """Test with syntax error in solution."""
        result = run_test_case(
            solution_code=invalid_syntax_solution,
            input_args=[[1, 2], 3],
            expected_output=[0, 1],
        )
        assert result.passed is False
        assert result.error is not None

    def test_missing_solution_class(self):
        """Test with missing Solution class."""
        code = "def twoSum(nums, target): return [0, 1]"
        result = run_test_case(
            solution_code=code,
            input_args=[[1, 2], 3],
            expected_output=[0, 1],
        )
        assert result.passed is False
        assert "Solution" in result.error

    def test_list_order_comparison(self, valid_solution):
        """Test that list order matters for comparison."""
        result = run_test_case(
            solution_code=valid_solution,
            input_args=[[2, 7, 11, 15], 9],
            expected_output=[1, 0],  # Reversed order
        )
        # Should pass because we compare sorted lists
        assert result.passed is True


class TestExecNamespace:
    """Tests for solution execution with typing annotations."""

    def test_solution_with_list_annotation(self):
        """Test solution using List[int] without explicit import."""
        code = """class Solution:
    def twoSum(self, nums: List[int], target: int) -> List[int]:
        seen = {}
        for i, n in enumerate(nums):
            if target - n in seen:
                return [seen[target - n], i]
            seen[n] = i
"""
        result = run_test_case(
            solution_code=code,
            input_args=[[2, 7, 11, 15], 9],
            expected_output=[0, 1],
        )
        assert result.passed is True
        assert result.error is None

    def test_solution_with_optional_annotation(self):
        """Test solution using Optional without explicit import."""
        code = """class Solution:
    def twoSum(self, nums: List[int], target: int) -> Optional[List[int]]:
        seen = {}
        for i, n in enumerate(nums):
            if target - n in seen:
                return [seen[target - n], i]
            seen[n] = i
        return None
"""
        result = run_test_case(
            solution_code=code,
            input_args=[[2, 7, 11, 15], 9],
            expected_output=[0, 1],
        )
        assert result.passed is True

    def test_solution_with_dict_annotation(self):
        """Test solution using Dict without explicit import."""
        code = """class Solution:
    def twoSum(self, nums: List[int], target: int) -> List[int]:
        seen: Dict[int, int] = {}
        for i, n in enumerate(nums):
            if target - n in seen:
                return [seen[target - n], i]
            seen[n] = i
"""
        result = run_test_case(
            solution_code=code,
            input_args=[[2, 7, 11, 15], 9],
            expected_output=[0, 1],
        )
        assert result.passed is True

    def test_solution_with_defaultdict(self):
        """Test solution using defaultdict without explicit import."""
        code = """class Solution:
    def groupAnagrams(self, strs: List[str]) -> List[List[str]]:
        groups = defaultdict(list)
        for s in strs:
            key = ''.join(sorted(s))
            groups[key].append(s)
        return list(groups.values())
"""
        result = run_test_case(
            solution_code=code,
            input_args=[["eat", "tea", "ate"]],
            expected_output=[["eat", "tea", "ate"]],
        )
        assert result.passed is True

    def test_solution_with_deque(self):
        """Test solution using deque without explicit import."""
        code = """class Solution:
    def maxSlidingWindow(self, nums: List[int], k: int) -> List[int]:
        q = deque()
        result = []
        for i, n in enumerate(nums):
            while q and nums[q[-1]] <= n:
                q.pop()
            q.append(i)
            if q[0] == i - k:
                q.popleft()
            if i >= k - 1:
                result.append(nums[q[0]])
        return result
"""
        result = run_test_case(
            solution_code=code,
            input_args=[[1, 3, -1, -3, 5, 3, 6, 7], 3],
            expected_output=[3, 3, 5, 5, 6, 7],
        )
        assert result.passed is True

    def test_solution_with_inf(self):
        """Test solution using inf without explicit import."""
        code = """class Solution:
    def minCost(self, nums: List[int]) -> int:
        best = inf
        for n in nums:
            if n < best:
                best = n
        return best
"""
        result = run_test_case(
            solution_code=code,
            input_args=[[3, 1, 2]],
            expected_output=1,
        )
        assert result.passed is True


class TestVerifySolution:
    """Tests for verify_solution function."""

    def test_all_tests_pass(self, valid_solution, sample_problem):
        """Test verification with all passing tests."""
        result = verify_solution(
            solution_code=valid_solution,
            test_cases=sample_problem.test_cases,
            examples=sample_problem.examples,
        )
        assert result.syntax_valid is True
        assert result.all_passed is True
        assert result.tests_passed == result.tests_run

    def test_syntax_error(self, invalid_syntax_solution, sample_problem):
        """Test verification with syntax error."""
        result = verify_solution(
            solution_code=invalid_syntax_solution,
            test_cases=sample_problem.test_cases,
            examples=sample_problem.examples,
        )
        assert result.syntax_valid is False
        assert result.syntax_error is not None

    def test_some_tests_fail(self, wrong_solution, sample_problem):
        """Test verification with failing tests."""
        result = verify_solution(
            solution_code=wrong_solution,
            test_cases=sample_problem.test_cases,
            examples=sample_problem.examples,
        )
        assert result.syntax_valid is True
        assert result.all_passed is False
        assert result.tests_passed < result.tests_run

    def test_empty_examples(self, valid_solution):
        """Test verification with no examples."""
        result = verify_solution(
            solution_code=valid_solution,
            test_cases=[],
            examples=[],
        )
        assert result.syntax_valid is True
        assert result.tests_run == 0

    def test_with_expected_outputs(self, valid_solution, sample_problem):
        """Test verification with AI-provided expected outputs."""
        expected_outputs = [[0, 1], [1, 2], [0, 1]]
        result = verify_solution(
            solution_code=valid_solution,
            test_cases=sample_problem.test_cases,
            examples=sample_problem.examples,
            expected_outputs=expected_outputs,
        )
        assert result.syntax_valid is True
        assert result.tests_passed > 0
