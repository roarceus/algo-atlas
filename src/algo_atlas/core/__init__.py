"""Core modules for AlgoAtlas."""

from algo_atlas.core.scraper import (
    ProblemData,
    extract_test_cases,
    get_problem_slug,
    scrape_problem,
    validate_leetcode_url,
)
from algo_atlas.core.verifier import (
    SyntaxResult,
    TestResult,
    VerificationResult,
    check_syntax,
    run_test_case,
    run_test_cases,
    verify_solution,
)

__all__ = [
    "ProblemData",
    "validate_leetcode_url",
    "get_problem_slug",
    "scrape_problem",
    "extract_test_cases",
    "SyntaxResult",
    "TestResult",
    "VerificationResult",
    "check_syntax",
    "run_test_case",
    "run_test_cases",
    "verify_solution",
]
