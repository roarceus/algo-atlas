"""Git operations for AlgoAtlas vault repository."""

import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple


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
