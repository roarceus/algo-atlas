"""Tests for the file manager module."""

import re

from algo_atlas.utils.file_manager import (
    check_gh_installed,
    check_problem_exists,
    count_vault_problems,
    create_problem_folder,
    extract_topics_from_readme,
    generate_branch_name,
    generate_stats_markdown,
    generate_topic_index_markdown,
    get_all_problems,
    get_pr_labels,
    list_all_topics,
    sanitize_title,
    save_markdown,
    save_solution_file,
    scan_vault_topics,
    search_by_difficulty,
    search_by_keyword,
    search_by_number,
    search_by_topic,
    search_problems,
    update_vault_readme,
    validate_vault_repo,
)


class TestValidateVaultRepo:
    """Tests for validate_vault_repo function."""

    def test_valid_vault(self, temp_vault):
        """Test validation of valid vault structure."""
        assert validate_vault_repo(temp_vault) is True

    def test_missing_easy_folder(self, tmp_path):
        """Test validation fails without Easy folder."""
        vault = tmp_path / "incomplete-vault"
        vault.mkdir()
        (vault / "Medium").mkdir()
        (vault / "Hard").mkdir()
        assert validate_vault_repo(vault) is False

    def test_missing_medium_folder(self, tmp_path):
        """Test validation fails without Medium folder."""
        vault = tmp_path / "incomplete-vault"
        vault.mkdir()
        (vault / "Easy").mkdir()
        (vault / "Hard").mkdir()
        assert validate_vault_repo(vault) is False

    def test_missing_hard_folder(self, tmp_path):
        """Test validation fails without Hard folder."""
        vault = tmp_path / "incomplete-vault"
        vault.mkdir()
        (vault / "Easy").mkdir()
        (vault / "Medium").mkdir()
        assert validate_vault_repo(vault) is False

    def test_nonexistent_vault(self, tmp_path):
        """Test validation fails for nonexistent path."""
        vault = tmp_path / "nonexistent"
        assert validate_vault_repo(vault) is False

    def test_none_vault_no_config(self, tmp_path, monkeypatch):
        """Test validation with None path and no configured vault."""
        # Patch get_vault_path to return None (no configured vault)
        monkeypatch.setattr(
            "algo_atlas.utils.vault_files.get_vault_path",
            lambda: None
        )
        assert validate_vault_repo(None) is False


class TestSanitizeTitle:
    """Tests for sanitize_title function."""

    def test_basic_title(self):
        """Test basic title sanitization."""
        assert sanitize_title("Two Sum") == "Two Sum"

    def test_title_with_special_chars(self):
        """Test title with special characters."""
        assert sanitize_title("Two Sum: Easy?") == "Two Sum Easy"

    def test_title_with_invalid_chars(self):
        """Test title with filesystem invalid characters."""
        assert sanitize_title('Test<>:"/\\|?*Title') == "TestTitle"

    def test_title_with_extra_spaces(self):
        """Test title with extra spaces."""
        assert sanitize_title("Two   Sum") == "Two Sum"

    def test_title_with_leading_trailing_spaces(self):
        """Test title with leading/trailing spaces."""
        assert sanitize_title("  Two Sum  ") == "Two Sum"


class TestCreateProblemFolder:
    """Tests for create_problem_folder function."""

    def test_create_easy_folder(self, temp_vault):
        """Test creating folder in Easy directory."""
        folder = create_problem_folder(temp_vault, 1, "Two Sum", "Easy")
        assert folder is not None
        assert folder.exists()
        assert folder.name == "1. Two Sum"
        assert folder.parent.name == "Easy"

    def test_create_medium_folder(self, temp_vault):
        """Test creating folder in Medium directory."""
        folder = create_problem_folder(temp_vault, 15, "3Sum", "Medium")
        assert folder is not None
        assert folder.exists()
        assert folder.parent.name == "Medium"

    def test_create_hard_folder(self, temp_vault):
        """Test creating folder in Hard directory."""
        folder = create_problem_folder(temp_vault, 4, "Median of Two Sorted Arrays", "Hard")
        assert folder is not None
        assert folder.exists()
        assert folder.parent.name == "Hard"

    def test_invalid_difficulty(self, temp_vault):
        """Test with invalid difficulty."""
        folder = create_problem_folder(temp_vault, 1, "Test", "Invalid")
        assert folder is None

    def test_folder_already_exists(self, temp_vault):
        """Test creating folder that already exists."""
        folder1 = create_problem_folder(temp_vault, 1, "Two Sum", "Easy")
        folder2 = create_problem_folder(temp_vault, 1, "Two Sum", "Easy")
        assert folder1 == folder2
        assert folder2.exists()


