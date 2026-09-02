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

