"""Command-line interface for AlgoAtlas."""

import argparse
import sys
from pathlib import Path
from typing import Optional

from algo_atlas.config.settings import get_settings
from algo_atlas.core.generator import (
    build_readme_content,
    check_claude_installed,
    generate_documentation,
    generate_expected_outputs,
)
from algo_atlas.core.scraper import ProblemData, scrape_problem, validate_leetcode_url
from algo_atlas.core.verifier import verify_solution
from algo_atlas.utils.file_manager import (
    check_gh_installed,
    check_problem_exists,
    checkout_main,
    commit_changes,
    create_and_checkout_branch,
    create_problem_folder,
    create_pull_request,
    ensure_labels_exist,
    generate_branch_name,
    get_pr_labels,
    list_all_topics,
    push_branch,
    save_markdown,
    save_solution_file,
    search_problems,
    stage_files,
    update_vault_readme,
    validate_vault_repo,
)
from algo_atlas.utils.logger import get_logger


def startup_checks(logger, dry_run: bool = False) -> tuple[bool, Optional[Path]]:
    """Run startup checks for vault and Claude CLI.

    Args:
        logger: Logger instance.
        dry_run: If True, skip vault checks.

    Returns:
        Tuple of (all_checks_passed, vault_path).
    """
    logger.header("AlgoAtlas")
    if dry_run:
        logger.info("DRY RUN MODE - No files will be saved")
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

    # Check vault configuration (skip in dry-run mode)
    if dry_run:
        logger.info("Vault check skipped (dry-run mode)")
    else:
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

    logger.success("Syntax valid")

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
    leetcode_url: str,
) -> bool:
    """Save solution and documentation to vault with git workflow.

    Creates a new branch, saves files, commits, pushes, and creates PR.

    Args:
        logger: Logger instance.
        vault_path: Path to vault.
        problem: Problem data.
        solution_code: Solution code.
        documentation: Generated documentation.
        leetcode_url: URL to the LeetCode problem.

    Returns:
        True if saved successfully.
    """
    logger.blank()
    logger.step("Saving to vault...")

    # Check if problem already exists (used for labels and info)
    existing = check_problem_exists(vault_path, problem.number)
    is_new_solution = existing is None
    if existing:
        logger.info(f"Note: Problem exists at {existing}")
        logger.info("Creating new branch for alternative solution...")

    # Generate and create branch
    branch_name = generate_branch_name(problem.number, problem.title)
    logger.step(f"Creating branch: {branch_name}")

    success, msg = create_and_checkout_branch(vault_path, branch_name)
    if not success:
        logger.error(msg)
        return False
    logger.success(msg)

    # Create problem folder
    folder = create_problem_folder(
        vault_path,
        problem.number,
        problem.title,
        problem.difficulty,
    )

    if not folder:
        logger.error("Failed to create problem folder")
        checkout_main(vault_path)
        return False

    # Save solution
    solution_path = folder / "solution.py"
    if save_solution_file(folder, solution_code):
        logger.success(f"Saved: {solution_path}")
    else:
        logger.error("Failed to save solution.py")
        checkout_main(vault_path)
        return False

    # Save documentation
    readme_path = folder / "README.md"
    if save_markdown(folder, documentation):
        logger.success(f"Saved: {readme_path}")
    else:
        logger.error("Failed to save README.md")
        checkout_main(vault_path)
        return False

    # Update vault stats
    vault_readme_path = vault_path / "README.md"
    success, msg = update_vault_readme(vault_path)
    if success:
        logger.success(msg)
    else:
        logger.warning(msg)

    # Stage files (include vault README if it exists)
    files_to_stage = [solution_path, readme_path]
    if vault_readme_path.exists():
        files_to_stage.append(vault_readme_path)
    success, msg = stage_files(vault_path, files_to_stage)
    if not success:
        logger.error(msg)
        checkout_main(vault_path)
        return False

    # Commit changes
    success, msg = commit_changes(vault_path, problem.number, problem.title)
    if not success:
        logger.error(msg)
        checkout_main(vault_path)
        return False
    logger.success(msg)

    # Push branch
    logger.step("Pushing to remote...")
    push_success, msg = push_branch(vault_path, branch_name)
    if not push_success:
        logger.error(msg)
        logger.info("Files saved locally. Push manually with:")
        logger.info(f"  cd {vault_path} && git push -u origin {branch_name}")
    else:
        logger.success(msg)

    # Switch back to main
    checkout_main(vault_path)

    # Create PR if push was successful and gh is available
    pr_url = None
    if push_success and check_gh_installed():
        # Ensure labels exist in the repo
        ensure_labels_exist(vault_path)

        # Get labels for this PR
        labels = get_pr_labels(problem.difficulty, is_new_solution)

        logger.step("Creating pull request...")
        success, result = create_pull_request(
            vault_path,
            branch_name,
            problem.number,
            problem.title,
            problem.difficulty,
            problem.topic_tags,
            leetcode_url,
            labels=labels,
        )
        if success:
            pr_url = result
            logger.success(f"PR created: {pr_url}")
            logger.info(f"Labels: {', '.join(labels)}")
        else:
            logger.warning(f"Could not create PR: {result}")
            logger.info("Create PR manually at your vault repository")

    logger.blank()
    logger.success(f"Problem saved to: {folder}")
    logger.info(f"Branch: {branch_name}")
    if pr_url:
        logger.info(f"PR: {pr_url}")
    elif push_success:
        logger.info("Create a PR to merge into main")

    return True


