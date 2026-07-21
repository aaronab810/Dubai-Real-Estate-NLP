# Notebook audit brief

File reviewed: `twitter_reddit_merge.ipynb`

## What I cleaned
- Removed all stored cell outputs from the notebook.
- Reset execution counts.
- Removed Colab output metadata / widget state.
- Removed 1 empty code cell.
- Added a short briefing cell at the top.

## Size reduction
- Original: 1.73 MB
- Cleaned: 0.41 MB

## Notebook structure
- Original cells: 80
- Cleaned cells: 80
- Original code cells: 60
- Original markdown cells: 20
- Code cells with old outputs removed: 50

## What the notebook is for
This is a no-rescrape Twitter/X + Reddit preprocessing pipeline. It loads saved raw Twitter/X files, applies/uses MiniLM filtering, loads Reddit exports, standardises the schema, merges platforms, filters domain/listing noise, performs low-information and duplicate/repost cleanup, creates validation samples, and produces paper-ready tables.

## Where you are now
The cleaning pipeline has already reached the final analysis-ready dataset stage:
- `master_processed_analysis_clean.parquet`
- `master_processed_analysis_clean.csv`

Your current active task is annotation/validation. After annotation, run agreement metrics and then build the SMDI layer.
