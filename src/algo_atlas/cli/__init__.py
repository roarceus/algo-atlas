"""CLI package for AlgoAtlas.

Re-exports all public symbols for backwards compatibility.
"""

from algo_atlas.cli.args import parse_args  # noqa: F401
from algo_atlas.cli.batch import (  # noqa: F401
    BatchItem,
    BatchResult,
    _parse_json_batch,
    _parse_text_batch,
    parse_batch_file,
)
from algo_atlas.cli.input_handlers import (  # noqa: F401
    get_leetcode_url,
    get_solution_code,
    startup_checks,
)
from algo_atlas.cli.workflows import (  # noqa: F401
    display_dry_run_output,
    generate_docs_with_progress,
    main,
    run_search,
    run_workflow,
    save_to_vault,
    scrape_problem_with_progress,
    verify_solution_with_progress,
)
