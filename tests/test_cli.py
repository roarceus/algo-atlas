"""Tests for the CLI module."""

import sys
from unittest.mock import patch

from algo_atlas.cli import parse_args


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
