"""File management utilities for AlgoAtlas vault operations."""

import re
from pathlib import Path
from typing import Optional

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
