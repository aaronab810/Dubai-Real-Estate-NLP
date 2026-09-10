# Superseded five-category workflow

Do not use these commands for the current paper. Preserved as development history.

# Active final-corpus study

This folder supersedes the parent folder's topic, semantic and association
outputs for the revised manuscript. Parent source/eligibility and DLD artifacts
remain provenance inputs. The interrupted `v2_development_snapshot` and `v3_development_snapshot` record the
inspection that exposed residual explicit offers; they are not completed final runs.

The final social population is 71,239 distinct activity IDs, comprising 11,787 X
posts, 4,450 Reddit submissions and 55,002 comments. It contains 68,285 unique
case-folded normalized-text families. The common 16 weeks contain 68,083 social
records (X 11,362; Reddit 56,721) and 59,229 DLD sale registrations. All semantic
results refer to candidate assignments pending independent category validation.

## Run and inspect

Use the existing project Python environment, with versions in the parent
`requirements-lock.txt`. Execute from the repository root. Do not run duplicate
fits concurrently. The original source snapshots and upstream scored files are
required for full reconstruction; none are silently downloaded or substituted.

The original source reconstruction remains in the parent directory:
`build_corpus.py`, `build_dld.py`, `validate_upstream.py`, `verify_inputs.py`,
`near_duplicates.py`, the historical discovery fit and `freeze_analysis_corpus.py`.
Those versioned outputs produced the v2 eligibility input. Reusing that frozen
input avoids needing to rerun historical exploratory discovery to reproduce the
current final study. Its SHA-256 is checked in the active lineage manifest.

The active execution sequence is:

```
python analysis/submission_2026_09_09/final_corpus_refit/freeze_final_corpus.py
python analysis/submission_2026_09_09/final_corpus_refit/fit_topics.py
python analysis/submission_2026_09_09/final_corpus_refit/assign_semantics.py
python analysis/submission_2026_09_09/final_corpus_refit/analyse_associations.py
python analysis/submission_2026_09_09/final_corpus_refit/spatial_feasibility.py
python analysis/submission_2026_09_09/final_corpus_refit/final_diagnostics.py
python analysis/submission_2026_09_09/final_corpus_refit/strengthen_diagnostics.py
python analysis/submission_2026_09_09/final_corpus_refit/check_analysis.py
python analysis/submission_2026_09_09/final_corpus_refit/prepare_validation.py
python analysis/submission_2026_09_09/final_corpus_refit/make_paper_assets.py
python analysis/submission_2026_09_09/final_corpus_refit/write_paper_numbers.py
python analysis/submission_2026_09_09/final_corpus_refit/write_empirical_narrative.py
python analysis/submission_2026_09_09/final_corpus_refit/threshold_040_check.py
```

`run_pipeline.py` runs through `make_paper_assets.py`; run the final three
commands separately. The 0.40 threshold comparison is an organizational
diagnostic and does not change category assignments. Compile `paper/main.tex`
before running `verify_paper.py`. Then run `verify_aggregate_results.py` and
`finalize_provenance.py`. Packaging uses `package_deliverables.py` after the
numerical and visual checks have been recorded in `FINAL_QA.json`.

Before fitting, restore the unchanged near-family, annotation mapping and DLD
registration inputs from the parent `private/`, and the DLD/quality aggregate
inputs from its `results/`. `run_pipeline.py` provides this preparation and the
ordered commands. It verifies the frozen v2 input and preserves human-completed
packets. The embedding model uses the pinned local Hugging Face snapshot. Vector
cache reuse is linked to exact training text/order; a fresh environment may need
the original model snapshot and embeddings or must recompute with that revision.

The standalone `verify_aggregate_results.py` works from an extracted research
companion with NumPy, pandas and SciPy. It recalculates the complete 72-coefficient
grid, common-window totals and lag sample sizes without private data. These are
arithmetic reproduction checks, not independent semantic validation.

## Output interpretation

- `analysis_corpus_manifest.json`: actual final eligibility repair and hashes.
- `topic_manifest.json`, `results/topic_specifications.csv`: six complete fits.
- `results/hierarchical_comparison.csv`: structural group diagnostics only.
- `results/topic_category_primary.csv`: fine-topic cue evidence, not reviewer votes.
- `semantic_manifest.json`, `results/semantic_coverage.csv`: operational labels.
- `results/associations_all.csv`: 24 contemporaneous primary coefficients plus
  48 secondary one/two-week coefficients, without result-based selection.
- `results/associations_sensitivity.csv`: all bounded sensitivity variants.
- `results/association_contrasts.csv`: shared-week platform and segment contrasts.
- `results/matched_topic_stability.csv`: stability with/without joint noise.
- `results/weekly_semantic_stability.csv`: weekly category-measure stability.
- `results/final_source_flow.csv`: final source-to-inclusion/exclusion arithmetic.
- `results/monthly_semantic_coverage.csv`: platform/month numerators and coverage.
- `validation_packet_manifest.json`: blank independent packet design and freeze.
- `lineage_manifest.json`: inherited/current source, code and output provenance.
- `embedding_reuse_checks.json`: exact-text/order checks on the final vector cache.

## Access and rights

The historical research companion contains
aggregate results, code and documentation. Neither includes private social text,
usernames, individual review judgments, source URLs or model binaries. Full
end-to-end reproduction requires the identified restricted snapshots and stored
upstream scores, including an upstream DeBERTa revision that was not recorded.
No public release, redistribution license or access approval is asserted.

Graphify's existing 635-node/1,186-edge graph records earlier project provenance.
It does not certify these new outputs or the semantic method. Independent SMDI
validation remains the main external scientific step. The authors will handle
their final submission review and conference-specific declarations.
