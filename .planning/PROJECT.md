# AlgoAtlas

## What This Is

AlgoAtlas is a CLI tool that automates documenting LeetCode solutions. Given a problem URL and solution code, it scrapes the problem, verifies the solution, generates structured documentation via Claude AI, and saves it to a personal vault repository with an automatic PR. Supports 13 languages and is designed for developers who solve LeetCode problems regularly and want a searchable, well-formatted record of their work.

## Core Value

Turn a solved LeetCode problem into a documented, committed vault entry with a single command — no manual steps.

## Requirements

### Validated

- ✓ Scrape LeetCode problem data (title, difficulty, examples, test cases, code snippet) via GraphQL API — existing
- ✓ Verify solution syntax per language before documentation — existing
- ✓ Run solution against scraped test cases and report pass/fail — existing
- ✓ Generate structured documentation via Claude AI CLI — existing
- ✓ Save generated docs to vault (Easy/Medium/Hard directories) — existing
- ✓ Auto-commit and push vault changes, open PR on vault repo — existing
- ✓ Support 13 languages: Python, JavaScript, TypeScript, Java, C++, C, Go, Rust, C#, Kotlin, Swift, Ruby, PHP — existing
- ✓ Batch processing from .txt/.json file — existing
- ✓ Search vault by query, topic, difficulty — existing
- ✓ Status command showing config, vault, Claude CLI, language runtimes — existing
- ✓ --dry-run flag (preview docs without saving) — existing
- ✓ --verbose flag (debug output for scraper + generator) — existing

### Active

- [ ] Non-interactive mode: pass URL and solution file as positional CLI args — skip all prompts
- [ ] Problem caching: cache scraped problem data locally, skip network on re-runs for same problem
- [ ] Partial save on test failure: save docs with warning instead of hard failing when tests don't pass
- [ ] --update mode: re-generate and overwrite docs for a problem already in vault

### Out of Scope

- Vault analytics dashboard — useful but not blocking daily use; defer
- Interactive search (arrow-key navigation) — nice-to-have UX polish; defer
- Multi-language batch (per-row language column) — complex; not a daily-use blocker
- Environment variable config — defer; YAML config is sufficient for now
- Web UI / browser extension — not aligned with CLI-first philosophy

## Context

- v1.15.0 on `main` branch; vault repo at `D:\GitHub - Personal\algo-atlas-vault`
- Project is functional but not yet in regular daily use — goal is to reach a state where it's genuinely useful as a daily habit
- 4 identified workflow friction points that block daily adoption: (1) re-scraping known problems, (2) hard failures on test edge cases, (3) no way to update existing docs, (4) too many interactive prompts for a routine operation
- Codebase map available at `.planning/codebase/` for architecture reference
- CI via GitHub Actions; per-language PRs with semantic release conventions
- 481 tests across 19 test files; test pattern is rigid 6-class 24-test per language

## Constraints

- **CLI-first**: Must remain a terminal tool — no web UI or browser dependency
- **Claude required**: Documentation generation requires Claude CLI installed; not optional
- **Vault repo**: Output goes to a separate git repo, not the project repo
- **Backward compatible**: All new flags/args must be optional; existing interactive workflow must still work unchanged
- **Windows support**: All subprocess calls must handle Windows path/binary resolution (shutil.which for .cmd)
- **Per-language PRs**: New language additions follow the established 4-commit + 1 lint workflow

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Positional args for URL + file | Turn daily use into a one-liner; no prompts when you know what you're doing | — Pending |
| Cache scoped to problem slug | Cache key = slug; invalidate if problem data changes | — Pending |
| Partial save = save + warning, not skip | A doc with warning is more useful than no doc | — Pending |
| --update overwrites vault entry + re-opens PR | Consistent with existing add flow | — Pending |

---
*Last updated: 2026-03-14 after initialization*
