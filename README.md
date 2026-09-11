# Dubai Real Estate NLP

### Online property discussion and Dubai property sales

How does online discussion of Dubai real estate relate to activity in the property market? This project combines posts from **X**, conversations from **Reddit**, and **Dubai Land Department (DLD)** sales registrations to study that question.

The work has two connected contributions: a documented research dataset with traceable cleaning and reconciliation decisions, and an exploratory analysis of how property-related discussion varies alongside registered sales. X and Reddit are analysed separately because they capture different patterns of participation and discussion.

[Read the paper](paper/main.pdf) · [Explore the graphs](analysis/submission_2026_09_09/final_corpus_refit/results/domain_graphs/comparisons/domain_market_comparisons.pdf) · [Reproduce the analysis](analysis/submission_2026_09_09/final_corpus_refit/DOMAIN_REPRODUCTION.md)

## Dataset

| Source | Retained records | Coverage |
|---|---:|---|
| X | 11,787 | Posts |
| Reddit | 59,452 | 4,450 submissions and 55,002 comments |
| DLD | 62,012 | Unique property sales registrations |

The social corpus contains **71,239 activity records**, corresponding to **68,285 unique training texts**. Social records are selected using January–April 2026 UTC dates; DLD registrations use Dubai dates. The aligned analysis covers **16 complete Monday–Sunday weeks, from 5 January to 26 April 2026**.

The dataset preparation retains source provenance and available conversational context, reconciles record counts, and documents exclusions and duplicate handling. An existing two-reviewer assessment of 400 records provides evidence about dataset quality.

## Method

```text
X posts and Reddit conversations
              ↓
Corpus reconciliation and cleaning
              ↓
BERTopic discovery: 367 non-noise topics
              ↓
LLM-assisted semantic topic labelling
              ↓
43 finer discourse categories and 10 broad thematic groups
              ↓
Weekly discussion shares, calculated separately for X and Reddit
              ↕
Weekly DLD sales counts, off-plan/ready activity and sale amounts
```

Candidate **Semantic Market Discourse Indicators (SMDIs)** describe the prevalence of identified themes. Records inherit the category assignments of their topic. The ten broad groups include pricing, investment, development, tenancy, professional services, regulation and political/social discussion.

Broad groups may overlap. Records assigned to BERTopic's noise label (`-1`) remain unassigned and are included in the main platform denominator. Category assignments cover **48.6% of retained social activity**. Independent human validation of the SMDI categories is pending; the earlier dataset-quality review does not establish category validity.

## What the analysis shows

Reddit developer discussion moves more closely with ready-property sales than with off-plan sales in this observation window. Political/social discussion on Reddit is higher in some weeks with fewer sales. X shows different patterns.

Several relationships weaken when the analysis uses weekly changes, narrower category definitions, or reduces the influence of busy Reddit threads. This sensitivity is part of the result: the meaning of a category and the way discussion is counted affect the observed relationship.

The study examines associations over a short period. It does not establish causal effects, forecasting ability, or representative investor sentiment. Registered sale amounts also depend on the mix of properties sold and are not a constant-quality price index.

The [graph explanations](analysis/submission_2026_09_09/final_corpus_refit/results/domain_graphs/comparisons/GRAPH_EXPLANATIONS.md) describe each comparison and distinguish primary analyses from contextual plots without a directly corresponding DLD outcome.

## Reproduce the analysis

From the repository root, install the recorded analysis dependencies and verify the saved aggregate results:

```sh
python -m pip install -r analysis/submission_2026_09_09/final_corpus_refit/requirements-domain.txt
python analysis/submission_2026_09_09/final_corpus_refit/run_pipeline.py --verify
```

Alternatively, open [Current_Study_Reproduction.ipynb](notebooks/Current_Study_Reproduction.ipynb). Both entry points use the same analysis scripts.

Aggregate verification requires no raw posts. Rebuilding the weekly series requires the restricted frozen inputs and checks their hashes before execution. The [reproduction guide](analysis/submission_2026_09_09/final_corpus_refit/DOMAIN_REPRODUCTION.md) documents the inputs, software versions, commands, definitions and output provenance.

## Repository guide

| Location | Contents |
|---|---|
| [paper/](paper/) | Manuscript, bibliography and semantic codebook |
| [notebooks/](notebooks/README.md) | Current reproduction notebook and labelled historical notebooks |
| [Current analysis](analysis/submission_2026_09_09/final_corpus_refit/README.md) | Analysis scripts, category mappings, manifests and results |
| [Analysis guide](analysis/README.md) | Current workflow and earlier development snapshots |
| [docs/](docs/README.md) | Earlier methodological notes and research reviews |
| `tests/` | Existing code and notebook regression checks |

Earlier notebooks and dated analyses are retained for provenance. They are labelled separately from the current workflow; running all notebooks in sequence is not the reproduction procedure.

## Data access

Shared research materials contain aggregate data, category definitions, analysis code and provenance records. Raw social posts, identities, record-level annotations, embeddings and fitted model binaries are excluded from the research companion. Full reconstruction requires authorised access to restricted source snapshots and cached inputs.

Source data remain subject to their original access and redistribution conditions. Repository access does not grant permission to redistribute platform records. See [access and sharing](analysis/submission_2026_09_09/final_corpus_refit/DOMAIN_REPRODUCTION.md#access-and-sharing) for the scope of the research artifact.
