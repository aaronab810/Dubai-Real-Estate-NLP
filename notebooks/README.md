# notebooks
This folder contains all Jupyter/Google Colab notebooks used in this research.

# reddit_data 
contains the scraping and gathering of real estate data from reddit subreddits: 
- r/dubairealestate
- r/dubai

# `twitter_reddit_merge.ipynb`

Twitter/X has been scraped using twscrape. 

This notebook is a Twitter/X + Reddit preprocessing pipeline. It loads saved raw Twitter/X files, applies/uses MiniLM filtering, loads Reddit exports, standardises the schema, merges platforms, filters domain/listing noise, performs low-information and duplicate/repost cleanup, creates validation samples, and produces paper-ready tables.

# `Topic_discovery_for_SMDI.ipynb`

This notebook is the creation of the SMDI using topic discovery on the combined dataset from 'twitter_reddit_merge.ipynb' using bertopic and undergoing clustering alternatives. 

#  `DLD_Market_Indicators.ipynb`

## Reviewed v7 attachment and AutoModerator correction

The supplied `dubai_re_ONE_NOTEBOOK_v7_current_trimmed (1) (1).ipynb` matched
`twitter_reddit_merge.ipynb` as parsed JSON before the September 2026 correction.
The latter remains the canonical copy. The accompanying supplied brief is saved
as [v7_supplied_audit_brief.md](v7_supplied_audit_brief.md); its 80-cell counts
refer to an earlier version, whereas the current notebook contains 59 cells.

Both preprocessing and topic discovery now explicitly exclude Reddit
AutoModerator. The topic notebook also filters saved embeddings in matching row
order and keeps topic -1 outside semantic groups. Refit BERTopic to remove its
earlier training contamination, then inspect groups before entering the reviewed
SMDI mapping. See [the review and evaluation](../docs/NOTEBOOK_REVIEW_2026_09_07.md).

## Executed clean-corpus refit, 7 September 2026

Topic discovery now defaults to `master_processed_analysis_clean.parquet` (CSV
fallback), matching the validation corpus. It does not append raw Reddit data
unless the historical comparison flag is enabled. Model outputs and the resume
path use `SMDI creation/clean_refit_2026_09_07`, preserving older runs. Resume also
accepts the parquet assignments in the locally executed refit package.

The executed refit removed four AutoModerator records from 47,748 final-clean
records. BERTopic assigned 23,261 records to 274 topics and left 24,483 as
outliers. These outputs still need topic/content validation; no new SMDI mapping
has been assigned. See [the reproducible run](../analysis/refit_2026_09_07/README.md)
and [the methodology evidence review](../docs/METHODOLOGY_EVIDENCE_2026_09_07.md).

