"""Core modules for AlgoAtlas."""

from algo_atlas.core.generator import (
    GenerationResult,
    build_readme_content,
    call_claude,
    check_claude_installed,
    generate_documentation,
    generate_expected_outputs,
)
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
    "GenerationResult",
    "check_claude_installed",
    "call_claude",
    "generate_documentation",
    "generate_expected_outputs",
    "build_readme_content",
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
