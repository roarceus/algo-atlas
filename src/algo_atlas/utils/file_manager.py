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

# Label definitions for PRs
LABEL_DEFINITIONS = {
    "easy": {"color": "00ff00", "description": "Easy difficulty problem"},
    "medium": {"color": "ffff00", "description": "Medium difficulty problem"},
    "hard": {"color": "ff0000", "description": "Hard difficulty problem"},
    "new-solution": {"color": "0000ff", "description": "First solution for this problem"},
    "alternative-solution": {"color": "800080", "description": "Alternative solution for existing problem"},
}


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


def ensure_labels_exist(vault_path: Path) -> Tuple[bool, str]:
    """Ensure all required labels exist in the vault repository.

    Creates labels if they don't exist. Skips existing labels.

    Args:
        vault_path: Path to vault repository.

    Returns:
        Tuple of (success, message).
    """
    created = []
    skipped = []

    for label_name, props in LABEL_DEFINITIONS.items():
        success, output = _run_gh_command(
            vault_path,
            [
                "label", "create", label_name,
                "--color", props["color"],
                "--description", props["description"],
                "--force",
            ],
        )
        if success:
            if "already exists" in output.lower():
                skipped.append(label_name)
            else:
                created.append(label_name)
        else:
            # Label might already exist (gh returns error for existing labels without --force)
            skipped.append(label_name)

    if created:
        return True, f"Created labels: {', '.join(created)}"
    else:
        return True, "All labels already exist"


def get_pr_labels(difficulty: str, is_new_solution: bool) -> list[str]:
    """Get list of labels to apply to a PR.

    Args:
        difficulty: Problem difficulty (Easy/Medium/Hard).
        is_new_solution: True if this is the first solution for the problem.

    Returns:
        List of label names to apply.
    """
    labels = []

    # Add difficulty label
    difficulty_lower = difficulty.lower()
    if difficulty_lower in LABEL_DEFINITIONS:
        labels.append(difficulty_lower)

    # Add solution type label
    if is_new_solution:
        labels.append("new-solution")
    else:
        labels.append("alternative-solution")

    return labels


def create_pull_request(
    vault_path: Path,
    branch_name: str,
    problem_number: int,
    title: str,
    difficulty: str,
    topics: list[str],
    leetcode_url: str,
    labels: Optional[list[str]] = None,
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
        labels: Optional list of labels to apply to the PR.

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

    # Build command args
    cmd_args = [
        "pr", "create",
        "--title", pr_title,
        "--body", pr_body,
        "--head", branch_name,
    ]

    # Add labels if provided
    if labels:
        for label in labels:
            cmd_args.extend(["--label", label])

    # Create PR using gh CLI
    success, output = _run_gh_command(vault_path, cmd_args)

    if success:
        # Output contains the PR URL
        return True, output
    else:
        return False, f"Failed to create PR: {output}"


# =============================================================================
# Vault Statistics
# =============================================================================

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


def extract_topics_from_readme(readme_path: Path) -> list[str]:
    """Extract topic tags from a problem README.

    Args:
        readme_path: Path to problem README.md.

    Returns:
        List of topic names, empty if not found.
    """
    try:
        content = readme_path.read_text(encoding="utf-8")
        # Look for pattern: **Topics:** Topic1, Topic2, Topic3
        match = re.search(r"\*\*Topics:\*\*\s*(.+?)(?:\n|$)", content)
        if match:
            topics_str = match.group(1).strip()
            # Split by comma and clean up
            return [t.strip() for t in topics_str.split(",") if t.strip()]
    except OSError:
        pass
    return []


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


# =============================================================================
# Search Functions
# =============================================================================


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
