"""Search functionality for AlgoAtlas vault."""

import re
from pathlib import Path
from typing import Optional

from algo_atlas.utils.vault_files import extract_topics_from_readme
from algo_atlas.utils.vault_readme import scan_vault_topics


def get_all_problems(vault_path: Path) -> list[dict]:
    """Get all problems from vault with their metadata.

    Args:
        vault_path: Path to vault repository.

    Returns:
        List of problem info dicts with: number, title, difficulty,
        folder_name, topics, folder_path.
    """
    problems = []

    for difficulty in ["Easy", "Medium", "Hard"]:
        difficulty_path = vault_path / difficulty
        if not difficulty_path.exists():
            continue

        for folder in difficulty_path.iterdir():
            if not folder.is_dir():
                continue

            # Check if it's a problem folder (starts with number)
            match = re.match(r"^(\d+)\.\s*(.+)$", folder.name)
            if not match:
                continue

            problem_num = int(match.group(1))
            problem_title = match.group(2)

            # Extract topics from README
            readme_path = folder / "README.md"
            topics = extract_topics_from_readme(readme_path)

            problems.append({
                "number": problem_num,
                "title": problem_title,
                "difficulty": difficulty,
                "folder_name": folder.name,
                "folder_path": folder,
                "topics": topics,
            })

    # Sort by problem number
    problems.sort(key=lambda p: p["number"])
    return problems


def search_by_topic(vault_path: Path, topic: str) -> list[dict]:
    """Search problems by topic (case-insensitive partial match).

    Args:
        vault_path: Path to vault repository.
        topic: Topic to search for.

    Returns:
        List of matching problem info dicts.
    """
    topic_lower = topic.lower()
    problems = get_all_problems(vault_path)

    return [
        p for p in problems
        if any(topic_lower in t.lower() for t in p["topics"])
    ]


def search_by_difficulty(vault_path: Path, difficulty: str) -> list[dict]:
    """Search problems by difficulty.

    Args:
        vault_path: Path to vault repository.
        difficulty: Difficulty level (easy/medium/hard, case-insensitive).

    Returns:
        List of matching problem info dicts.
    """
    difficulty_normalized = difficulty.capitalize()
    if difficulty_normalized not in ["Easy", "Medium", "Hard"]:
        return []

    problems = get_all_problems(vault_path)
    return [p for p in problems if p["difficulty"] == difficulty_normalized]


def search_by_keyword(vault_path: Path, keyword: str) -> list[dict]:
    """Search problems by keyword in title (case-insensitive).

    Args:
        vault_path: Path to vault repository.
        keyword: Keyword to search in problem titles.

    Returns:
        List of matching problem info dicts.
    """
    keyword_lower = keyword.lower()
    problems = get_all_problems(vault_path)

    return [
        p for p in problems
        if keyword_lower in p["title"].lower()
    ]


def search_by_number(vault_path: Path, number: int) -> Optional[dict]:
    """Search for a specific problem by number.

    Args:
        vault_path: Path to vault repository.
        number: Problem number to find.

    Returns:
        Problem info dict if found, None otherwise.
    """
    problems = get_all_problems(vault_path)

    for p in problems:
        if p["number"] == number:
            return p
    return None


def search_problems(
    vault_path: Path,
    query: Optional[str] = None,
    topic: Optional[str] = None,
    difficulty: Optional[str] = None,
) -> list[dict]:
    """Search problems with multiple filters.

    Args:
        vault_path: Path to vault repository.
        query: Keyword to search in titles or problem number.
        topic: Topic to filter by.
        difficulty: Difficulty to filter by.

    Returns:
        List of matching problem info dicts.
    """
    problems = get_all_problems(vault_path)

    # Filter by difficulty
    if difficulty:
        difficulty_normalized = difficulty.capitalize()
        if difficulty_normalized in ["Easy", "Medium", "Hard"]:
            problems = [p for p in problems if p["difficulty"] == difficulty_normalized]

    # Filter by topic
    if topic:
        topic_lower = topic.lower()
        problems = [
            p for p in problems
            if any(topic_lower in t.lower() for t in p["topics"])
        ]

    # Filter by query (title keyword or number)
    if query:
        # Check if query is a number
        if query.isdigit():
            num = int(query)
            problems = [p for p in problems if p["number"] == num]
        else:
            query_lower = query.lower()
            problems = [
                p for p in problems
                if query_lower in p["title"].lower()
            ]

    return problems


def list_all_topics(vault_path: Path) -> list[str]:
    """Get list of all unique topics in vault.

    Args:
        vault_path: Path to vault repository.

    Returns:
        Sorted list of unique topic names.
    """
    topic_index = scan_vault_topics(vault_path)
    return sorted(topic_index.keys())
