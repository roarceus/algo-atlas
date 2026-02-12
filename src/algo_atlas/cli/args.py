"""Command-line argument parsing for AlgoAtlas."""

import argparse


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        Parsed arguments namespace.
    """
    parser = argparse.ArgumentParser(
        prog="algo-atlas",
        description="Generate documentation for LeetCode solutions",
    )

    # Create subcommands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Default run command (no subcommand needed)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview generated documentation without saving to vault",
    )
    parser.add_argument(
        "-l", "--language",
        default=None,
        help="Language slug for solution (e.g., python3, javascript). Defaults to config setting.",
    )

    # Search subcommand
    search_parser = subparsers.add_parser(
        "search",
        help="Search problems in vault",
    )
    search_parser.add_argument(
        "query",
        nargs="?",
        default=None,
        help="Search query (problem number or keyword in title)",
    )
    search_parser.add_argument(
        "-t", "--topic",
        help="Filter by topic (partial match)",
    )
    search_parser.add_argument(
        "-d", "--difficulty",
        choices=["easy", "medium", "hard"],
        help="Filter by difficulty",
    )
    search_parser.add_argument(
        "--list-topics",
        action="store_true",
        help="List all topics in vault",
    )

    # Batch subcommand
    batch_parser = subparsers.add_parser(
        "batch",
        help="Process multiple problems from a batch file",
    )
    batch_parser.add_argument(
        "file",
        help="Path to batch file (.txt or .json)",
    )
    batch_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview generated documentation without saving to vault",
    )
    batch_parser.add_argument(
        "--skip-verification",
        action="store_true",
        help="Skip solution verification (syntax check and test cases)",
    )
    batch_parser.add_argument(
        "--continue-on-error",
        action="store_true",
        help="Continue processing remaining items if one fails",
    )
    batch_parser.add_argument(
        "-l", "--language",
        default=None,
        help="Language slug for solutions (e.g., python3, javascript). Defaults to config setting.",
    )

    return parser.parse_args()
