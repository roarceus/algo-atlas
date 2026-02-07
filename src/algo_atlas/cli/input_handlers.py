"""User input handling for AlgoAtlas CLI."""

from pathlib import Path
from typing import Optional

from algo_atlas.config.settings import get_settings
from algo_atlas.core.generator import check_claude_installed
from algo_atlas.core.scraper import validate_leetcode_url
from algo_atlas.utils.vault_files import validate_vault_repo


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
