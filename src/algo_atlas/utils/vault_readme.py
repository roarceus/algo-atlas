"""Vault README statistics and topic index management."""

import re
from datetime import datetime
from pathlib import Path
from typing import Tuple

from algo_atlas.utils.vault_files import extract_topics_from_readme


STATS_START_MARKER = "<!-- STATS:START -->"
STATS_END_MARKER = "<!-- STATS:END -->"
TOPICS_START_MARKER = "<!-- TOPICS:START -->"
TOPICS_END_MARKER = "<!-- TOPICS:END -->"


def count_vault_problems(vault_path: Path) -> dict[str, int]:
    """Count problem folders in each difficulty directory.

    Args:
        vault_path: Path to vault repository.

    Returns:
        Dictionary with counts: {"Easy": n, "Medium": n, "Hard": n}.
    """
    counts = {"Easy": 0, "Medium": 0, "Hard": 0}

    for difficulty in counts:
        difficulty_path = vault_path / difficulty
        if difficulty_path.exists():
            # Count directories that match problem pattern (number. title)
            folders = [
                f for f in difficulty_path.iterdir()
                if f.is_dir() and re.match(r"^\d+\.", f.name)
            ]
            counts[difficulty] = len(folders)

    return counts


def generate_stats_markdown(counts: dict[str, int]) -> str:
    """Generate markdown table for vault statistics.

    Args:
        counts: Dictionary with problem counts by difficulty.

    Returns:
        Markdown string with stats table.
    """
    total = sum(counts.values())
    today = datetime.now().strftime("%Y-%m-%d")

    lines = [
        STATS_START_MARKER,
        "## Statistics",
        "",
        "| Difficulty | Count | Percentage |",
        "|------------|-------|------------|",
    ]

    for difficulty in ["Easy", "Medium", "Hard"]:
        count = counts.get(difficulty, 0)
        pct = round(count / total * 100) if total > 0 else 0
        lines.append(f"| {difficulty} | {count} | {pct}% |")

    lines.append(f"| **Total** | **{total}** | **100%** |")
    lines.append("")
    lines.append(f"*Last updated: {today}*")
    lines.append(STATS_END_MARKER)

    return "\n".join(lines)


def scan_vault_topics(vault_path: Path) -> dict[str, list[dict]]:
    """Scan vault and build topic index.

    Args:
        vault_path: Path to vault repository.

    Returns:
        Dictionary mapping topic name to list of problem info dicts.
        Each problem dict has: number, title, difficulty, folder_name.
    """
    topic_index: dict[str, list[dict]] = {}

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

            problem_info = {
                "number": problem_num,
                "title": problem_title,
                "difficulty": difficulty,
                "folder_name": folder.name,
            }

            for topic in topics:
                if topic not in topic_index:
                    topic_index[topic] = []
                topic_index[topic].append(problem_info)

    # Sort problems within each topic by number
    for topic in topic_index:
        topic_index[topic].sort(key=lambda p: p["number"])

    return topic_index


def generate_topic_index_markdown(topic_index: dict[str, list[dict]]) -> str:
    """Generate markdown for topic index.

    Args:
        topic_index: Dictionary mapping topic to list of problems.

    Returns:
        Markdown string with topic index.
    """
    if not topic_index:
        return ""

    lines = [
        TOPICS_START_MARKER,
        "## Topics",
        "",
    ]

    # Sort topics alphabetically
    for topic in sorted(topic_index.keys()):
        problems = topic_index[topic]
        lines.append(f"### {topic}")
        lines.append("")

        for p in problems:
            # URL-encode the folder name for the link
            encoded_folder = p["folder_name"].replace(" ", "%20")
            link = f"{p['difficulty']}/{encoded_folder}/"
            lines.append(f"- [{p['number']}. {p['title']}]({link})")

        lines.append("")

    lines.append(TOPICS_END_MARKER)

    return "\n".join(lines)


def _update_or_append_section(
    content: str,
    section_md: str,
    start_marker: str,
    end_marker: str,
) -> str:
    """Update existing section or append new section to content.

    Args:
        content: Existing README content.
        section_md: New markdown for the section.
        start_marker: Section start marker.
        end_marker: Section end marker.

    Returns:
        Updated content string.
    """
    if start_marker in content and end_marker in content:
        # Replace existing section
        pattern = re.compile(
            rf"{re.escape(start_marker)}.*?{re.escape(end_marker)}",
            re.DOTALL,
        )
        return pattern.sub(section_md, content)
    else:
        # Append section
        return content.rstrip() + "\n\n" + section_md + "\n"


def update_vault_readme(vault_path: Path) -> Tuple[bool, str]:
    """Update vault README.md with statistics and topic index.

    If sections exist (between markers), replaces them.
    Otherwise, appends sections to end of file.

    Args:
        vault_path: Path to vault repository.

    Returns:
        Tuple of (success, message).
    """
    readme_path = vault_path / "README.md"

    # Generate stats
    counts = count_vault_problems(vault_path)
    stats_md = generate_stats_markdown(counts)

    # Generate topic index
    topic_index = scan_vault_topics(vault_path)
    topics_md = generate_topic_index_markdown(topic_index)

    try:
        # Read existing content or create new
        if readme_path.exists():
            content = readme_path.read_text(encoding="utf-8")
        else:
            content = "# AlgoAtlas Vault\n\nMy documented LeetCode solutions.\n\n"

        # Update stats section
        content = _update_or_append_section(
            content, stats_md, STATS_START_MARKER, STATS_END_MARKER
        )

        # Update topics section (if there are any topics)
        if topics_md:
            content = _update_or_append_section(
                content, topics_md, TOPICS_START_MARKER, TOPICS_END_MARKER
            )

        # Write updated content
        readme_path.write_text(content, encoding="utf-8")

        total = sum(counts.values())
        num_topics = len(topic_index)
        return True, f"Updated vault: {total} problems, {num_topics} topics"

    except OSError as e:
        return False, f"Failed to update README: {e}"