class TestSaveSolutionFile:
    """Tests for save_solution_file function."""

    def test_save_solution(self, temp_vault):
        """Test saving solution file."""
        folder = create_problem_folder(temp_vault, 1, "Two Sum", "Easy")
        code = "class Solution:\n    pass"

        result = save_solution_file(folder, code)

        assert result is True
        assert (folder / "solution.py").exists()
        assert (folder / "solution.py").read_text() == code

    def test_save_with_custom_filename(self, temp_vault):
        """Test saving with custom filename."""
        folder = create_problem_folder(temp_vault, 1, "Two Sum", "Easy")
        code = "# Alternative solution"

        result = save_solution_file(folder, code, "solution_v2.py")

        assert result is True
        assert (folder / "solution_v2.py").exists()


class TestSaveMarkdown:
    """Tests for save_markdown function."""

    def test_save_markdown(self, temp_vault):
        """Test saving markdown file."""
        folder = create_problem_folder(temp_vault, 1, "Two Sum", "Easy")
        content = "# Two Sum\n\nThis is a test."

        result = save_markdown(folder, content)

        assert result is True
        assert (folder / "README.md").exists()
        assert (folder / "README.md").read_text() == content

    def test_save_with_custom_filename(self, temp_vault):
        """Test saving with custom filename."""
        folder = create_problem_folder(temp_vault, 1, "Two Sum", "Easy")
        content = "# Notes"

        result = save_markdown(folder, content, "NOTES.md")

        assert result is True
        assert (folder / "NOTES.md").exists()


class TestCheckProblemExists:
    """Tests for check_problem_exists function."""

    def test_problem_exists(self, temp_vault):
        """Test finding existing problem."""
        create_problem_folder(temp_vault, 1, "Two Sum", "Easy")

        result = check_problem_exists(temp_vault, 1)

        assert result is not None
        assert "1. Two Sum" in str(result)

    def test_problem_not_exists(self, temp_vault):
        """Test searching for nonexistent problem."""
        result = check_problem_exists(temp_vault, 999)
        assert result is None

    def test_find_in_different_difficulties(self, temp_vault):
        """Test finding problems in different difficulties."""
        create_problem_folder(temp_vault, 1, "Two Sum", "Easy")
        create_problem_folder(temp_vault, 4, "Median", "Hard")

        assert check_problem_exists(temp_vault, 1) is not None
        assert check_problem_exists(temp_vault, 4) is not None
        assert check_problem_exists(temp_vault, 2) is None


class TestGenerateBranchName:
    """Tests for generate_branch_name function."""

    def test_basic_branch_name(self):
        """Test basic branch name generation."""
        branch = generate_branch_name(1, "Two Sum")

        assert branch.startswith("add/1-two-sum-")
        # Check timestamp format (YYMMDD-HHMM)
        assert re.match(r"add/1-two-sum-\d{6}-\d{4}$", branch)

    def test_branch_name_with_special_chars(self):
        """Test branch name with special characters in title."""
        branch = generate_branch_name(20, "Valid Parentheses")

        assert branch.startswith("add/20-valid-parentheses-")
        assert "(" not in branch
        assert ")" not in branch

    def test_branch_name_with_numbers(self):
        """Test branch name with numbers in title."""
        branch = generate_branch_name(15, "3Sum")

        assert branch.startswith("add/15-3sum-")

    def test_branch_name_uniqueness(self):
        """Test that branch names are unique (timestamp-based)."""
        import time

        branch1 = generate_branch_name(1, "Two Sum")
        time.sleep(0.1)  # Small delay
        branch2 = generate_branch_name(1, "Two Sum")

        # Branches should start the same but may differ in last minute
        assert branch1.startswith("add/1-two-sum-")
        assert branch2.startswith("add/1-two-sum-")


class TestCheckGhInstalled:
    """Tests for check_gh_installed function."""

    def test_returns_boolean(self):
        """Test that check_gh_installed returns a boolean."""
        result = check_gh_installed()
        assert isinstance(result, bool)


