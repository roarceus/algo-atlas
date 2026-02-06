"""Tests for the Rich-based logger module."""

import pytest

from algo_atlas.utils.logger import (
    Logger,
    get_logger,
    reset_logger,
    _CHECK,
    _CROSS,
    _BULLET,
    _ARROW,
)


@pytest.fixture(autouse=True)
def reset_global_logger():
    """Reset the global logger before and after each test."""
    reset_logger()
    yield
    reset_logger()


class TestLogger:
    """Tests for Logger class."""

    def test_create_logger(self):
        """Test creating a logger instance."""
        logger = Logger()
        assert logger.verbose is False
        assert logger.console is not None

    def test_create_verbose_logger(self):
        """Test creating a verbose logger."""
        logger = Logger(verbose=True)
        assert logger.verbose is True

    def test_success_output(self, capsys):
        """Test success message output."""
        logger = Logger()
        logger.success("Test passed")
        captured = capsys.readouterr()
        assert "Test passed" in captured.out
        assert _CHECK in captured.out

    def test_error_output(self, capsys):
        """Test error message output."""
        logger = Logger()
        logger.error("Test failed")
        captured = capsys.readouterr()
        assert "Test failed" in captured.out
        assert _CROSS in captured.out

    def test_warning_output(self, capsys):
        """Test warning message output."""
        logger = Logger()
        logger.warning("Warning message")
        captured = capsys.readouterr()
        assert "Warning message" in captured.out
        assert "!" in captured.out

    def test_info_output(self, capsys):
        """Test info message output."""
        logger = Logger()
        logger.info("Info message")
        captured = capsys.readouterr()
        assert "Info message" in captured.out
        assert _BULLET in captured.out

    def test_step_output(self, capsys):
        """Test step message output."""
        logger = Logger()
        logger.step("Step message")
        captured = capsys.readouterr()
        assert "Step message" in captured.out
        assert _ARROW in captured.out

    def test_debug_output_verbose(self, capsys):
        """Test debug message output in verbose mode."""
        logger = Logger(verbose=True)
        logger.debug("Debug message")
        captured = capsys.readouterr()
        assert "Debug message" in captured.out

    def test_debug_output_not_verbose(self, capsys):
        """Test debug message is hidden when not verbose."""
        logger = Logger(verbose=False)
        logger.debug("Debug message")
        captured = capsys.readouterr()
        assert "Debug message" not in captured.out

    def test_header_output(self, capsys):
        """Test header message output."""
        logger = Logger()
        logger.header("Test Header")
        captured = capsys.readouterr()
        assert "Test Header" in captured.out

    def test_blank_output(self, capsys):
        """Test blank line output."""
        logger = Logger()
        logger.blank()
        captured = capsys.readouterr()
        assert captured.out == "\n"

    def test_progress_start_and_end_success(self, capsys):
        """Test progress start and end with success."""
        logger = Logger()
        logger.progress_start("Loading")
        logger.progress_end(success=True)
        captured = capsys.readouterr()
        assert "Loading" in captured.out
        assert _CHECK in captured.out

    def test_progress_start_and_end_failure(self, capsys):
        """Test progress start and end with failure."""
        logger = Logger()
        logger.progress_start("Loading")
        logger.progress_end(success=False)
        captured = capsys.readouterr()
        assert "Loading" in captured.out
        assert _CROSS in captured.out

    def test_table_output(self, capsys):
        """Test table output."""
        logger = Logger()
        logger.table(
            title="Test Table",
            columns=["Name", "Value"],
            rows=[["foo", "bar"], ["baz", "qux"]],
        )
        captured = capsys.readouterr()
        assert "Test Table" in captured.out
        assert "Name" in captured.out
        assert "Value" in captured.out
        assert "foo" in captured.out
        assert "bar" in captured.out

    def test_rule_output(self, capsys):
        """Test rule output."""
        logger = Logger()
        logger.rule("Section")
        captured = capsys.readouterr()
        assert "Section" in captured.out

    def test_rule_output_no_title(self, capsys):
        """Test rule output without title."""
        logger = Logger()
        logger.rule()
        captured = capsys.readouterr()
        # Rule should produce some output (horizontal line)
        assert len(captured.out) > 0

    def test_status_context_manager(self, capsys):
        """Test status context manager."""
        logger = Logger()
        with logger.status("Working..."):
            pass
        # Status spinner doesn't capture well in tests, just verify no error


class TestGetLogger:
    """Tests for get_logger function."""

    def test_get_logger_returns_logger(self):
        """Test get_logger returns a Logger instance."""
        logger = get_logger()
        assert isinstance(logger, Logger)

    def test_get_logger_singleton(self):
        """Test get_logger returns the same instance."""
        logger1 = get_logger()
        logger2 = get_logger()
        assert logger1 is logger2

    def test_get_logger_verbose(self):
        """Test get_logger with verbose flag."""
        logger = get_logger(verbose=True)
        assert logger.verbose is True


class TestResetLogger:
    """Tests for reset_logger function."""

    def test_reset_logger(self):
        """Test reset_logger creates new instance."""
        logger1 = get_logger()
        reset_logger()
        logger2 = get_logger()
        assert logger1 is not logger2
