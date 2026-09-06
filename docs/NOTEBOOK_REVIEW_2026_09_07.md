# Notebook correction and methodology review

Reviewed 7 September 2026. This records code changes and evidence, not a replacement for the professors' research questions. Source records and human annotation files were not edited. The research Google Doc was read only.

## AutoModerator correction

Both canonical notebooks now explicitly recognize the known Reddit AutoModerator account, using exact account matching with case/whitespace and Reddit u/ prefix normalization. Human mentions of AutoModerator and unrelated usernames containing 'auto' or 'bot' are preserved.

- Topic_discovery_for_SMDI.ipynb: filter before new embeddings; when resuming, apply the same positional mask to saved records and embeddings, export removed records, recount topic sizes, and prevent later cells from reloading the unfiltered matrix.
- twitter_reddit_merge.ipynb: include known AutoModerator in the final removal mask and existing audit exports, including the first occurrence of each notice.
- Topic -1 remains unassigned and does not enter semantic clustering. Removed bot-only topics no longer enter topic summaries. Since group IDs can change, the old SMDI mapping is shown as a historical example and export requires a reviewed mapping.
- Old stored outputs were cleared from the topic notebook because their counts and charts precede this correction.

Eight regression checks cover exact account recognition, missing identity columns, preservation of human mentions, positional matrix alignment with nondefault dataframe indexes, idempotence, mismatched caches, first-copy removal, outlier exclusion and the mapping guard. On the available 87,574-row snapshot, the actual resume cell excludes 2,134 AutoModerator records and retains 85,440 correctly aligned embedding rows. Of the excluded records, 2,128 had ordinary topic IDs and 6 had topic -1. The retained outlier count is 41,881.

This is a tested filtering correction. BERTopic was not refitted locally: removing records from a saved model's assignments does not undo their earlier influence on the fitted model. Run the discovery section for a new model, then inspect the new semantic groups before filling REVIEWED_SMDI_MAPPING. The full Drive/Colab preprocessing pipeline was not executed locally.

## What the supplied files added

The supplied notebook `dubai_re_ONE_NOTEBOOK_v7_current_trimmed (1) (1).ipynb` is identical, as parsed JSON, to the pre-fix repository notebook `notebooks/twitter_reddit_merge.ipynb`. Their byte hashes differ because of serialization formatting. The canonical repository file is therefore the reviewed attachment with the correction applied; a second competing notebook copy is unnecessary.

The supplied brief is preserved as `notebooks/v7_supplied_audit_brief.md`. Its 80-cell counts refer to another/earlier version: the supplied current notebook has 59 cells and zero saved code outputs. Its instruction about the next active task is historical context, not an instruction overriding the current request.

The pipeline already has domain/listing filtering, contextual Reddit fields, low-information checks, an author-aware exact-duplicate step and a same-author near-duplicate step using a 0.98 threshold. It exports master_processed_analysis_clean.parquet/csv. The topic notebook instead loads master_processed.csv and appends Reddit exports. That is the concrete corpus mismatch; no assumption about an unseen notebook session is required. The AutoModerator fix does not silently switch the input corpus.

## Outlier method evaluated

The existing candidate method was frozen before this evaluation. Match on platform, username and exact clean_text, excluding ambiguous matches, yielded 178 records from the existing 400-record human annotation sample. Each annotator was evaluated separately because label-version independence and reconciliation are unresolved.

For this evaluation, substantive acceptance requires domain relevance=1, genuine discourse=1, listing/promotion=0 and low information=0. Domain relevance alone is a different target: an advertisement can be domain-relevant without being substantive discussion.

| Candidate policy | Reference | Precision | Recall | F1 |
|---|---|---:|---:|---:|
| Strict property-discussion bucket | Annotator 1 | 84.6% | 49.6% | 62.6% |
| Strict property-discussion bucket | Annotator 2 | 80.8% | 47.0% | 59.4% |
| Discussion plus contextual/short-message review buckets | Annotator 1 | 76.4% | 92.5% | 83.7% |
| Discussion plus contextual/short-message review buckets | Annotator 2 | 78.3% | 94.0% | 85.4% |

Precision asks how many selected records meet the reference definition. Recall asks how many reference-positive records were found. The strict method misses about half of the substantive relevant records in this matched sample. The expanded review set finds most but includes more unsuitable records.

These are retrospective results on previously filtered validation records, not population estimates for all 41,887 outliers. Some categories have no matched labels; the reference sample is relevance-heavy and its version history is unresolved. Do not use its high domain-only precision as evidence of global recovery quality.

A separate fresh sample of 66 outliers (10 per non-bot category and all 6 automated candidates) was inspected qualitatively by Codex with categories withheld during text review. This is machine-assisted error analysis, not another human annotator or independent gold standard. It exposed generic acknowledgements under relevant parent posts, short informative price headlines, property discussion padded with repeated sentences, advice mixed with lead generation, and implicit residential links missed by the keyword rules. The 12-word cutoff and parent-keyword inheritance are not reliable acceptance tests.

**Decision:** the current rules are suitable for routing review, not automatic final recovery. The user's rule remains: geopolitics requires a property link. A lack of detected keywords is not proof that a link is absent, so all excluded candidates remain preserved. Validate a context-aware classifier on human-labelled samples from every category before automatic acceptance/rejection. No new classifier performance is claimed here.

Reproducible code and aggregate results are under analysis/research_review_2026_09_06. Raw annotation records, posts, contact details and review samples remain local and are excluded from Git tracking.