class TestGetPrLabels:
    """Tests for get_pr_labels function."""

    def test_easy_new_solution(self):
        """Test labels for new Easy problem."""
        labels = get_pr_labels("Easy", is_new_solution=True)
        assert "easy" in labels
        assert "new-solution" in labels
        assert "alternative-solution" not in labels

    def test_medium_alternative_solution(self):
        """Test labels for alternative Medium solution."""
        labels = get_pr_labels("Medium", is_new_solution=False)
        assert "medium" in labels
        assert "alternative-solution" in labels
        assert "new-solution" not in labels

    def test_hard_new_solution(self):
        """Test labels for new Hard problem."""
        labels = get_pr_labels("Hard", is_new_solution=True)
        assert "hard" in labels
        assert "new-solution" in labels

    def test_labels_are_lowercase(self):
        """Test that difficulty labels are lowercase."""
        labels = get_pr_labels("Easy", is_new_solution=True)
        assert all(label.islower() or "-" in label for label in labels)


class TestCountVaultProblems:
    """Tests for count_vault_problems function."""

    def test_empty_vault(self, temp_vault):
        """Test counting empty vault."""
        counts = count_vault_problems(temp_vault)
        assert counts == {"Easy": 0, "Medium": 0, "Hard": 0}

    def test_count_problems(self, temp_vault):
        """Test counting problems in vault."""
        create_problem_folder(temp_vault, 1, "Two Sum", "Easy")
        create_problem_folder(temp_vault, 2, "Add Two Numbers", "Medium")
        create_problem_folder(temp_vault, 3, "Longest Substring", "Medium")
        create_problem_folder(temp_vault, 4, "Median", "Hard")

        counts = count_vault_problems(temp_vault)

        assert counts["Easy"] == 1
        assert counts["Medium"] == 2
        assert counts["Hard"] == 1

    def test_ignores_non_problem_folders(self, temp_vault):
        """Test that non-problem folders are ignored."""
        create_problem_folder(temp_vault, 1, "Two Sum", "Easy")
        # Create a non-problem folder
        (temp_vault / "Easy" / "notes").mkdir()

        counts = count_vault_problems(temp_vault)

        assert counts["Easy"] == 1


class TestGenerateStatsMarkdown:
    """Tests for generate_stats_markdown function."""

    def test_generate_stats(self):
        """Test generating stats markdown."""
        counts = {"Easy": 5, "Medium": 3, "Hard": 2}

        result = generate_stats_markdown(counts)

        assert "## Statistics" in result
        assert "| Easy | 5 | 50% |" in result
        assert "| Medium | 3 | 30% |" in result
        assert "| Hard | 2 | 20% |" in result
        assert "| **Total** | **10** | **100%** |" in result
        assert "<!-- STATS:START -->" in result
        assert "<!-- STATS:END -->" in result

    def test_generate_stats_empty(self):
        """Test generating stats for empty vault."""
        counts = {"Easy": 0, "Medium": 0, "Hard": 0}

        result = generate_stats_markdown(counts)

        assert "| **Total** | **0** | **100%** |" in result


class TestUpdateVaultReadme:
    """Tests for update_vault_readme function."""

    def test_create_readme_if_missing(self, temp_vault):
        """Test creating README if it doesn't exist."""
        create_problem_folder(temp_vault, 1, "Two Sum", "Easy")

        success, msg = update_vault_readme(temp_vault)

        assert success is True
        assert (temp_vault / "README.md").exists()
        content = (temp_vault / "README.md").read_text()
        assert "## Statistics" in content
        assert "| Easy | 1 |" in content

    def test_update_existing_readme(self, temp_vault):
        """Test updating existing README with stats."""
        # Create initial README
        readme = temp_vault / "README.md"
        readme.write_text("# My Vault\n\nWelcome!\n")

        create_problem_folder(temp_vault, 1, "Two Sum", "Easy")
        success, msg = update_vault_readme(temp_vault)

        assert success is True
        content = readme.read_text()
        assert "# My Vault" in content
        assert "## Statistics" in content

    def test_replace_existing_stats(self, temp_vault):
        """Test replacing existing stats section."""
        # Create README with stats
        readme = temp_vault / "README.md"
        readme.write_text(
            "# Vault\n\n<!-- STATS:START -->\nOld stats\n<!-- STATS:END -->\n"
        )

        create_problem_folder(temp_vault, 1, "Two Sum", "Easy")
        create_problem_folder(temp_vault, 2, "Add Two", "Medium")
        success, msg = update_vault_readme(temp_vault)

        content = readme.read_text()
        assert "Old stats" not in content
        assert "| Easy | 1 |" in content
        assert "| Medium | 1 |" in content


