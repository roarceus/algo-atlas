"""Claude AI integration for documentation generation."""

import json
import shutil
import subprocess
from dataclasses import dataclass
from typing import Any, Optional

from algo_atlas.core.scraper import ProblemData
from algo_atlas.utils.prompts import get_documentation_prompt, get_expected_outputs_prompt


@dataclass
class GenerationResult:
    """Result of Claude generation."""

    success: bool
    content: Optional[str] = None
    error: Optional[str] = None


def check_claude_installed() -> bool:
    """Check if Claude CLI is installed and accessible.

    Returns:
        True if Claude CLI is available, False otherwise.
    """
    return shutil.which("claude") is not None


def call_claude(prompt: str, max_tokens: int = 4096) -> GenerationResult:
    """Call Claude CLI with a prompt.

    Args:
        prompt: The prompt to send to Claude.
        max_tokens: Maximum tokens in response.

    Returns:
        GenerationResult with response or error.
    """
    if not check_claude_installed():
        return GenerationResult(
            success=False,
            error="Claude CLI not installed. Install with: npm install -g @anthropic-ai/claude-code",
        )

    try:
        # Run claude with prompt via stdin
        result = subprocess.run(
            ["claude", "-p", prompt, "--output-format", "text"],
            capture_output=True,
            text=True,
            timeout=120,  # 2 minute timeout
        )

        if result.returncode != 0:
            return GenerationResult(
                success=False,
                error=f"Claude CLI error: {result.stderr}",
            )

        return GenerationResult(
            success=True,
            content=result.stdout.strip(),
        )

    except subprocess.TimeoutExpired:
        return GenerationResult(
            success=False,
            error="Claude CLI timed out after 120 seconds",
        )
    except FileNotFoundError:
        return GenerationResult(
            success=False,
            error="Claude CLI not found in PATH",
        )
    except Exception as e:
        return GenerationResult(
            success=False,
            error=f"Unexpected error: {str(e)}",
        )


def generate_documentation(
    problem: ProblemData,
    solution_code: str,
) -> GenerationResult:
    """Generate documentation for a LeetCode solution.

    Args:
        problem: Scraped problem data.
        solution_code: Python solution code.

    Returns:
        GenerationResult with markdown documentation.
    """
    prompt = get_documentation_prompt(
        number=problem.number,
        title=problem.title,
        difficulty=problem.difficulty,
        topics=problem.topic_tags,
        description=problem.description,
        constraints=problem.constraints,
        examples=problem.examples,
        solution_code=solution_code,
    )

    result = call_claude(prompt)

    if result.success and result.content:
        # Clean up the markdown if needed
        content = result.content.strip()

        # Remove markdown code fence if Claude wrapped the output
        if content.startswith("```markdown"):
            content = content[11:]
        if content.startswith("```md"):
            content = content[5:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]

        result.content = content.strip()

    return result


def generate_expected_outputs(
    problem: ProblemData,
    test_cases: list[str],
) -> Optional[list[Any]]:
    """Generate expected outputs for test cases using Claude.

    Args:
        problem: Scraped problem data.
        test_cases: List of test case input strings.

    Returns:
        List of expected outputs, or None if generation failed.
    """
    if not test_cases:
        return None

    prompt = get_expected_outputs_prompt(
        number=problem.number,
        title=problem.title,
        description=problem.description,
        test_inputs=test_cases,
    )

    result = call_claude(prompt)

    if not result.success or not result.content:
        return None

    # Parse JSON response
    try:
        content = result.content.strip()

        # Remove markdown code fence if present
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]

        outputs = json.loads(content.strip())

        if isinstance(outputs, list):
            return outputs

    except json.JSONDecodeError:
        pass

    return None


def build_readme_content(
    problem: ProblemData,
    documentation: str,
) -> str:
    """Build final README content with header.

    Args:
        problem: Problem data.
        documentation: Generated documentation markdown.

    Returns:
        Complete README content.
    """
    # Add problem header if not present
    header = f"# {problem.number}. {problem.title}\n\n"
    header += f"**Difficulty:** {problem.difficulty}\n\n"
    header += f"**Topics:** {', '.join(problem.topic_tags)}\n\n"
    header += f"**LeetCode Link:** [Problem]"
    header += f"(https://leetcode.com/problems/{problem.slug}/)\n\n"
    header += "---\n\n"

    # Check if documentation already has a title
    if documentation.startswith("#"):
        return documentation

    return header + documentation
