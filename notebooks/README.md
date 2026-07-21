# notebooks
This folder contains all Jupyter/Google Colab notebooks used in this research.

# reddit_data 
contains the scraping and gathering of real estate data from reddit subreddits: 
- r/dubairealestate
- r/dubai

# File reviewed: `twitter_reddit_merge.ipynb`

Twitter/X has been scraped using twscrape. 

This notebook is a Twitter/X + Reddit preprocessing pipeline. It loads saved raw Twitter/X files, applies/uses MiniLM filtering, loads Reddit exports, standardises the schema, merges platforms, filters domain/listing noise, performs low-information and duplicate/repost cleanup, creates validation samples, and produces paper-ready tables.