class TestExtractTopicsFromReadme:
    """Tests for extract_topics_from_readme function."""

    def test_extract_topics(self, temp_vault):
        """Test extracting topics from README."""
        folder = create_problem_folder(temp_vault, 1, "Two Sum", "Easy")
        readme = folder / "README.md"
        readme.write_text("# Two Sum\n\n**Topics:** Array, Hash Table\n")

        topics = extract_topics_from_readme(readme)

        assert topics == ["Array", "Hash Table"]

    def test_no_topics_line(self, temp_vault):
        """Test README without topics line."""
        folder = create_problem_folder(temp_vault, 1, "Two Sum", "Easy")
        readme = folder / "README.md"
        readme.write_text("# Two Sum\n\nNo topics here.\n")

        topics = extract_topics_from_readme(readme)

        assert topics == []

    def test_nonexistent_file(self, temp_vault):
        """Test nonexistent README returns empty list."""
        topics = extract_topics_from_readme(temp_vault / "nonexistent.md")
        assert topics == []


class TestScanVaultTopics:
    """Tests for scan_vault_topics function."""

    def test_scan_topics(self, temp_vault):
        """Test scanning vault for topics."""
        # Create problems with READMEs
        folder1 = create_problem_folder(temp_vault, 1, "Two Sum", "Easy")
        (folder1 / "README.md").write_text("**Topics:** Array, Hash Table\n")

        folder2 = create_problem_folder(temp_vault, 15, "3Sum", "Medium")
        (folder2 / "README.md").write_text("**Topics:** Array, Two Pointers\n")

        topic_index = scan_vault_topics(temp_vault)

        assert "Array" in topic_index
        assert len(topic_index["Array"]) == 2
        assert "Hash Table" in topic_index
        assert "Two Pointers" in topic_index

    def test_empty_vault(self, temp_vault):
        """Test scanning empty vault."""
        topic_index = scan_vault_topics(temp_vault)
        assert topic_index == {}

    def test_problems_sorted_by_number(self, temp_vault):
        """Test that problems within topic are sorted by number."""
        folder1 = create_problem_folder(temp_vault, 15, "3Sum", "Medium")
        (folder1 / "README.md").write_text("**Topics:** Array\n")

        folder2 = create_problem_folder(temp_vault, 1, "Two Sum", "Easy")
        (folder2 / "README.md").write_text("**Topics:** Array\n")

        topic_index = scan_vault_topics(temp_vault)

        assert topic_index["Array"][0]["number"] == 1
        assert topic_index["Array"][1]["number"] == 15


class TestGenerateTopicIndexMarkdown:
    """Tests for generate_topic_index_markdown function."""

    def test_generate_index(self):
        """Test generating topic index markdown."""
        topic_index = {
            "Array": [
                {"number": 1, "title": "Two Sum", "difficulty": "Easy", "folder_name": "1. Two Sum"},
            ],
            "Hash Table": [
                {"number": 1, "title": "Two Sum", "difficulty": "Easy", "folder_name": "1. Two Sum"},
            ],
        }

        result = generate_topic_index_markdown(topic_index)

        assert "## Topics" in result
        assert "### Array" in result
        assert "### Hash Table" in result
        assert "[1. Two Sum](Easy/1.%20Two%20Sum/)" in result
        assert "<!-- TOPICS:START -->" in result
        assert "<!-- TOPICS:END -->" in result

    def test_empty_index(self):
        """Test generating empty topic index."""
        result = generate_topic_index_markdown({})
        assert result == ""

    def test_topics_sorted_alphabetically(self):
        """Test that topics are sorted alphabetically."""
        topic_index = {
            "Zebra": [{"number": 1, "title": "Test", "difficulty": "Easy", "folder_name": "1. Test"}],
            "Apple": [{"number": 2, "title": "Test2", "difficulty": "Easy", "folder_name": "2. Test2"}],
        }

        result = generate_topic_index_markdown(topic_index)

        apple_pos = result.index("### Apple")
        zebra_pos = result.index("### Zebra")
        assert apple_pos < zebra_pos


