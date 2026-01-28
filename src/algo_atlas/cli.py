"""Command-line interface for AlgoAtlas."""

import sys
from pathlib import Path
from typing import Optional

from algo_atlas.config.settings import get_settings, reload_settings
from algo_atlas.core.generator import (
    build_readme_content,
    check_claude_installed,
    generate_documentation,
    generate_expected_outputs,
)
from algo_atlas.core.scraper import ProblemData, scrape_problem, validate_leetcode_url
from algo_atlas.core.verifier import verify_solution
from algo_atlas.utils.file_manager import (
    check_problem_exists,
    create_problem_folder,
    save_markdown,
    save_solution_file,
    validate_vault_repo,
)
from algo_atlas.utils.logger import get_logger


def startup_checks(logger) -> tuple[bool, Optional[Path]]:
    """Run startup checks for vault and Claude CLI.

    Args:
        logger: Logger instance.

    Returns:
        Tuple of (all_checks_passed, vault_path).
    """
    logger.header("AlgoAtlas")
    logger.info("Running startup checks...")
    logger.blank()

    all_passed = True
    vault_path = None

    # Check Claude CLI
    if check_claude_installed():
        logger.success("Claude CLI installed")
    else:
        logger.error("Claude CLI not found")
        logger.info("Install with: npm install -g @anthropic-ai/claude-code")
        all_passed = False

    # Check vault configuration
    settings = get_settings()
    if settings.vault_path:
        vault_path = Path(settings.vault_path)
        if validate_vault_repo(vault_path):
            logger.success(f"Vault configured: {vault_path}")
        else:
            logger.error(f"Vault path invalid: {vault_path}")
            logger.info("Ensure Easy/, Medium/, Hard/ directories exist")
            all_passed = False
    else:
        logger.error("Vault path not configured")
        logger.info("Set vault_path in config/config.yaml")
        all_passed = False

    logger.blank()
    return all_passed, vault_path


def get_leetcode_url(logger) -> Optional[str]:
    """Prompt user for LeetCode URL.

    Args:
        logger: Logger instance.

    Returns:
        Valid LeetCode URL or None if user quits.
    """
    while True:
        url = logger.prompt("Enter LeetCode problem URL (or 'q' to quit)")

        if url.lower() in ("q", "quit", "exit"):
            return None

        if validate_leetcode_url(url):
            return url

        logger.error("Invalid LeetCode URL format")
        logger.info("Example: https://leetcode.com/problems/two-sum/")


def get_solution_code(logger) -> Optional[str]:
    """Get solution code from user (file path or paste).

    Args:
        logger: Logger instance.

    Returns:
        Solution code string or None if cancelled.
    """
    logger.blank()
    logger.info("Enter solution code:")
    logger.info("  - Paste a file path (e.g., solution.py)")
    logger.info("  - Or paste code directly, then enter 'END' on a new line")
    logger.blank()

    first_line = input().strip()

    # Check if it's a file path
    if first_line.endswith(".py") or Path(first_line).exists():
        path = Path(first_line)
        if path.exists():
            try:
                code = path.read_text(encoding="utf-8")
                logger.success(f"Loaded from: {path}")
                return code
            except Exception as e:
                logger.error(f"Failed to read file: {e}")
                return None
        else:
            logger.error(f"File not found: {path}")
            return None

    # Collect pasted code
    lines = [first_line]
    while True:
        line = input()
        if line.strip().upper() == "END":
            break
        lines.append(line)

    code = "\n".join(lines)
    if code.strip():
        logger.success("Code received")
        return code

    logger.error("No code provided")
    return None


def scrape_problem_with_progress(logger, url: str) -> Optional[ProblemData]:
    """Scrape problem with progress indication.

    Args:
        logger: Logger instance.
        url: LeetCode problem URL.

    Returns:
        ProblemData or None if failed.
    """
    logger.blank()
    logger.step("Scraping problem from LeetCode...")

    problem = scrape_problem(url)

    if problem:
        logger.success(f"Found: {problem.number}. {problem.title} ({problem.difficulty})")
        logger.info(f"Topics: {', '.join(problem.topic_tags)}")
        return problem
    else:
        logger.error("Failed to scrape problem")
        logger.info("Check URL and try again")
        return None


