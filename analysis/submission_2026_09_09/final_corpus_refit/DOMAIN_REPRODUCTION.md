# Current paper: Pass-1 topics, 43 finer categories, ten broad groups

The current source is `paper/main.tex`. It replaces the earlier five-category keyword/gate analysis. The default `run_pipeline.py` now runs the current broad-group workflow. Old files and scripts remain development history; use `--legacy-five-category` only to reproduce that superseded analysis. Do not use the older semantic validation packets for the new categories.

## What was done

The final corpus and Pass-1 BERTopic model were not changed. GPT 5.6 Sol provided semantic topic labels, according to the authors' account. The workbook preserves the labels and mapping; the complete original prompting session is not archived and cannot be regenerated exactly. The supplied workbook actually contains 43 categories, numbered SMDI-01 through SMDI-43. The authors supplied the ten broad-group mapping and corrected seven earlier omissions. All topics 0–366 are covered. Topic -1 stays unassigned. The finer mapping is single-label; broad groups overlap and do not form a strict whole-category hierarchy.

The codebook preserves the supplied finer definitions. The record assignment rule is topic inheritance, with no new keyword gate or per-document classifier. All such assignments remain candidates pending independent validation. The earlier 400 paired annotations concern data quality only. No human SMDI results have been created.

## Reproduce the published aggregate coefficients

The current notebook entry point is `notebooks/Current_Study_Reproduction.ipynb`. Its default executes aggregate verification and previews the saved outputs. It calls the scripts below, rather than maintaining another implementation. Older notebooks are labelled and listed in `notebooks/README.md`.

From the repository root (or the same relative layout in the research companion):

```text
python analysis/submission_2026_09_09/final_corpus_refit/verify_domain_aggregates.py
```

This needs numpy, pandas and scipy. It verifies the supplied weekly counts, denominators, 96 planned specification/lag rows and the additional saved weighted/filtered series. It needs no raw social text. It cannot establish whether text was correctly classified.

An equivalent entry point is `python analysis/submission_2026_09_09/final_corpus_refit/run_pipeline.py --verify`. Install the recorded analysis dependencies using `python -m pip install -r analysis/submission_2026_09_09/final_corpus_refit/requirements-domain.txt` in your chosen environment. Jupyter/Colab supplies the notebook interface; the verification script itself does not require Jupyter.

## Rebuild from restricted frozen inputs

```text
python analysis/submission_2026_09_09/final_corpus_refit/run_pipeline.py
```

Before a rebuild, the runner checks all seven required input files against the portable `frozen_input_hashes.json`. Use `--check-inputs` to run that check alone. Missing or changed inputs stop execution before outputs are written. A newly approved mapping requires an explicit provenance update and recomputation, not bypassing this check.

Steps: `build_domain_graphs.py` constructs weekly series and basic sensitivities; `domain_paper_analysis.py` adds weighting, calendar, narrower-category, composition and bootstrap checks and writes tables/codebook; `make_domain_comparisons.py` writes the paired figures. The first script retains earlier six-panel diagnostic pages, but the paired comparisons under `results/domain_graphs/comparisons` and the paper figure are the current reader-facing figures.

Required inputs include `private/social_with_topics.parquet`, `private/training_with_topics.parquet`, `private/near_families.parquet`, the quality flags in `private/social_semantic.parquet`, and the parent directory's `private/dld_sales_registrations.parquet`. The legacy semantic file supplies only unchanged quality flags; its old five-category assignments are not used. Topic model/embedding provenance is in `topic_manifest.json` and `embedding_reuse_checks.json`. All input hashes and package versions for the current analysis are in `results/domain_graphs/paper_analysis_manifest.json` and `release_manifest.json`.

Model fitting is not repeated by this command. The mapping is tied to frozen topic IDs; a new topic model would require a separately reviewed mapping. Historical acquisition, human quality annotations and upstream classifier scores are retained inputs. The classifier revision and interactive LLM session cannot be exactly regenerated. The frozen workbook and score snapshots identify what was actually analysed.

## Measurement and output definitions

- `topic_to_fine_category.csv`: 367 topics, one of 43 finer categories per topic.
- `topic_to_domain.csv`: overlapping topic memberships in the ten author-supplied groups. Count each record once per group.
- `fine_category_codebook.csv`: supplied names, descriptions and topic lists. Its `Posts` column means unique training texts, not activity records.
- `domain_weekly.csv`: 320 rows, ten groups × two platforms × 16 weeks. `count` is group activity, `eligible_records` includes topic -1, and `topic_assigned_records` excludes it. `share_all` and `share_assigned` are fractions, not percentages. `share_unique` counts each text once within platform/week.
- `dld_weekly.csv`: unique sales registrations, not all transaction types. Amounts are nominal AED. Median and mean amounts are not constant-quality price indices.
- `primary_contemporaneous.csv`: eight same-week comparisons, four conceptual pairs on each platform.
- `primary_associations_and_sensitivities.csv`: four social specifications × three forward lags × eight pairs. A lag k matches social week t with DLD week t+k. Samples are 16/15/14 weeks; first differences have one fewer observation.
- `additional_weekly_series.csv` and `additional_sensitivities.csv`: thread/author/near-family weights, quality exclusions, UTC weeks, narrower workbook categories, detrending, two-week periods and amount-composition checks. A constant series gives an undefined correlation, not zero.
- `bootstrap_intervals.csv`: 4,999 paired stationary-bootstrap repetitions at mean block lengths 2/3/4. Spearman ranks are recalculated within each repetition. These intervals assume the chosen resampling scheme and omit category errors.
- `platform_contrasts.csv`: X minus Reddit correlations with shared-week resampling.
- `reddit_thread_concentration.csv`: largest thread's contribution to each group's weekly activity.
- `comparisons/pairing_rationale.csv`: identifies primary comparisons, exploratory transaction/service comparisons and contextual pairings lacking a direct administrative outcome.

## Paper outputs

Table 1 uses the corpus and DLD manifests; Table 2 uses historical annotation reliability. Table 3 uses `domain_coverage_all_corpus.csv`. Table 4 uses the same-week table and block-3 bootstrap intervals. Figure 1 uses `domain_weekly.csv` and `dld_weekly.csv`, subtracting each series' mean and dividing by its sample standard deviation. The full 11 paired figures cover ten groups, with two segment comparisons for the developer group.

The manuscript source is `paper/main.tex`, with its bibliography in `paper/references.bib`. The Springer class and bibliography style are included. Build with pdfLaTeX or XeLaTeX and BibTeX; the recorded local build used Tectonic.

## Access and sharing

The companion contains aggregates, topic-level definitions, scripts and provenance. It excludes raw posts, usernames, record-level review packets, model binaries and embeddings. These sources are not automatically licensed for redistribution. Aggregate reproduction is available from the package; full reconstruction requires authorised access to restricted inputs. No public release, repository push or conference submission has been made.

The historical Graphify graph has 635 nodes and 1,186 edges. It supports project provenance only; it does not validate categories or statistical findings.
