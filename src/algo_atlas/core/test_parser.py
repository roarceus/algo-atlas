"""Test case input/output parsing for LeetCode solutions."""

import ast
import json
from typing import Any


def _parse_test_input(input_str: str) -> list[Any]:
    """Parse test case input string into Python objects.

    Args:
        input_str: Raw input string (may be multiple lines for multiple args).
                   Handles formats like:
                   - Multi-line: each arg on its own line
                   - LeetCode format: "nums = [2,7,11,15], target = 9"

    Returns:
        List of parsed arguments.
    """
    args = []
    input_str = input_str.strip()

    # Check if it's LeetCode's "var = value, var2 = value2" format
    if "=" in input_str and not input_str.startswith("["):
        # Parse LeetCode example format: "nums = [2,7,11,15], target = 9"
        # Split by comma, but respect brackets/braces
        parts = _split_leetcode_input(input_str)
        for part in parts:
            part = part.strip()
            if "=" in part:
                # Extract value after "="
                _, value = part.split("=", 1)
                value = value.strip()
                parsed = _parse_single_value(value)
                args.append(parsed)
        return args

    # Multi-line format: each arg on its own line
    lines = input_str.split("\n")

    for line in lines:
        line = line.strip()
        if not line:
            continue

        parsed = _parse_single_value(line)
        args.append(parsed)

    return args


def _split_leetcode_input(input_str: str) -> list[str]:
    """Split LeetCode input format respecting brackets.

    Args:
        input_str: String like "nums = [2,7,11,15], target = 9"

    Returns:
        List of parts like ["nums = [2,7,11,15]", "target = 9"]
    """
    parts = []
    current = []
    depth = 0

    for char in input_str:
        if char in "([{":
            depth += 1
            current.append(char)
        elif char in ")]}":
            depth -= 1
            current.append(char)
        elif char == "," and depth == 0:
            parts.append("".join(current))
            current = []
        else:
            current.append(char)

    if current:
        parts.append("".join(current))

    return parts


def _parse_single_value(value: str) -> Any:
    """Parse a single value string into a Python object.

    Args:
        value: Value string to parse.

    Returns:
        Parsed Python object.
    """
    value = value.strip()

    try:
        # Try JSON parsing first
        return json.loads(value)
    except json.JSONDecodeError:
        pass

    try:
        # Try Python literal eval
        return ast.literal_eval(value)
    except (ValueError, SyntaxError):
        pass

    # Return as string if all else fails
    return value


def _parse_expected_output(output_str: str) -> Any:
    """Parse expected output string into Python object.

    Args:
        output_str: Raw output string.

    Returns:
        Parsed output value.
    """
    output_str = output_str.strip()

    try:
        return json.loads(output_str)
    except json.JSONDecodeError:
        try:
            return ast.literal_eval(output_str)
        except (ValueError, SyntaxError):
            return output_str
