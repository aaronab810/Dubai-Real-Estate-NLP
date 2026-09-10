# Current final-corpus study

Use [DOMAIN_REPRODUCTION.md](DOMAIN_REPRODUCTION.md) for the current 367-topic, 43-category, ten-group analysis, or open [the current notebook](../../../notebooks/Current_Study_Reproduction.ipynb).

```sh
python analysis/submission_2026_09_09/final_corpus_refit/run_pipeline.py --verify
```

Run the command from the repository root. It verifies aggregates without private data. Use `--check-inputs` before a restricted-input rebuild, then run without flags to rebuild the current analysis. These commands do not refit the model or produce semantic validation.

The earlier five-category instructions are preserved in [HISTORICAL_WORKFLOW.md](HISTORICAL_WORKFLOW.md). Do not run the old semantic assignment, manuscript-writing or validation-packet scripts on the current release. Their category definitions and outputs are superseded.
