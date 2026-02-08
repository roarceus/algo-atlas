"""Batch processing for AlgoAtlas CLI."""

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from algo_atlas.core.scraper import validate_leetcode_url

from algo_atlas.cli.workflows import (
    display_dry_run_output,
    generate_docs_with_progress,
    save_to_vault,
    scrape_problem_with_progress,
    verify_solution_with_progress,
)


@dataclass
class BatchItem:
    """Single item in a batch file."""

    url: str
    solution_path: Path


@dataclass
class BatchResult:
    """Result of processing a single batch item."""

    url: str
    success: bool
    problem_title: Optional[str] = None
    error: Optional[str] = None


def parse_batch_file(file_path: Path) -> list[BatchItem]:
    """Parse a batch file containing problem URLs and solution paths.

    Supports two formats:
    1. Text format (.txt): One entry per line as "URL, solution_path"
    2. JSON format (.json): Array of {"url": "...", "solution": "..."} objects

    Args:
        file_path: Path to the batch file.

    Returns:
        List of BatchItem objects.

    Raises:
        ValueError: If file format is invalid or cannot be parsed.
    """
    if not file_path.exists():
        raise ValueError(f"Batch file not found: {file_path}")

    content = file_path.read_text(encoding="utf-8").strip()

    if file_path.suffix.lower() == ".json":
        return _parse_json_batch(content, file_path.parent)
    else:
        return _parse_text_batch(content, file_path.parent)


def _parse_json_batch(content: str, base_path: Path) -> list[BatchItem]:
    """Parse JSON format batch file.

    Args:
        content: JSON content string.
        base_path: Base path for resolving relative solution paths.

    Returns:
        List of BatchItem objects.
    """
    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format: {e}")

    if not isinstance(data, list):
        raise ValueError("JSON batch file must contain an array")

    items = []
    for i, entry in enumerate(data):
        if not isinstance(entry, dict):
            raise ValueError(f"Entry {i + 1} must be an object")

        url = entry.get("url", "").strip()
        solution = entry.get("solution", "").strip()

        if not url:
            raise ValueError(f"Entry {i + 1} missing 'url' field")
        if not solution:
            raise ValueError(f"Entry {i + 1} missing 'solution' field")

        solution_path = Path(solution)
        if not solution_path.is_absolute():
            solution_path = base_path / solution_path

        items.append(BatchItem(url=url, solution_path=solution_path))

    return items


def _parse_text_batch(content: str, base_path: Path) -> list[BatchItem]:
    """Parse text format batch file.

    Args:
        content: Text content string.
        base_path: Base path for resolving relative solution paths.

    Returns:
        List of BatchItem objects.
    """
    items = []
    lines = content.split("\n")

    for line_num, line in enumerate(lines, 1):
        line = line.strip()

        # Skip empty lines and comments
        if not line or line.startswith("#"):
            continue

        # Split by comma
        parts = [p.strip() for p in line.split(",")]

        if len(parts) < 2:
            raise ValueError(
                f"Line {line_num}: Expected 'URL, solution_path' format"
            )

        url = parts[0]
        solution = parts[1]

        if not url:
            raise ValueError(f"Line {line_num}: Missing URL")
        if not solution:
            raise ValueError(f"Line {line_num}: Missing solution path")

        solution_path = Path(solution)
        if not solution_path.is_absolute():
            solution_path = base_path / solution_path

        items.append(BatchItem(url=url, solution_path=solution_path))

    return items