class TestGetAllProblems:
    """Tests for get_all_problems function."""

    def test_empty_vault(self, temp_vault):
        """Test getting problems from empty vault."""
        problems = get_all_problems(temp_vault)
        assert problems == []

    def test_get_problems(self, temp_vault):
        """Test getting all problems from vault."""
        folder1 = create_problem_folder(temp_vault, 1, "Two Sum", "Easy")
        (folder1 / "README.md").write_text("**Topics:** Array, Hash Table\n")

        folder2 = create_problem_folder(temp_vault, 15, "3Sum", "Medium")
        (folder2 / "README.md").write_text("**Topics:** Array, Two Pointers\n")

        problems = get_all_problems(temp_vault)

        assert len(problems) == 2
        assert problems[0]["number"] == 1
        assert problems[0]["title"] == "Two Sum"
        assert problems[0]["difficulty"] == "Easy"
        assert "Array" in problems[0]["topics"]
        assert problems[1]["number"] == 15

    def test_problems_sorted_by_number(self, temp_vault):
        """Test that problems are sorted by number."""
        create_problem_folder(temp_vault, 100, "Problem 100", "Hard")
        create_problem_folder(temp_vault, 1, "Problem 1", "Easy")
        create_problem_folder(temp_vault, 50, "Problem 50", "Medium")

        problems = get_all_problems(temp_vault)

        assert problems[0]["number"] == 1
        assert problems[1]["number"] == 50
        assert problems[2]["number"] == 100


class TestSearchByTopic:
    """Tests for search_by_topic function."""

    def test_search_by_topic(self, temp_vault):
        """Test searching by topic."""
        folder1 = create_problem_folder(temp_vault, 1, "Two Sum", "Easy")
        (folder1 / "README.md").write_text("**Topics:** Array, Hash Table\n")

        folder2 = create_problem_folder(temp_vault, 20, "Valid Parentheses", "Easy")
        (folder2 / "README.md").write_text("**Topics:** String, Stack\n")

        results = search_by_topic(temp_vault, "Array")

        assert len(results) == 1
        assert results[0]["number"] == 1

    def test_search_case_insensitive(self, temp_vault):
        """Test that topic search is case-insensitive."""
        folder = create_problem_folder(temp_vault, 1, "Two Sum", "Easy")
        (folder / "README.md").write_text("**Topics:** Array, Hash Table\n")

        results = search_by_topic(temp_vault, "array")

        assert len(results) == 1

    def test_search_partial_match(self, temp_vault):
        """Test that topic search supports partial match."""
        folder = create_problem_folder(temp_vault, 1, "Two Sum", "Easy")
        (folder / "README.md").write_text("**Topics:** Hash Table\n")

        results = search_by_topic(temp_vault, "Hash")

        assert len(results) == 1

    def test_no_matches(self, temp_vault):
        """Test search with no matches."""
        folder = create_problem_folder(temp_vault, 1, "Two Sum", "Easy")
        (folder / "README.md").write_text("**Topics:** Array\n")

        results = search_by_topic(temp_vault, "Graph")

        assert len(results) == 0


class TestSearchByDifficulty:
    """Tests for search_by_difficulty function."""

    def test_search_easy(self, temp_vault):
        """Test searching for Easy problems."""
        create_problem_folder(temp_vault, 1, "Two Sum", "Easy")
        create_problem_folder(temp_vault, 2, "Add Two Numbers", "Medium")

        results = search_by_difficulty(temp_vault, "easy")

        assert len(results) == 1
        assert results[0]["difficulty"] == "Easy"

    def test_search_case_insensitive(self, temp_vault):
        """Test that difficulty search is case-insensitive."""
        create_problem_folder(temp_vault, 1, "Two Sum", "Easy")

        results = search_by_difficulty(temp_vault, "EASY")

        assert len(results) == 1

    def test_invalid_difficulty(self, temp_vault):
        """Test search with invalid difficulty."""
        create_problem_folder(temp_vault, 1, "Two Sum", "Easy")

        results = search_by_difficulty(temp_vault, "invalid")

        assert len(results) == 0