def verify_solution_with_progress(
    logger,
    solution_code: str,
    problem: ProblemData,
) -> bool:
    """Verify solution with progress indication.

    Args:
        logger: Logger instance.
        solution_code: Python solution code.
        problem: Scraped problem data.

    Returns:
        True if verification passed, False otherwise.
    """
    logger.blank()
    logger.step("Verifying solution...")

    # Try to get expected outputs from Claude for additional test cases
    expected_outputs = None
    if problem.test_cases:
        logger.info("Generating expected outputs for test cases...")
        expected_outputs = generate_expected_outputs(problem, problem.test_cases)

    result = verify_solution(
        solution_code,
        problem.test_cases,
        problem.examples,
        expected_outputs,
    )

    if not result.syntax_valid:
        logger.error(f"Syntax error: {result.syntax_error}")
        return False

    logger.success(f"Syntax valid")

    if result.tests_run > 0:
        if result.all_passed:
            logger.success(f"All tests passed ({result.tests_passed}/{result.tests_run})")
        else:
            logger.warning(f"Tests: {result.tests_passed}/{result.tests_run} passed")
            for i, tr in enumerate(result.test_results):
                if not tr.passed:
                    logger.error(f"  Test {i+1}: expected {tr.expected}, got {tr.actual}")
                    if tr.error:
                        logger.error(f"    Error: {tr.error}")

    return result.syntax_valid


def generate_docs_with_progress(
    logger,
    problem: ProblemData,
    solution_code: str,
) -> Optional[str]:
    """Generate documentation with progress indication.

    Args:
        logger: Logger instance.
        problem: Problem data.
        solution_code: Solution code.

    Returns:
        Generated markdown or None if failed.
    """
    logger.blank()
    logger.step("Generating documentation with Claude...")

    result = generate_documentation(problem, solution_code)

    if result.success and result.content:
        logger.success("Documentation generated")
        return build_readme_content(problem, result.content)
    else:
        logger.error(f"Generation failed: {result.error}")
        return None


def save_to_vault(
    logger,
    vault_path: Path,
    problem: ProblemData,
    solution_code: str,
    documentation: str,
) -> bool:
    """Save solution and documentation to vault.

    Args:
        logger: Logger instance.
        vault_path: Path to vault.
        problem: Problem data.
        solution_code: Solution code.
        documentation: Generated documentation.

    Returns:
        True if saved successfully.
    """
    logger.blank()
    logger.step("Saving to vault...")

    # Check if problem already exists
    existing = check_problem_exists(vault_path, problem.number)
    if existing:
        logger.warning(f"Problem already exists: {existing}")
        if not logger.confirm("Overwrite existing files?", default=False):
            logger.info("Skipped saving")
            return False

    # Create problem folder
    folder = create_problem_folder(
        vault_path,
        problem.number,
        problem.title,
        problem.difficulty,
    )

    if not folder:
        logger.error("Failed to create problem folder")
        return False

    # Save solution
    if save_solution_file(folder, solution_code):
        logger.success(f"Saved: {folder / 'solution.py'}")
    else:
        logger.error("Failed to save solution.py")
        return False

    # Save documentation
    if save_markdown(folder, documentation):
        logger.success(f"Saved: {folder / 'README.md'}")
    else:
        logger.error("Failed to save README.md")
        return False

    logger.blank()
    logger.success(f"Problem saved to: {folder}")
    return True


def run_workflow(logger, vault_path: Path) -> bool:
    """Run the main workflow for one problem.

    Args:
        logger: Logger instance.
        vault_path: Path to vault.

    Returns:
        True if workflow completed successfully.
    """
    # Get URL
    url = get_leetcode_url(logger)
    if not url:
        return False

    # Scrape problem
    problem = scrape_problem_with_progress(logger, url)
    if not problem:
        return False

    # Get solution code
    solution_code = get_solution_code(logger)
    if not solution_code:
        return False

    # Verify solution
    if not verify_solution_with_progress(logger, solution_code, problem):
        if not logger.confirm("Continue despite verification issues?", default=False):
            return False

    # Generate documentation
    documentation = generate_docs_with_progress(logger, problem, solution_code)
    if not documentation:
        if not logger.confirm("Save without documentation?", default=False):
            return False
        documentation = f"# {problem.number}. {problem.title}\n\nDocumentation pending."

    # Save to vault
    save_to_vault(logger, vault_path, problem, solution_code, documentation)

    return True


def main():
    """Main entry point for AlgoAtlas CLI."""
    logger = get_logger()

    # Run startup checks
    checks_passed, vault_path = startup_checks(logger)

    if not checks_passed:
        logger.error("Startup checks failed. Please fix issues above.")
        sys.exit(1)

    # Main loop
    while True:
        try:
            run_workflow(logger, vault_path)

            logger.blank()
            if not logger.confirm("Process another problem?", default=True):
                break

            logger.blank()

        except KeyboardInterrupt:
            logger.blank()
            logger.info("Interrupted")
            break

    logger.blank()
    logger.info("Goodbye!")


if __name__ == "__main__":
    main()
