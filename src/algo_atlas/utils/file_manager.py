"""File management utilities for AlgoAtlas vault operations."""

import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

from algo_atlas.config.settings import get_settings


def get_vault_path() -> Optional[Path]:
    """Get configured vault path.

    Returns:
        Path to vault directory if configured, None otherwise.
    """
    settings = get_settings()
    return settings.get_vault_path()


def validate_vault_repo(vault_path: Optional[Path] = None) -> bool:
    """Check if vault repository exists and has required structure.

    Args:
        vault_path: Path to vault. Uses configured path if None.

    Returns:
        True if vault is valid, False otherwise.
    """
    if vault_path is None:
        vault_path = get_vault_path()

    if vault_path is None or not vault_path.exists():
        return False

    # Check for required difficulty directories
    required_dirs = ["Easy", "Medium", "Hard"]
    for dir_name in required_dirs:
        if not (vault_path / dir_name).exists():
            return False

    return True


def create_difficulty_folders(vault_path: Path) -> bool:
    """Create difficulty folders in vault if they don't exist.

    Args:
        vault_path: Path to vault directory.

    Returns:
        True if successful, False otherwise.
    """
    try:
        for difficulty in ["Easy", "Medium", "Hard"]:
            folder = vault_path / difficulty
            folder.mkdir(exist_ok=True)
        return True
    except OSError:
        return False


def sanitize_title(title: str) -> str:
    """Sanitize problem title for use in folder/file names.

    Args:
        title: Original problem title.

    Returns:
        Sanitized title safe for filesystem.
    """
    # Remove or replace invalid characters
    sanitized = re.sub(r'[<>:"/\\|?*]', "", title)
    # Replace multiple spaces with single space
    sanitized = re.sub(r"\s+", " ", sanitized)
    # Strip leading/trailing whitespace
    sanitized = sanitized.strip()
    return sanitized


def create_problem_folder(
    vault_path: Path,
    problem_number: int,
    title: str,
    difficulty: str,
) -> Optional[Path]:
    """Create problem folder with naming convention: '{num}. {Title}'.

    Args:
        vault_path: Path to vault directory.
        problem_number: LeetCode problem number.
        title: Problem title.
        difficulty: Problem difficulty (Easy, Medium, Hard).

    Returns:
        Path to created folder, None if failed.
    """
    if difficulty not in ["Easy", "Medium", "Hard"]:
        return None

    sanitized_title = sanitize_title(title)
    folder_name = f"{problem_number}. {sanitized_title}"
    folder_path = vault_path / difficulty / folder_name

    try:
        folder_path.mkdir(parents=True, exist_ok=True)
        return folder_path
    except OSError:
        return None


def save_solution_file(
    folder_path: Path,
    solution_code: str,
    filename: str = "solution.py",
) -> bool:
    """Save solution code to Python file.

    Args:
        folder_path: Path to problem folder.
        solution_code: Python solution code.
        filename: Output filename (default: solution.py).

    Returns:
        True if successful, False otherwise.
    """
    try:
        file_path = folder_path / filename
        file_path.write_text(solution_code, encoding="utf-8")
        return True
    except OSError:
        return False


def save_markdown(
    folder_path: Path,
    content: str,
    filename: str = "README.md",
) -> bool:
    """Save markdown documentation file.

    Args:
        folder_path: Path to problem folder.
        content: Markdown content.
        filename: Output filename (default: README.md).

    Returns:
        True if successful, False otherwise.
    """
    try:
        file_path = folder_path / filename
        file_path.write_text(content, encoding="utf-8")
        return True
    except OSError:
        return False


def check_problem_exists(
    vault_path: Path,
    problem_number: int,
) -> Optional[Path]:
    """Search for existing problem folder by number.

    Args:
        vault_path: Path to vault directory.
        problem_number: LeetCode problem number to search.

    Returns:
        Path to existing folder if found, None otherwise.
    """
    pattern = f"{problem_number}. *"

    for difficulty in ["Easy", "Medium", "Hard"]:
        difficulty_path = vault_path / difficulty
        if not difficulty_path.exists():
            continue

        matches = list(difficulty_path.glob(pattern))
        if matches:
            return matches[0]

    return None


