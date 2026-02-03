# AlgoAtlas

[![CI](https://github.com/roarceus/algo-atlas/actions/workflows/ci.yml/badge.svg)](https://github.com/roarceus/algo-atlas/actions/workflows/ci.yml)
[![Code Quality](https://github.com/roarceus/algo-atlas/actions/workflows/code-quality.yml/badge.svg)](https://github.com/roarceus/algo-atlas/actions/workflows/code-quality.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A CLI tool that generates comprehensive documentation for your LeetCode solutions using Claude AI.

## Architecture

AlgoAtlas uses a **two-repository architecture**:
- **algo-atlas** (this repo) - The CLI tool/application
- **algo-atlas-vault** - Separate repository for storing documented solutions

This separation keeps the tool code separate from your solutions, making the vault repository clean and portfolio-ready.

## Features

### Core Features
- **LeetCode Scraper** - Fetch problem details via GraphQL API with user-agent rotation
- **Solution Verifier** - Syntax checking and test case execution with timeout protection
- **AI Documentation** - Generate detailed explanations using Claude Code CLI
- **Organized Vault** - Store solutions by difficulty (Easy/Medium/Hard)
- **Interactive CLI** - Colored console output with progress indicators

### Vault Automation
- **Auto-update Stats** - Automatically update vault README with problem counts
- **Branch-per-Problem** - Create unique branches: `add/{number}-{slug}-{timestamp}`
- **Auto-create PR** - Generate pull requests with problem details and approach preview
- **PR Labels** - Auto-apply labels based on difficulty (`easy`, `medium`, `hard`) and solution type (`new-solution`, `alternative-solution`)

### Additional Features
- **Dry-run Mode** - Preview documentation without saving (`--dry-run`)
- **Duplicate Detection** - Warns if problem exists, supports alternative solutions
- **Topic Index** - Auto-generate topic-based index in vault README
- **LeetCode Format Parsing** - Handles `nums = [2,7,11,15], target = 9` format

## Implementation Status

| Phase | Description | Status |
|-------|-------------|--------|
| **Phase 1** | Core Features (Scraper, Verifier, Generator, CLI) | Completed |
| **Phase 1.5** | Bug Fixes (Input parsing, Claude output cleanup) | Completed |
| **Phase 2** | Vault Automation (Stats, Branches, PRs, Labels) | Completed |
| **Phase 3** | Additional Features (Dry-run, Duplicates, Topic Index) | Completed |

## Installation

### Prerequisites

- Python 3.10 or higher
- [Claude Code CLI](https://github.com/anthropics/claude-code) installed and configured
- [GitHub CLI](https://cli.github.com/) (for PR creation features)

### Install from source

```bash
git clone https://github.com/roarceus/algo-atlas.git
cd algo-atlas
pip install -e .
```

### Install dependencies only

```bash
pip install -r requirements.txt
```

## Configuration

1. Copy the example config file:

```bash
cp config/config.yaml.example config/config.yaml
```

2. Edit `config/config.yaml` with your settings:

```yaml
# Path to your algo-atlas-vault repository
vault_path: "/path/to/algo-atlas-vault"

leetcode:
  timeout: 30
  max_retries: 3
  retry_delay: 2

verifier:
  execution_timeout: 5
```

3. Set up your vault repository:

```bash
# Create vault as sibling directory
cd ..
mkdir algo-atlas-vault && cd algo-atlas-vault
git init
mkdir Easy Medium Hard
echo "# AlgoAtlas Vault" > README.md
git add . && git commit -m "Initial commit"
git remote add origin <your-vault-repo-url>
git push -u origin main
```

**Vault Structure:**

```
algo-atlas-vault/
├── Easy/
│   └── 1. Two Sum/
│       ├── solution.py
│       └── README.md
├── Medium/
│   └── 2. Add Two Numbers/
│       ├── solution.py
│       └── README.md
├── Hard/
└── README.md              # Auto-updated with statistics and topic index
```

## Usage

Run the CLI:

```bash
python -m algo_atlas
```

### Workflow

1. **Startup Checks** - Verifies Claude CLI and vault configuration
2. **Enter URL** - Paste a LeetCode problem URL
3. **Provide Solution** - Paste code or provide a file path
4. **Verification** - Syntax check and test case execution
5. **Documentation** - Claude generates comprehensive README
6. **Git Workflow**:
   - Creates branch: `add/{number}-{slug}-{YYMMDD}-{HHMM}`
   - Saves files to vault in organized structure
   - Updates vault README with statistics
   - Commits and pushes changes
   - Creates PR with labels and metadata

### Example Session

```
AlgoAtlas
---------
 * Running startup checks...

 + Claude CLI installed
 + Vault configured: /path/to/algo-atlas-vault

? Enter LeetCode problem URL (or 'q' to quit): https://leetcode.com/problems/two-sum/

 -> Scraping problem from LeetCode...
 + Found: 1. Two Sum (Easy)
 * Topics: Array, Hash Table

Enter solution code:
  - Paste a file path (e.g., solution.py)
  - Or paste code directly, then enter 'END' on a new line

class Solution:
    def twoSum(self, nums, target):
        seen = {}
        for i, n in enumerate(nums):
            if target - n in seen:
                return [seen[target - n], i]
            seen[n] = i
END

 + Code received

 -> Verifying solution...
 + Syntax valid
 + All tests passed (3/3)

 -> Generating documentation with Claude...
 + Documentation generated

 -> Saving to vault...
 + Created branch: add/1-two-sum-250130-1432
 + Saved: /path/to/vault/Easy/1. Two Sum/solution.py
 + Saved: /path/to/vault/Easy/1. Two Sum/README.md
 + Updated vault statistics
 + Committed and pushed changes
 + Created PR: https://github.com/user/algo-atlas-vault/pull/1

? Process another problem? [Y/n]:
```

### Dry-run Mode

Preview documentation without saving:

```bash
python -m algo_atlas --dry-run
```

## Project Structure

```
algo-atlas/
├── src/algo_atlas/
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py              # Interactive CLI
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py     # Configuration management
│   ├── core/
│   │   ├── __init__.py
│   │   ├── generator.py    # Claude integration
│   │   ├── scraper.py      # LeetCode GraphQL scraper
│   │   └── verifier.py     # Solution verification
│   └── utils/
│       ├── __init__.py
│       ├── file_manager.py # Vault file operations
│       ├── logger.py       # Colored console output
│       └── prompts.py      # Claude prompt templates
├── tests/
├── config/
│   └── config.yaml.example
├── docs/
├── pyproject.toml
└── README.md
```

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/roarceus/algo-atlas.git
cd algo-atlas

# Install with dev dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Running Tests

```bash
pytest tests/ -v
```

### Code Quality

```bash
# Format code
black src/ tests/
isort src/ tests/

# Lint
flake8 src/ tests/
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feat/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: add amazing feature'`)
4. Push to the branch (`git push origin feat/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [LeetCode](https://leetcode.com/) for the problem platform
- [Anthropic](https://www.anthropic.com/) for Claude AI
- [Claude Code](https://github.com/anthropics/claude-code) for the CLI tool
