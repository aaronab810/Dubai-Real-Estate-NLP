# Analysis directory guide

The current paper uses [submission_2026_09_09/final_corpus_refit](submission_2026_09_09/final_corpus_refit/README.md). Start with its [reproduction instructions](submission_2026_09_09/final_corpus_refit/DOMAIN_REPRODUCTION.md), or the [current notebook](../notebooks/Current_Study_Reproduction.ipynb).

## Current workflow

| File or folder inside `submission_2026_09_09/final_corpus_refit/` | Purpose |
|---|---|
| `run_pipeline.py` | Verify saved aggregates, check frozen inputs, or rebuild the current analysis |
| `build_domain_graphs.py` | Construct platform-specific weekly group shares and DLD series |
| `domain_paper_analysis.py` | Calculate comparisons and sensitivity checks; generate tables and codebook |
| `make_domain_comparisons.py` | Generate the paired social-discourse/market plots |
| `results/domain_graphs/comparisons/` | Current plots and explanations |
| `user_domains_10.json`, `supplied_smdi_workbook.json` | The two supplied topic mappings |
| `frozen_input_hashes.json`, `release_manifest.json` | Input and release file checksums |

## Earlier work

Other dated directories preserve acquisition reviews, cleaning development, earlier topic fits and paper revisions. Their dates identify development snapshots, not newer alternatives to the current pipeline. The parent `submission_2026_09_09/` also contains source manifests used by the current study alongside older scripts.

The separate `noise_analysis/` experiments are not incorporated in the current Pass-1-only paper. Older five-category instructions are preserved in [HISTORICAL_WORKFLOW.md](submission_2026_09_09/final_corpus_refit/HISTORICAL_WORKFLOW.md).

Use the current entry point instead of running every dated notebook or script in sequence. Source locations are retained to preserve provenance and existing file references.
