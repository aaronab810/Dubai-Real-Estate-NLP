# Notebook inventory

The companion ZIP includes the current entry point. Historical notebook links below refer to files in the full repository, not to additional notebooks bundled in that ZIP.

The current execution entry point is [Current_Study_Reproduction.ipynb](Current_Study_Reproduction.ipynb). It calls the same scripts as the command-line workflow. Historical notebooks retain their original code and saved outputs; their banners identify scope, not a claim of fresh execution.

| Notebook | Status | Purpose |
|---|---|---|
| [dfm_transaction.ipynb](../dfm_transaction.ipynb) | Historical predecessor | Earlier transaction/sentiment experiments; not the current study. |
| [twitter_reddit_merge.ipynb](twitter_reddit_merge.ipynb) | Historical source preparation | Earlier cleaning pipeline; the final frozen corpus includes later reconciliation and repairs in Python scripts. |
| [Topic_discovery_for_SMDI.ipynb](Topic_discovery_for_SMDI.ipynb) | Historical September 7 topic run | Targets the older clean_refit_2026_09_07 corpus. It does not generate the current 367-topic mapping. |
| [DLD_Market_Indicators.ipynb](DLD_Market_Indicators.ipynb) | Superseded market analysis | Older five-SMDI frequency analysis and mixed transaction aggregates. Use the current sales-only script workflow. |
| [01_Reddit_Scraping.ipynb](reddit_data/01_Reddit_Scraping.ipynb) | Historical acquisition | Source collection; rerunning changes the source snapshot and requires platform access. |
| [02_Real_Estate_Method_Comparison.ipynb](reddit_data/02_Real_Estate_Method_Comparison.ipynb) | Historical filter development | Classifier comparison and development, not the current empirical analysis. |
| [03_dubai_deberta_threshold.ipynb](reddit_data/03_dubai_deberta_threshold.ipynb) | Historical filter development | Threshold development; cached scores are retained inputs to the current study. |
| [full_noise_clustering.ipynb](../analysis/submission_2026_09_09/final_corpus_refit/noise_analysis/colab/full_noise_clustering.ipynb) | Separate residual experiment | All-noise AHC experiment; not incorporated in the Pass-1-only paper. |

Restricted copies inside `private/` are excluded from this inventory and from Git. Historical notebook code has not been silently replaced with newer results. The 635-node, 1,186-edge Graphify graph documents these older relationships; current status is recorded here.
