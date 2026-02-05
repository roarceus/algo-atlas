"""Tests for the CLI module."""

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from algo_atlas.cli import (
    BatchItem,
    BatchResult,
    parse_args,
    parse_batch_file,
    _parse_json_batch,
    _parse_text_batch,
)


class TestParseArgs:
    """Tests for parse_args function."""

    def test_no_args(self):
        """Test default behavior with no arguments."""
        with patch.object(sys, "argv", ["algo-atlas"]):
            args = parse_args()
            assert args.dry_run is False

    def test_dry_run_flag(self):
        """Test --dry-run flag."""
        with patch.object(sys, "argv", ["algo-atlas", "--dry-run"]):
            args = parse_args()
            assert args.dry_run is True

    def test_help_flag(self):
        """Test --help flag exits cleanly."""
        with patch.object(sys, "argv", ["algo-atlas", "--help"]):
            try:
                parse_args()
            except SystemExit as e:
                assert e.code == 0

    def test_batch_command(self):
        """Test batch command parsing."""
        with patch.object(sys, "argv", ["algo-atlas", "batch", "batch.txt"]):
            args = parse_args()
            assert args.command == "batch"
            assert args.file == "batch.txt"
            assert args.dry_run is False
            assert args.skip_verification is False
            assert args.continue_on_error is False

    def test_batch_with_flags(self):
        """Test batch command with all flags."""
        with patch.object(sys, "argv", [
            "algo-atlas", "batch", "batch.json",
            "--dry-run", "--skip-verification", "--continue-on-error"
        ]):
            args = parse_args()
            assert args.command == "batch"
            assert args.file == "batch.json"
            assert args.dry_run is True
            assert args.skip_verification is True
            assert args.continue_on_error is True

    def test_search_command(self):
        """Test search command parsing."""
        with patch.object(sys, "argv", ["algo-atlas", "search", "two-sum"]):
            args = parse_args()
            assert args.command == "search"
            assert args.query == "two-sum"


class TestBatchItem:
    """Tests for BatchItem dataclass."""

    def test_create_batch_item(self):
        """Test creating a BatchItem."""
        item = BatchItem(
            url="https://leetcode.com/problems/two-sum/",
            solution_path=Path("/path/to/solution.py"),
        )
        assert item.url == "https://leetcode.com/problems/two-sum/"
        assert item.solution_path == Path("/path/to/solution.py")


class TestBatchResult:
    """Tests for BatchResult dataclass."""

    def test_success_result(self):
        """Test successful BatchResult."""
        result = BatchResult(
            url="https://leetcode.com/problems/two-sum/",
            success=True,
            problem_title="1. Two Sum",
        )
        assert result.success is True
        assert result.error is None

    def test_failure_result(self):
        """Test failed BatchResult."""
        result = BatchResult(
            url="https://leetcode.com/problems/two-sum/",
            success=False,
            error="Failed to scrape",
        )
        assert result.success is False
        assert result.error == "Failed to scrape"


class TestParseTextBatch:
    """Tests for _parse_text_batch function."""

    def test_parse_basic_text(self, tmp_path):
        """Test parsing basic text format."""
        content = """https://leetcode.com/problems/two-sum/, solution1.py
https://leetcode.com/problems/valid-parentheses/, solution2.py"""

        items = _parse_text_batch(content, tmp_path)

        assert len(items) == 2
        assert items[0].url == "https://leetcode.com/problems/two-sum/"
        assert items[0].solution_path == tmp_path / "solution1.py"
        assert items[1].url == "https://leetcode.com/problems/valid-parentheses/"
        assert items[1].solution_path == tmp_path / "solution2.py"

    def test_parse_with_comments(self, tmp_path):
        """Test parsing text with comment lines."""
        content = """# This is a comment
https://leetcode.com/problems/two-sum/, solution.py
# Another comment"""

        items = _parse_text_batch(content, tmp_path)

        assert len(items) == 1
        assert items[0].url == "https://leetcode.com/problems/two-sum/"

    def test_parse_with_empty_lines(self, tmp_path):
        """Test parsing text with empty lines."""
        content = """https://leetcode.com/problems/two-sum/, solution1.py

https://leetcode.com/problems/valid-parentheses/, solution2.py

"""

        items = _parse_text_batch(content, tmp_path)

        assert len(items) == 2

    def test_parse_with_absolute_path(self, tmp_path):
        """Test parsing text with absolute path."""
        content = f"https://leetcode.com/problems/two-sum/, {tmp_path / 'solution.py'}"

        items = _parse_text_batch(content, tmp_path)

        assert len(items) == 1
        assert items[0].solution_path == tmp_path / "solution.py"

    def test_parse_invalid_format(self, tmp_path):
        """Test parsing invalid format raises error."""
        content = "https://leetcode.com/problems/two-sum/"  # Missing solution path

        with pytest.raises(ValueError, match="Expected 'URL, solution_path' format"):
            _parse_text_batch(content, tmp_path)

    def test_parse_empty_url(self, tmp_path):
        """Test parsing with empty URL raises error."""
        content = ", solution.py"

        with pytest.raises(ValueError, match="Missing URL"):
            _parse_text_batch(content, tmp_path)


