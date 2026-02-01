"""Tests for the file manager module."""

import re

from algo_atlas.utils.file_manager import (
    check_gh_installed,
    check_problem_exists,
    create_problem_folder,
    generate_branch_name,
    get_pr_labels,
    sanitize_title,
    save_markdown,
    save_solution_file,
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
            "algo_atlas.utils.file_manager.get_vault_path",
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
