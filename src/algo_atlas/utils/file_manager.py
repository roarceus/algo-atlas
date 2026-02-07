"""File management utilities for AlgoAtlas vault operations.

This module re-exports functions from the split submodules for backwards
compatibility. New code should import directly from the specific modules:
- vault_files: File/folder operations
- git_ops: Git operations
- github_ops: GitHub CLI operations
- vault_readme: README stats and topic index
- vault_search: Search functionality
"""

# Vault file operations
from algo_atlas.utils.vault_files import (  # noqa: F401
    check_problem_exists,
    create_difficulty_folders,
    create_problem_folder,
    extract_topics_from_readme,
    get_problem_info_from_path,
    get_vault_path,
    sanitize_title,
    save_markdown,
    save_solution_file,
    validate_vault_repo,
)

# Git operations
from algo_atlas.utils.git_ops import (  # noqa: F401
    checkout_main,
    commit_changes,
    create_and_checkout_branch,
    generate_branch_name,
    get_current_branch,
    push_branch,
    stage_files,
)

# GitHub CLI operations
from algo_atlas.utils.github_ops import (  # noqa: F401
    LABEL_DEFINITIONS,
    check_gh_installed,
    create_pull_request,
    ensure_labels_exist,
    get_pr_labels,
)

# Vault README operations
from algo_atlas.utils.vault_readme import (  # noqa: F401
    STATS_END_MARKER,
    STATS_START_MARKER,
    TOPICS_END_MARKER,
    TOPICS_START_MARKER,
    count_vault_problems,
    generate_stats_markdown,
    generate_topic_index_markdown,
    scan_vault_topics,
    update_vault_readme,
)

# Search operations
from algo_atlas.utils.vault_search import (  # noqa: F401
    get_all_problems,
    list_all_topics,
    search_by_difficulty,
    search_by_keyword,
    search_by_number,
    search_by_topic,
    search_problems,
)