class TestParseJsonBatch:
    """Tests for _parse_json_batch function."""

    def test_parse_basic_json(self, tmp_path):
        """Test parsing basic JSON format."""
        content = json.dumps([
            {"url": "https://leetcode.com/problems/two-sum/", "solution": "solution1.py"},
            {"url": "https://leetcode.com/problems/valid-parentheses/", "solution": "solution2.py"},
        ])

        items = _parse_json_batch(content, tmp_path)

        assert len(items) == 2
        assert items[0].url == "https://leetcode.com/problems/two-sum/"
        assert items[0].solution_path == tmp_path / "solution1.py"

    def test_parse_invalid_json(self, tmp_path):
        """Test parsing invalid JSON raises error."""
        content = "not valid json"

        with pytest.raises(ValueError, match="Invalid JSON format"):
            _parse_json_batch(content, tmp_path)

    def test_parse_not_array(self, tmp_path):
        """Test parsing non-array JSON raises error."""
        content = json.dumps({"url": "...", "solution": "..."})

        with pytest.raises(ValueError, match="must contain an array"):
            _parse_json_batch(content, tmp_path)

    def test_parse_missing_url(self, tmp_path):
        """Test parsing with missing URL raises error."""
        content = json.dumps([{"solution": "solution.py"}])

        with pytest.raises(ValueError, match="missing 'url' field"):
            _parse_json_batch(content, tmp_path)

    def test_parse_missing_solution(self, tmp_path):
        """Test parsing with missing solution raises error."""
        content = json.dumps([{"url": "https://leetcode.com/problems/two-sum/"}])

        with pytest.raises(ValueError, match="missing 'solution' field"):
            _parse_json_batch(content, tmp_path)


class TestParseBatchFile:
    """Tests for parse_batch_file function."""

    def test_parse_text_file(self, tmp_path):
        """Test parsing .txt batch file."""
        batch_file = tmp_path / "batch.txt"
        batch_file.write_text(
            "https://leetcode.com/problems/two-sum/, solution.py\n"
        )

        items = parse_batch_file(batch_file)

        assert len(items) == 1
        assert items[0].url == "https://leetcode.com/problems/two-sum/"

    def test_parse_json_file(self, tmp_path):
        """Test parsing .json batch file."""
        batch_file = tmp_path / "batch.json"
        batch_file.write_text(json.dumps([
            {"url": "https://leetcode.com/problems/two-sum/", "solution": "solution.py"}
        ]))

        items = parse_batch_file(batch_file)

        assert len(items) == 1
        assert items[0].url == "https://leetcode.com/problems/two-sum/"

    def test_parse_nonexistent_file(self, tmp_path):
        """Test parsing nonexistent file raises error."""
        batch_file = tmp_path / "nonexistent.txt"

        with pytest.raises(ValueError, match="Batch file not found"):
            parse_batch_file(batch_file)

    def test_parse_csv_as_text(self, tmp_path):
        """Test parsing .csv file as text format."""
        batch_file = tmp_path / "batch.csv"
        batch_file.write_text(
            "https://leetcode.com/problems/two-sum/, solution.py\n"
        )

        items = parse_batch_file(batch_file)

        assert len(items) == 1
