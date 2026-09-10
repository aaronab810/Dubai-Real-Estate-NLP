> **Historical document:** This describes an earlier workflow. Use [DOMAIN_REPRODUCTION.md](DOMAIN_REPRODUCTION.md) for the current 43-category/ten-group release. Older five-category validation packets do not validate the current mapping.

# Manuscript and research-artifact dependencies

| Output | Executed source | Interpretation |
|---|---|---|
| Dataset population table | analysis_corpus_manifest.json; results/final_source_flow.csv; inherited corpus_manifest.json and dld_manifest.json | Initial, repaired, final and common-window populations |
| Historical quality table | inherited results/annotation_reliability.csv | 400 paired quality labels, not SMDI categories |
| Retained quality counts | results/final_historical_validation.csv | Actual membership in the final eligibility set |
| Candidate coverage table | results/semantic_coverage.csv | Per-platform overlapping category counts and eligible denominators |
| Primary correlation table | results/associations_all.csv, lag=0 | Six pairs x two platforms; Pearson, Spearman and conditional block-3 intervals |
| Weekly figure | results/smdi_weekly.csv and dld_weekly.csv, 16 complete weeks | Candidate shares and off-plan/ready sales counts |
| Reduction figure | topic_specifications.csv and hierarchical_comparison.csv | Organizational diagnostics, not economic categories |
| Topic-fit/reduction supplementary tables | topic_specifications.csv and hierarchical_comparison.csv | All six fits, fixed groups and distance cuts |
| Lag supplementary table | associations_all.csv, lag=0/1/2 | All coefficients; n=16/15/14 |
| Robustness supplementary table | associations_sensitivity.csv | Selected compact contrasts; complete CSV retained |
| Spatial feasibility | spatial_manifest.json; geographic_coverage.csv; spatial_feasibility.csv | Literal mentions only; no geolocation inference |
| Dynamic manuscript numbers | write_paper_numbers.py -> paper/results_numbers.tex | Generated macros with source hashes |
| Result paragraphs | paper/empirical_narrative.tex; sensitivity_narrative.tex | Interpretations verified against full result tables |

## Restricted-data execution

run_pipeline.py restores unchanged near-family, DLD and annotation inputs from the
parent execution. With --fit it freezes the final population and fits six models;
without it, it runs semantic assignment, associations, spatial feasibility,
quality/stability checks, blank independent-review preparation and paper assets.
write_paper_numbers.py follows these steps. The final LaTeX assembly also uses the
reviewed narrative files and the original official Springer template.

Fit input is the final frozen corpus. Cached 384-dimensional vectors are mapped
from the inherited training_key and checked against exact target text and order;
embedding_reuse_checks.json records the verified source and resulting hashes.
The pinned encoder revision and package versions are in topic_manifest.json.
Full reconstruction needs the identified restricted snapshots, not merely the
aggregate companion. Original upstream DeBERTa revision provenance is incomplete;
stored scored snapshots preserve the historical selection actually used.

## Independent validation

prepare_validation.py creates private shuffled, prediction-blinded reviewer
packets, a separate prediction/design key and blank topic-review fields. The
codebook and assignment hashes are frozen in validation_packet_manifest.json.
No row-level review materials or private text are packaged. The evaluation script
requires real reviewer and adjudicator judgments; current outputs contain none.

## Archive checks

The manuscript ZIP includes main.tex, bibliography, every referenced table/figure,
three generated/narrative inputs and the original svmult.cls/spmpsci.bst. It is
compiled after extraction. The aggregate companion preserves scripts' original
repository-relative paths, documentation, aggregate CSVs and supplementary tables.
Its standalone verify_aggregate_results.py recomputes all 72 coefficients directly.
SHA256SUMS.json covers every archive payload. No private-directory recursion is used.

The existing Graphify graph (635 nodes, 1,186 edges) links historical rationale and
source documents. It is neither current execution lineage nor methodological validation.