## Deduplication: evidence and proposed policy

[Schofield, Thompson and Mimno (EMNLP 2017), Quantifying the Effects of Text Duplication on Semantic Models](https://aclanthology.org/D17-1290/) experimentally show how overrepresented repeated text can distort latent semantic patterns. Their models differ from BERTopic; the paper supports controlling redundancy, not any particular cosine cutoff in this project.

[Li and Li (Findings of EMNLP 2024), Generative Deduplication For Socia Media Data Selection](https://aclanthology.org/2024.findings-emnlp.330/) evaluates semantic deduplication for social-media NLP training. It supports investigating training redundancy, not indiscriminately removing every repeated expression from a discourse-frequency series.

[Kim et al. (JNCI Monographs 2013), Methodological Considerations in Analyzing Twitter Data](https://academic.oup.com/jncimono/article/2013/47/140/959212) discusses source/author-aware duplicate and spam handling and the interpretation of activity measures. There is no universal deduplication rule that simultaneously optimizes topic discovery and measures all communication activity.

Proposed policy for this study:

1. Remove duplicate ingestion of the same platform + record ID, recording the retained version.
2. Exclude known automated moderation notices from substantive discourse, including their first copies. This is implemented.
3. For topic discovery, report exact normalized text multiplicities and compare results with repeated templates collapsed/downweighted. Preserve the membership mapping to original records. Avoid changing numbers, negations or geographic entities during normalization.
4. For temporal attention, preserve distinct legitimate human actions and calculate sensitivity series with same-author repeats capped within the chosen time unit. A blanket keep-first rule across four months can erase later attention. Different-author repetition may represent diffusion rather than duplicate ingestion.
5. Keep near-duplicates as candidates until evaluated. The existing 0.98 threshold is an implementation heuristic; the reviewed papers do not validate it. Similar statements can differ in price, timing or polarity. Unknown/deleted authors must not be treated as a single person.

Items 3–5 are methodological recommendations, not silently applied changes to the current human-message cleaning policy. The attachment's current near-duplicate and author normalization behavior needs a separate reviewed change if this policy is adopted.

## NLP contributions beyond counts

Counts, engagement and author concentration are descriptive statistics. Their inputs may depend on NLP-derived themes, but they are not separate NLP tasks.

- Aspect extraction and aspect-based sentiment: identify what is being judged (rents, affordability, developer delivery, maintenance, regulation) and the polarity toward each aspect. A positive location judgment and negative rent judgment can coexist. [Pontiki et al., SemEval 2014 Task 4](https://aclanthology.org/S14-2004/) establishes the task, not a Dubai model.
- Target-specific stance: support/opposition toward a defined proposition such as buying Dubai property now. This differs from generic sentiment. [Mohammad et al., SemEval 2016 Task 6](https://aclanthology.org/S16-1003/) provides a tweet stance benchmark; buying/selling intentions would need separately defined labels and validation.
- Uncertainty/speculation extraction: identify expressed possibilities, expectations and their scope. [Farkas et al., CoNLL 2010 shared task](https://aclanthology.org/W10-3001/) addresses linguistic hedges; hedging is not automatically real-estate speculation or financial risk.
- Entity/relation extraction: connect a named community/developer with an aspect, event or price claim. Existing text can support this, but a place mention alone is not the author's residence or an observed transaction.

For a manageable four-month study, prioritize aspect-based sentiment plus a small, validated set of housing expectations/intent labels. Report frequency of the resulting labels separately; do not interpret embedding similarity as sentiment intensity or as a calibrated probability.

## Four months is the working constraint

The earlier multi-year ranges are not a requirement and are not feasible here. Retain January–April 2026. The [read-only research draft](https://docs.google.com/document/d/1vZPgrS1_iiIwDxr5hxLOJc81eMAcZRWZhrUOmNwmiHY/edit) asks primarily about correlation and variation by transaction type/platform, which can be investigated as an exploratory observational study within this window. Preserve the professors' RQs; flag that their draft mentions Facebook/listing platforms while the current social corpus contains X and Reddit.

Use matched full weeks as the primary descriptive comparison; retain 16 complete weeks when excluding partial boundary weeks. Choose a small number of justified outcome/theme comparisons in advance. Treat one- or two-week leads as exploratory, compare count levels and changes, report sensitivity to bot/dedup policies, and avoid causal or validated forecasting claims. Daily analysis is possible only after checking collection coverage and matching calendar boundaries; more daily bins do not create independent evidence or solve autocorrelation. Monthly plots can summarize four values but should not drive fitted forecasting models. No additional years of collection are required to finish the current exploratory study.

## Reconciliation explained from the beginning

Imagine one post says: “My landlord increased the rent; what can I do?” Aaron labels it relevant; Prajwal labels it irrelevant. That is one disagreement. First save both original answers and calculate kappa on the independently completed files. Next, discuss the definition and available context. If both agree on a final answer, write it in a new final_label column, with the reason. Keep Aaron's and Prajwal's original columns unchanged. If agreement is impossible, ask a designated third reviewer or mark the case unresolved.

The final label is useful when training/evaluating a classifier or creating a reference dataset. It is not necessary to force agreement merely to report inter-annotator reliability. Never recalculate initial kappa using labels edited to agree. For these files, 57 current disagreements versus the older 120-record report reflects changed annotator 1 labels; we need the version history to distinguish independent corrections from post-discussion changes.
