"""Prompt templates for Claude AI integration."""

DOCUMENTATION_PROMPT = """You are a technical documentation expert. Generate comprehensive documentation for this LeetCode problem solution.

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

Generate a README.md with the following sections:

1. **Problem Link** - LeetCode URL
2. **Problem Statement** - Brief summary (2-3 sentences)
3. **Approach** - Explain the algorithm/strategy used (be specific about the technique)
4. **Complexity Analysis**
   - Time Complexity: O(?) with explanation
   - Space Complexity: O(?) with explanation
5. **Code Walkthrough** - Step-by-step explanation of key parts
6. **Key Insights** - What makes this solution efficient or clever

Format the output as clean Markdown. Be concise but thorough. Focus on helping someone understand WHY the solution works, not just WHAT it does.

IMPORTANT: Output ONLY the raw markdown content. Do NOT include:
- Any preamble like "Here's the README..." or "I've prepared..."
- Code fences around the markdown (no ```markdown blocks)
- Any closing remarks or commentary

Start directly with the first heading (# Problem Link or similar).
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