def display_dry_run_output(
    logger,
    problem: ProblemData,
    solution_code: str,
    documentation: str,
) -> None:
    """Display generated documentation in dry-run mode.

    Args:
        logger: Logger instance.
        problem: Problem data.
        solution_code: Solution code.
        documentation: Generated documentation.
    """
    logger.blank()
    logger.header("DRY RUN OUTPUT")
    logger.blank()

    logger.info(f"Would save to: {problem.difficulty}/{problem.number}. {problem.title}/")
    logger.blank()

    logger.step("solution.py:")
    logger.blank()
    print(solution_code)
    logger.blank()

    logger.step("README.md:")
    logger.blank()
    print(documentation)
    logger.blank()

    logger.success("Dry run complete - no files were saved")


def run_workflow(logger, vault_path: Optional[Path], dry_run: bool = False) -> bool:
    """Run the main workflow for one problem.

    Args:
        logger: Logger instance.
        vault_path: Path to vault (None if dry-run).
        dry_run: If True, preview output without saving.

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
        if dry_run:
            logger.error("Cannot complete dry run without documentation")
            return False
        if not logger.confirm("Save without documentation?", default=False):
            return False
        documentation = f"# {problem.number}. {problem.title}\n\nDocumentation pending."

    # Dry run: display output and exit
    if dry_run:
        display_dry_run_output(logger, problem, solution_code, documentation)
        return True

    # Save to vault
    save_to_vault(logger, vault_path, problem, solution_code, documentation, url)

    return True


def run_search(logger, vault_path: Path, args: argparse.Namespace) -> None:
    """Run search command and display results.

    Args:
        logger: Logger instance.
        vault_path: Path to vault directory.
        args: Parsed command-line arguments.
    """
    logger.header("AlgoAtlas Search")

    # If --list-topics flag, show all topics
    if args.list_topics:
        topics = list_all_topics(vault_path)
        if topics:
            logger.info(f"Found {len(topics)} topics in vault:")
            logger.blank()
            for topic in topics:
                logger.info(f"  - {topic}")
        else:
            logger.warning("No topics found in vault")
        return

    # Run search with filters
    results = search_problems(
        vault_path,
        query=args.query,
        topic=args.topic,
        difficulty=args.difficulty,
    )

    if not results:
        logger.warning("No problems found matching your search")
        return

    logger.success(f"Found {len(results)} problem(s):")
    logger.blank()

    # Group by difficulty for display
    by_difficulty = {"Easy": [], "Medium": [], "Hard": []}
    for p in results:
        by_difficulty[p["difficulty"]].append(p)

    for difficulty in ["Easy", "Medium", "Hard"]:
        problems = by_difficulty[difficulty]
        if not problems:
            continue

        logger.info(f"[{difficulty}]")
        for p in problems:
            topics_str = ", ".join(p["topics"]) if p["topics"] else "No topics"
            logger.info(f"  {p['number']}. {p['title']}")
            logger.info(f"     Topics: {topics_str}")
            logger.info(f"     Path: {p['folder_path']}")
        logger.blank()


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        Parsed arguments namespace.
    """
    parser = argparse.ArgumentParser(
        prog="algo-atlas",
        description="Generate documentation for LeetCode solutions",
    )

    # Create subcommands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Default run command (no subcommand needed)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview generated documentation without saving to vault",
    )

    # Search subcommand
    search_parser = subparsers.add_parser(
        "search",
        help="Search problems in vault",
    )
    search_parser.add_argument(
        "query",
        nargs="?",
        default=None,
        help="Search query (problem number or keyword in title)",
    )
    search_parser.add_argument(
        "-t", "--topic",
        help="Filter by topic (partial match)",
    )
    search_parser.add_argument(
        "-d", "--difficulty",
        choices=["easy", "medium", "hard"],
        help="Filter by difficulty",
    )
    search_parser.add_argument(
        "--list-topics",
        action="store_true",
        help="List all topics in vault",
    )

    return parser.parse_args()


def main():
    """Main entry point for AlgoAtlas CLI."""
    args = parse_args()
    logger = get_logger()

    # Handle search command
    if args.command == "search":
        # Get vault path for search
        settings = get_settings()
        if not settings.vault_path:
            logger.error("Vault path not configured")
            sys.exit(1)

        vault_path = Path(settings.vault_path)
        if not validate_vault_repo(vault_path):
            logger.error(f"Vault path invalid: {vault_path}")
            sys.exit(1)

        run_search(logger, vault_path, args)
        return

    # Default: run documentation workflow
    # Run startup checks
    checks_passed, vault_path = startup_checks(logger, dry_run=args.dry_run)

    if not checks_passed:
        logger.error("Startup checks failed. Please fix issues above.")
        sys.exit(1)

    # Main loop
    while True:
        try:
            run_workflow(logger, vault_path, dry_run=args.dry_run)

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