def process_batch_item(
    logger,
    vault_path: Optional[Path],
    item: BatchItem,
    item_num: int,
    total: int,
    skip_verification: bool = False,
    dry_run: bool = False,
) -> BatchResult:
    """Process a single batch item.

    Args:
        logger: Logger instance.
        vault_path: Path to vault (None if dry-run).
        item: BatchItem to process.
        item_num: Current item number (1-indexed).
        total: Total number of items.
        skip_verification: If True, skip test case verification.
        dry_run: If True, preview output without saving.

    Returns:
        BatchResult with processing outcome.
    """
    logger.blank()
    logger.header(f"Processing {item_num}/{total}")
    logger.info(f"URL: {item.url}")
    logger.info(f"Solution: {item.solution_path}")

    # Validate URL
    if not validate_leetcode_url(item.url):
        return BatchResult(
            url=item.url,
            success=False,
            error="Invalid LeetCode URL format",
        )

    # Check solution file exists
    if not item.solution_path.exists():
        return BatchResult(
            url=item.url,
            success=False,
            error=f"Solution file not found: {item.solution_path}",
        )

    # Read solution code
    try:
        solution_code = item.solution_path.read_text(encoding="utf-8")
    except Exception as e:
        return BatchResult(
            url=item.url,
            success=False,
            error=f"Failed to read solution file: {e}",
        )

    # Scrape problem
    problem = scrape_problem_with_progress(logger, item.url)
    if not problem:
        return BatchResult(
            url=item.url,
            success=False,
            error="Failed to scrape problem from LeetCode",
        )

    # Verify solution (unless skipped)
    if not skip_verification:
        if not verify_solution_with_progress(logger, solution_code, problem):
            logger.warning("Verification issues detected, continuing anyway...")

    # Generate documentation
    documentation = generate_docs_with_progress(logger, problem, solution_code)
    if not documentation:
        return BatchResult(
            url=item.url,
            success=False,
            problem_title=f"{problem.number}. {problem.title}",
            error="Failed to generate documentation",
        )

    # Dry run: display output and return success
    if dry_run:
        display_dry_run_output(logger, problem, solution_code, documentation)
        return BatchResult(
            url=item.url,
            success=True,
            problem_title=f"{problem.number}. {problem.title}",
        )

    # Save to vault
    if save_to_vault(logger, vault_path, problem, solution_code, documentation, item.url):
        return BatchResult(
            url=item.url,
            success=True,
            problem_title=f"{problem.number}. {problem.title}",
        )
    else:
        return BatchResult(
            url=item.url,
            success=False,
            problem_title=f"{problem.number}. {problem.title}",
            error="Failed to save to vault",
        )


def run_batch(
    logger,
    vault_path: Optional[Path],
    args: argparse.Namespace,
) -> None:
    """Run batch processing workflow.

    Args:
        logger: Logger instance.
        vault_path: Path to vault (None if dry-run).
        args: Parsed command-line arguments.
    """
    batch_file = Path(args.file)

    logger.header("AlgoAtlas Batch Processing")
    logger.info(f"Batch file: {batch_file}")

    # Parse batch file
    try:
        items = parse_batch_file(batch_file)
    except ValueError as e:
        logger.error(f"Failed to parse batch file: {e}")
        sys.exit(1)

    if not items:
        logger.warning("No items found in batch file")
        return

    logger.success(f"Found {len(items)} problem(s) to process")

    if args.dry_run:
        logger.info("DRY RUN MODE - No files will be saved")

    # Process each item
    results: list[BatchResult] = []

    with logger.progress("Processing problems", total=len(items)) as (progress, task_id):
        for i, item in enumerate(items, 1):
            try:
                result = process_batch_item(
                    logger=logger,
                    vault_path=vault_path,
                    item=item,
                    item_num=i,
                    total=len(items),
                    skip_verification=args.skip_verification,
                    dry_run=args.dry_run,
                )
                results.append(result)
                progress.update(task_id, advance=1)

                if not result.success and not args.continue_on_error:
                    logger.error("Stopping batch due to error (use --continue-on-error to skip)")
                    break

            except KeyboardInterrupt:
                logger.blank()
                logger.warning("Batch processing interrupted by user")
                break
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                results.append(BatchResult(
                    url=item.url,
                    success=False,
                    error=str(e),
                ))
                progress.update(task_id, advance=1)
                if not args.continue_on_error:
                    break

    # Display summary
    display_batch_summary(logger, results, len(items))


def display_batch_summary(
    logger,
    results: list[BatchResult],
    total_items: int,
) -> None:
    """Display summary of batch processing results.

    Args:
        logger: Logger instance.
        results: List of BatchResult objects.
        total_items: Total number of items in batch file.
    """
    logger.blank()
    logger.header("Batch Processing Summary")

    successful = [r for r in results if r.success]
    failed = [r for r in results if not r.success]
    skipped = total_items - len(results)

    logger.info(f"Total items: {total_items}")
    logger.success(f"Successful: {len(successful)}")
    if failed:
        logger.error(f"Failed: {len(failed)}")
    if skipped > 0:
        logger.warning(f"Skipped: {skipped}")

    # Show successful items
    if successful:
        logger.blank()
        logger.info("Completed:")
        for r in successful:
            title = r.problem_title or r.url
            logger.success(f"  {title}")

    # Show failed items with errors
    if failed:
        logger.blank()
        logger.info("Failed:")
        for r in failed:
            title = r.problem_title or r.url
            logger.error(f"  {title}")
            if r.error:
                logger.info(f"    Error: {r.error}")

    logger.blank()