def get_problem_info_from_path(folder_path: Path) -> dict:
    """Extract problem info from folder path.

    Args:
        folder_path: Path to problem folder.

    Returns:
        Dictionary with problem number, title, and difficulty.
    """
    folder_name = folder_path.name
    difficulty = folder_path.parent.name

    # Parse folder name: "{number}. {title}"
    match = re.match(r"^(\d+)\.\s*(.+)$", folder_name)
    if match:
        return {
            "number": int(match.group(1)),
            "title": match.group(2),
            "difficulty": difficulty,
        }

    return {
        "number": None,
        "title": folder_name,
        "difficulty": difficulty,
    }


# =============================================================================
# Git Operations for Vault
# =============================================================================


def generate_branch_name(problem_number: int, title: str) -> str:
    """Generate branch name for a problem.

    Format: add/{number}-{slug}-{YYMMDD}-{HHMM}

    Args:
        problem_number: LeetCode problem number.
        title: Problem title.

    Returns:
        Branch name string.
    """
    # Create slug from title
    slug = title.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")

    # Add timestamp
    timestamp = datetime.now().strftime("%y%m%d-%H%M")

    return f"add/{problem_number}-{slug}-{timestamp}"


def _run_git_command(
    vault_path: Path,
    args: list[str],
    check: bool = True,
) -> Tuple[bool, str]:
    """Run a git command in the vault directory.

    Args:
        vault_path: Path to vault repository.
        args: Git command arguments (without 'git' prefix).
        check: Whether to raise on non-zero exit.

    Returns:
        Tuple of (success, output/error message).
    """
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=vault_path,
            capture_output=True,
            text=True,
            check=check,
        )
        return True, result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return False, e.stderr.strip() or str(e)
    except FileNotFoundError:
        return False, "Git not found. Please install git."


def get_current_branch(vault_path: Path) -> Optional[str]:
    """Get the current branch name in vault repo.

    Args:
        vault_path: Path to vault repository.

    Returns:
        Current branch name or None if failed.
    """
    success, output = _run_git_command(
        vault_path,
        ["rev-parse", "--abbrev-ref", "HEAD"],
    )
    return output if success else None


def create_and_checkout_branch(vault_path: Path, branch_name: str) -> Tuple[bool, str]:
    """Create and checkout a new branch in vault repo.

    Args:
        vault_path: Path to vault repository.
        branch_name: Name of branch to create.

    Returns:
        Tuple of (success, message).
    """
    # First ensure we're on main/master
    success, _ = _run_git_command(vault_path, ["checkout", "main"], check=False)
    if not success:
        # Try master if main doesn't exist
        success, _ = _run_git_command(vault_path, ["checkout", "master"], check=False)

    # Pull latest changes
    _run_git_command(vault_path, ["pull", "origin", "HEAD"], check=False)

    # Create and checkout new branch
    success, output = _run_git_command(
        vault_path,
        ["checkout", "-b", branch_name],
    )

    if success:
        return True, f"Created branch: {branch_name}"
    else:
        return False, f"Failed to create branch: {output}"


def stage_files(vault_path: Path, files: list[Path]) -> Tuple[bool, str]:
    """Stage files for commit.

    Args:
        vault_path: Path to vault repository.
        files: List of file paths to stage.

    Returns:
        Tuple of (success, message).
    """
    # Convert to relative paths from vault
    relative_files = []
    for f in files:
        try:
            relative_files.append(str(f.relative_to(vault_path)))
        except ValueError:
            relative_files.append(str(f))

    success, output = _run_git_command(
        vault_path,
        ["add"] + relative_files,
    )

    if success:
        return True, f"Staged {len(files)} files"
    else:
        return False, f"Failed to stage files: {output}"


