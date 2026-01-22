"""Colored logging utilities for AlgoAtlas."""

import sys
from typing import Optional

from colorama import Fore, Style, init

# Initialize colorama for Windows support
init(autoreset=True)


def _supports_unicode() -> bool:
    """Check if the terminal supports Unicode output."""
    try:
        encoding = sys.stdout.encoding or ""
        return encoding.lower() in ("utf-8", "utf8")
    except AttributeError:
        return False


class Logger:
    """Colored console logger with progress indicators."""

    # Use ASCII-safe symbols for Windows compatibility
    _CHECK = "+" if not _supports_unicode() else "\u2713"
    _CROSS = "x" if not _supports_unicode() else "\u2717"
    _BULLET = "*" if not _supports_unicode() else "\u2022"
    _ARROW = "->" if not _supports_unicode() else "\u2192"

    # Status indicators
    SUCCESS = f"{Fore.GREEN}{_CHECK}{Style.RESET_ALL}"
    FAILURE = f"{Fore.RED}{_CROSS}{Style.RESET_ALL}"
    WARNING = f"{Fore.YELLOW}!{Style.RESET_ALL}"
    INFO = f"{Fore.BLUE}{_BULLET}{Style.RESET_ALL}"
    ARROW = f"{Fore.CYAN}{_ARROW}{Style.RESET_ALL}"

    def __init__(self, verbose: bool = False):
        """Initialize logger.

        Args:
            verbose: Enable verbose output.
        """
        self.verbose = verbose

    def success(self, message: str) -> None:
        """Print success message with green checkmark."""
        print(f" {self.SUCCESS} {Fore.GREEN}{message}{Style.RESET_ALL}")

    def error(self, message: str) -> None:
        """Print error message with red X."""
        print(f" {self.FAILURE} {Fore.RED}{message}{Style.RESET_ALL}")

    def warning(self, message: str) -> None:
        """Print warning message with yellow indicator."""
        print(f" {self.WARNING} {Fore.YELLOW}{message}{Style.RESET_ALL}")

    def info(self, message: str) -> None:
        """Print info message with blue bullet."""
        print(f" {self.INFO} {message}")

    def step(self, message: str) -> None:
        """Print step message with cyan arrow."""
        print(f" {self.ARROW} {message}")

    def debug(self, message: str) -> None:
        """Print debug message (only if verbose)."""
        if self.verbose:
            print(f"   {Fore.LIGHTBLACK_EX}{message}{Style.RESET_ALL}")

    def header(self, message: str) -> None:
        """Print header message."""
        print(f"\n{Fore.CYAN}{Style.BRIGHT}{message}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'-' * len(message)}{Style.RESET_ALL}")

    def blank(self) -> None:
        """Print blank line."""
        print()

    def prompt(self, message: str, default: Optional[str] = None) -> str:
        """Display prompt and get user input.

        Args:
            message: Prompt message.
            default: Default value if user presses Enter.

        Returns:
            User input or default value.
        """
        if default:
            prompt_text = f"{Fore.CYAN}? {message} [{default}]: {Style.RESET_ALL}"
        else:
            prompt_text = f"{Fore.CYAN}? {message}: {Style.RESET_ALL}"

        response = input(prompt_text).strip()
        return response if response else (default or "")

    def confirm(self, message: str, default: bool = True) -> bool:
        """Display confirmation prompt.

        Args:
            message: Confirmation message.
            default: Default value if user presses Enter.

        Returns:
            True if confirmed, False otherwise.
        """
        default_hint = "Y/n" if default else "y/N"
        prompt_text = f"{Fore.CYAN}? {message} [{default_hint}]: {Style.RESET_ALL}"

        response = input(prompt_text).strip().lower()

        if not response:
            return default
        return response in ("y", "yes")

    def progress_start(self, message: str) -> None:
        """Print progress start message (no newline)."""
        print(f" {self.INFO} {message}...", end="", flush=True)

    def progress_end(self, success: bool = True) -> None:
        """Complete progress with success/failure indicator."""
        if success:
            print(f" {self.SUCCESS}")
        else:
            print(f" {self.FAILURE}")


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
