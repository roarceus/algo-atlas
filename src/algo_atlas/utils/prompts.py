"""Prompt templates for Claude AI integration."""

DOCUMENTATION_PROMPT = """You are a technical documentation expert. Generate documentation for this LeetCode problem solution using the EXACT structure below.

## Problem Information
- **Number**: {number}
- **Title**: {title}
- **Difficulty**: {difficulty}
- **Topics**: {topics}

## Problem Description
{description}

## Constraints
{constraints}

## Examples
{examples}

## Solution Code
```python
{solution_code}
```

---

Generate a README.md using this EXACT structure. Every section is REQUIRED and must appear in this order:

# [Problem Title]

## Overview
- **Difficulty**: [Easy/Medium/Hard]
- **Topics**: [comma-separated list of topics]
- **LeetCode Link**: [URL]

## Problem Statement
[2-3 sentence summary of what the problem asks]

## Prerequisites
[List 2-4 concepts, data structures, or patterns one should understand before attempting this problem. Be specific.]

Example:
- Hash Table fundamentals (insertion, lookup)
- Understanding of complement/two-pointer technique
- Array traversal with index tracking

## Approach
[Name the technique/algorithm used and explain the strategy in 2-3 paragraphs]

## Visual Example
[Step-by-step walkthrough using ONE example from the problem. Use ASCII art, tables, or formatted text to show how the algorithm processes the input. Show the state at each step.]

Example format:
```
Input: nums = [2,7,11,15], target = 9

Step 1: i=0, num=2
        complement = 9 - 2 = 7
        seen = {{}}
        7 not in seen, add 2 to seen
        seen = {{2: 0}}

Step 2: i=1, num=7
        complement = 9 - 7 = 2
        seen = {{2: 0}}
        2 in seen! Return [0, 1]

Output: [0, 1]
```

## Complexity Analysis

### Time Complexity: O(n)
[Explanation - use O(n), O(n^2), O(log n), O(n log n) format, NOT special characters]

### Space Complexity: O(n)
[Explanation - use O(n), O(n^2), O(1) format, NOT special characters]

## Step-by-Step Code Walkthrough
[Break down the code into logical parts with explanations]

## Key Insights
[Bullet points of what makes this solution work and any clever observations]

## Common Pitfalls
[List 2-4 common mistakes or edge cases people often miss when solving this problem]

Example:
- Forgetting to handle empty input
- Using the same element twice
- Off-by-one errors in index handling
- Not considering negative numbers

---

RULES:
1. Use the EXACT section headings shown above in the EXACT order
2. The Visual Example MUST show actual step-by-step execution with state changes
3. Use the first example from the problem for the visual walkthrough
4. Keep explanations concise but complete
5. Do NOT add extra sections or change the order
6. For complexity notation, use ONLY: O(1), O(log n), O(n), O(n log n), O(n^2), O(n^3), O(2^n)
   Do NOT use special characters like superscripts or Unicode symbols
7. Use plain ASCII characters only. No special arrows, no Unicode symbols, no superscripts

IMPORTANT: Output ONLY the raw markdown content. Do NOT include:
- Any preamble like "Here's the README..." or "I've prepared..."
- Code fences around the markdown (no ```markdown blocks)
- Any closing remarks or commentary

Start directly with: # {title}
"""

EXPECTED_OUTPUTS_PROMPT = """You are solving a LeetCode problem. Given the problem description and test case inputs, compute the expected outputs.

## Problem Information
- **Number**: {number}
- **Title**: {title}

## Problem Description
{description}

## Test Case Inputs
{test_inputs}

---

For each test case input, provide the expected output. Return ONLY a JSON array of the expected outputs in order, nothing else.

Example format: [output1, output2, output3]

If the output is an array, include it as-is: [[1,2], [3,4], 5]
"""


def get_documentation_prompt(
    number: int,
    title: str,
    difficulty: str,
    topics: list[str],
    description: str,
    constraints: list[str],
    examples: list[dict],
    solution_code: str,
) -> str:
    """Format the documentation generation prompt.

    Args:
        number: Problem number.
        title: Problem title.
        difficulty: Problem difficulty.
        topics: List of topic tags.
        description: Problem description.
        constraints: List of constraints.
        examples: List of example dicts with input/output.
        solution_code: Python solution code.

    Returns:
        Formatted prompt string.
    """
    # Format topics
    topics_str = ", ".join(topics) if topics else "N/A"

    # Format constraints
    constraints_str = "\n".join(f"- {c}" for c in constraints) if constraints else "N/A"

    # Format examples
    examples_parts = []
    for ex in examples:
        ex_num = ex.get("number", "?")
        ex_input = ex.get("input", "N/A")
        ex_output = ex.get("output", "N/A")
        ex_explanation = ex.get("explanation", "")

        example_text = f"**Example {ex_num}:**\n- Input: {ex_input}\n- Output: {ex_output}"
        if ex_explanation:
            example_text += f"\n- Explanation: {ex_explanation}"
        examples_parts.append(example_text)

    examples_str = "\n\n".join(examples_parts) if examples_parts else "N/A"

    return DOCUMENTATION_PROMPT.format(
        number=number,
        title=title,
        difficulty=difficulty,
        topics=topics_str,
        description=description,
        constraints=constraints_str,
        examples=examples_str,
        solution_code=solution_code,
    )


def get_expected_outputs_prompt(
    number: int,
    title: str,
    description: str,
    test_inputs: list[str],
) -> str:
    """Format the expected outputs generation prompt.

    Args:
        number: Problem number.
        title: Problem title.
        description: Problem description.
        test_inputs: List of test case input strings.

    Returns:
        Formatted prompt string.
    """
    # Format test inputs
    inputs_str = "\n".join(f"Test {i+1}: {inp}" for i, inp in enumerate(test_inputs))

    return EXPECTED_OUTPUTS_PROMPT.format(
        number=number,
        title=title,
        description=description,
        test_inputs=inputs_str,
    )