def commit_changes(
    vault_path: Path,
    problem_number: int,
    title: str,
) -> Tuple[bool, str]:
    """Commit staged changes with a formatted message.

    Args:
        vault_path: Path to vault repository.
        problem_number: LeetCode problem number.
        title: Problem title.

    Returns:
        Tuple of (success, message).
    """
    commit_message = f"Add {problem_number}. {title}"

    success, output = _run_git_command(
        vault_path,
        ["commit", "-m", commit_message],
    )

    if success:
        return True, f"Committed: {commit_message}"
    else:
        return False, f"Failed to commit: {output}"


def push_branch(vault_path: Path, branch_name: str) -> Tuple[bool, str]:
    """Push branch to remote origin.

    Args:
        vault_path: Path to vault repository.
        branch_name: Name of branch to push.

    Returns:
        Tuple of (success, message).
    """
    success, output = _run_git_command(
        vault_path,
        ["push", "-u", "origin", branch_name],
    )

    if success:
        return True, f"Pushed branch: {branch_name}"
    else:
        return False, f"Failed to push: {output}"


def checkout_main(vault_path: Path) -> Tuple[bool, str]:
    """Checkout main/master branch.

    Args:
        vault_path: Path to vault repository.

    Returns:
        Tuple of (success, message).
    """
    success, output = _run_git_command(vault_path, ["checkout", "main"], check=False)
    if not success:
        success, output = _run_git_command(vault_path, ["checkout", "master"], check=False)

    if success:
        return True, "Switched to main branch"
    else:
        return False, f"Failed to checkout main: {output}"


# =============================================================================
# GitHub CLI Operations
# =============================================================================


def _run_gh_command(
    vault_path: Path,
    args: list[str],
) -> Tuple[bool, str]:
    """Run a GitHub CLI command in the vault directory.

    Args:
        vault_path: Path to vault repository.
        args: gh command arguments (without 'gh' prefix).

    Returns:
        Tuple of (success, output/error message).
    """
    try:
        result = subprocess.run(
            ["gh"] + args,
            cwd=vault_path,
            capture_output=True,
            text=True,
            check=True,
        )
        return True, result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return False, e.stderr.strip() or str(e)
    except FileNotFoundError:
        return False, "GitHub CLI (gh) not found. Install from https://cli.github.com/"


def check_gh_installed() -> bool:
    """Check if GitHub CLI is installed and authenticated.

    Returns:
        True if gh is available and authenticated.
    """
    try:
        result = subprocess.run(
            ["gh", "auth", "status"],
            capture_output=True,
            text=True,
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


def create_pull_request(
    vault_path: Path,
    branch_name: str,
    problem_number: int,
    title: str,
    difficulty: str,
    topics: list[str],
    leetcode_url: str,
) -> Tuple[bool, str]:
    """Create a pull request using GitHub CLI.

    Args:
        vault_path: Path to vault repository.
        branch_name: Name of the branch to create PR from.
        problem_number: LeetCode problem number.
        title: Problem title.
        difficulty: Problem difficulty (Easy/Medium/Hard).
        topics: List of problem topics/tags.
        leetcode_url: URL to LeetCode problem.

    Returns:
        Tuple of (success, pr_url_or_error_message).
    """
    # Build PR title
    pr_title = f"Add {problem_number}. {title}"

    # Build PR body
    topics_str = ", ".join(topics) if topics else "N/A"
    pr_body = f"""## Problem
- **Difficulty:** {difficulty}
- **Topics:** {topics_str}
- **LeetCode:** [{problem_number}. {title}]({leetcode_url})

---
*Generated by [AlgoAtlas](https://github.com/roarceus/algo-atlas)*"""

    # Create PR using gh CLI
    success, output = _run_gh_command(
        vault_path,
        [
            "pr", "create",
            "--title", pr_title,
            "--body", pr_body,
            "--head", branch_name,
        ],
    )

    if success:
        # Output contains the PR URL
        return True, output
    else:
        return False, f"Failed to create PR: {output}"
