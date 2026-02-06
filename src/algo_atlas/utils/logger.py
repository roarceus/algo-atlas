"""Rich-based logging utilities for AlgoAtlas."""

import sys
from contextlib import contextmanager
from typing import Generator, Optional

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.status import Status
from rich.table import Table
from rich.text import Text
from rich.theme import Theme

# Custom theme for AlgoAtlas
ALGOATLAS_THEME = Theme({
    "success": "bold green",
    "error": "bold red",
    "warning": "bold yellow",
    "info": "blue",
    "step": "cyan",
    "header": "bold cyan",
    "debug": "dim",
})


def _supports_unicode() -> bool:
    """Check if the terminal supports Unicode output."""
    try:
        encoding = sys.stdout.encoding or ""
        return encoding.lower() in ("utf-8", "utf8")
    except AttributeError:
        return False


# Use ASCII-safe symbols when Unicode is not supported
_UNICODE = _supports_unicode()
_CHECK = "\u2713" if _UNICODE else "+"
_CROSS = "\u2717" if _UNICODE else "x"
_BULLET = "\u2022" if _UNICODE else "*"
_ARROW = "\u2192" if _UNICODE else "->"


class Logger:
    """Rich-based console logger with progress indicators."""

    def __init__(self, verbose: bool = False):
        """Initialize logger.

        Args:
            verbose: Enable verbose output.
        """
        self.verbose = verbose
        self.console = Console(theme=ALGOATLAS_THEME, legacy_windows=False)
        self._status: Optional[Status] = None

    def success(self, message: str) -> None:
        """Print success message with green checkmark."""
        self.console.print(f" [success]{_CHECK}[/success] [success]{message}[/success]")

    def error(self, message: str) -> None:
        """Print error message with red X."""
        self.console.print(f" [error]{_CROSS}[/error] [error]{message}[/error]")

    def warning(self, message: str) -> None:
        """Print warning message with yellow indicator."""
        self.console.print(f" [warning]![/warning] [warning]{message}[/warning]")

    def info(self, message: str) -> None:
        """Print info message with blue bullet."""
        self.console.print(f" [info]{_BULLET}[/info] {message}")

    def step(self, message: str) -> None:
        """Print step message with cyan arrow."""
        self.console.print(f" [step]{_ARROW}[/step] {message}")

    def debug(self, message: str) -> None:
        """Print debug message (only if verbose)."""
        if self.verbose:
            self.console.print(f"   [debug]{message}[/debug]")

    def header(self, message: str) -> None:
        """Print header message with panel."""
        self.console.print()
        self.console.print(Panel(
            Text(message, style="header", justify="center"),
            border_style="cyan",
            padding=(0, 2),
        ))

    def blank(self) -> None:
        """Print blank line."""
        self.console.print()

    def prompt(self, message: str, default: Optional[str] = None) -> str:
        """Display prompt and get user input.

        Args:
            message: Prompt message.
            default: Default value if user presses Enter.

        Returns:
            User input or default value.
        """
        return Prompt.ask(f"[cyan]?[/cyan] {message}", default=default or "")

    def confirm(self, message: str, default: bool = True) -> bool:
        """Display confirmation prompt.

        Args:
            message: Confirmation message.
            default: Default value if user presses Enter.

        Returns:
            True if confirmed, False otherwise.
        """
        return Confirm.ask(f"[cyan]?[/cyan] {message}", default=default)

    def progress_start(self, message: str) -> None:
        """Print progress start message (no newline)."""
        self.console.print(f" [info]{_BULLET}[/info] {message}...", end="")

    def progress_end(self, success: bool = True) -> None:
        """Complete progress with success/failure indicator."""
        if success:
            self.console.print(f" [success]{_CHECK}[/success]")
        else:
            self.console.print(f" [error]{_CROSS}[/error]")

    @contextmanager
    def status(self, message: str) -> Generator[Status, None, None]:
        """Context manager for showing a spinner during long operations.

        Args:
            message: Status message to display.

        Yields:
            Status object that can be updated.

        Example:
            with logger.status("Processing...") as status:
                do_work()
                status.update("Almost done...")
        """
        with self.console.status(
            f"[step]{message}[/step]",
            spinner="line" if not _UNICODE else "dots",
        ) as status:
            yield status

    def table(
        self,
        title: str,
        columns: list[str],
        rows: list[list[str]],
        styles: Optional[list[str]] = None,
    ) -> None:
        """Print a formatted table.

        Args:
            title: Table title.
            columns: List of column headers.
            rows: List of row data (each row is a list of strings).
            styles: Optional list of styles for each column.
        """
        table = Table(title=title, border_style="cyan", safe_box=not _UNICODE)

        for i, col in enumerate(columns):
            style = styles[i] if styles and i < len(styles) else None
            table.add_column(col, style=style)

        for row in rows:
            table.add_row(*row)

        self.console.print(table)

    def rule(self, title: str = "") -> None:
        """Print a horizontal rule with optional title.

        Args:
            title: Optional title to display in the rule.
        """
        self.console.rule(title, style="cyan")


# Global logger instance
_logger: Optional[Logger] = None


def get_logger(verbose: bool = False) -> Logger:
    """Get or create global logger instance.

    Args:
        verbose: Enable verbose output.

    Returns:
        Logger instance.
    """
    global _logger
    if _logger is None:
        _logger = Logger(verbose=verbose)
    return _logger


def reset_logger() -> None:
    """Reset the global logger instance.

    Useful for testing or reinitializing with different settings.
    """
    global _logger
    _logger = None