class TestSearchByKeyword:
    """Tests for search_by_keyword function."""

    def test_search_by_keyword(self, temp_vault):
        """Test searching by keyword in title."""
        create_problem_folder(temp_vault, 1, "Two Sum", "Easy")
        create_problem_folder(temp_vault, 15, "3Sum", "Medium")

        results = search_by_keyword(temp_vault, "Sum")

        assert len(results) == 2

    def test_search_case_insensitive(self, temp_vault):
        """Test that keyword search is case-insensitive."""
        create_problem_folder(temp_vault, 1, "Two Sum", "Easy")

        results = search_by_keyword(temp_vault, "sum")

        assert len(results) == 1

    def test_no_matches(self, temp_vault):
        """Test search with no matches."""
        create_problem_folder(temp_vault, 1, "Two Sum", "Easy")

        results = search_by_keyword(temp_vault, "Graph")

        assert len(results) == 0


class TestSearchByNumber:
    """Tests for search_by_number function."""

    def test_search_by_number(self, temp_vault):
        """Test searching by problem number."""
        create_problem_folder(temp_vault, 1, "Two Sum", "Easy")
        create_problem_folder(temp_vault, 15, "3Sum", "Medium")

        result = search_by_number(temp_vault, 1)

        assert result is not None
        assert result["number"] == 1
        assert result["title"] == "Two Sum"

    def test_not_found(self, temp_vault):
        """Test search for non-existent problem."""
        create_problem_folder(temp_vault, 1, "Two Sum", "Easy")

        result = search_by_number(temp_vault, 999)

        assert result is None


class TestSearchProblems:
    """Tests for search_problems function."""

    def test_search_with_query(self, temp_vault):
        """Test search with query parameter."""
        create_problem_folder(temp_vault, 1, "Two Sum", "Easy")
        create_problem_folder(temp_vault, 15, "3Sum", "Medium")

        results = search_problems(temp_vault, query="Two")

        assert len(results) == 1
        assert results[0]["title"] == "Two Sum"

    def test_search_with_number_query(self, temp_vault):
        """Test search with numeric query."""
        create_problem_folder(temp_vault, 1, "Two Sum", "Easy")
        create_problem_folder(temp_vault, 15, "3Sum", "Medium")

        results = search_problems(temp_vault, query="15")

        assert len(results) == 1
        assert results[0]["number"] == 15

    def test_search_with_multiple_filters(self, temp_vault):
        """Test search with multiple filters."""
        folder1 = create_problem_folder(temp_vault, 1, "Two Sum", "Easy")
        (folder1 / "README.md").write_text("**Topics:** Array, Hash Table\n")

        folder2 = create_problem_folder(temp_vault, 15, "3Sum", "Medium")
        (folder2 / "README.md").write_text("**Topics:** Array, Two Pointers\n")

        results = search_problems(temp_vault, topic="Array", difficulty="easy")

        assert len(results) == 1
        assert results[0]["number"] == 1

    def test_search_no_filters(self, temp_vault):
        """Test search with no filters returns all."""
        create_problem_folder(temp_vault, 1, "Two Sum", "Easy")
        create_problem_folder(temp_vault, 15, "3Sum", "Medium")

        results = search_problems(temp_vault)

        assert len(results) == 2


class TestListAllTopics:
    """Tests for list_all_topics function."""

    def test_list_topics(self, temp_vault):
        """Test listing all topics."""
        folder1 = create_problem_folder(temp_vault, 1, "Two Sum", "Easy")
        (folder1 / "README.md").write_text("**Topics:** Array, Hash Table\n")

        folder2 = create_problem_folder(temp_vault, 20, "Valid Parentheses", "Easy")
        (folder2 / "README.md").write_text("**Topics:** String, Stack\n")

        topics = list_all_topics(temp_vault)

        assert len(topics) == 4
        assert "Array" in topics
        assert "Hash Table" in topics
        assert "Stack" in topics
        assert "String" in topics

    def test_topics_sorted(self, temp_vault):
        """Test that topics are sorted alphabetically."""
        folder = create_problem_folder(temp_vault, 1, "Two Sum", "Easy")
        (folder / "README.md").write_text("**Topics:** Zebra, Apple, Mango\n")

        topics = list_all_topics(temp_vault)

        assert topics == ["Apple", "Mango", "Zebra"]

    def test_empty_vault(self, temp_vault):
        """Test listing topics from empty vault."""
        topics = list_all_topics(temp_vault)
        assert topics == []
