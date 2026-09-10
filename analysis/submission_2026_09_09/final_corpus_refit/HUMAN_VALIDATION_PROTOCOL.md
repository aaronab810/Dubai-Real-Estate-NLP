> **Historical document:** This describes an earlier workflow. Use [DOMAIN_REPRODUCTION.md](DOMAIN_REPRODUCTION.md) for the current 43-category/ten-group release. Older five-category validation packets do not validate the current mapping.

# Independent SMDI validation: pending human work

No human category results exist in this version. The existing 400 paired records
assess four dataset-quality criteria and must not be used as SMDI gold labels.

`prepare_validation.py` creates separate reviewer files with target and available
context, independently shuffled row orders, and blank judgment fields. Category
predictions, topic IDs, strata and inclusion probabilities remain in a separate
private key. Sampling covers platform, UTC month, assignment status and category
pattern, including noise and unclassified records so missed categories can be
observed. Within each disjoint stratum, take a simple random sample of up to six
records without replacement. The manifest records the resulting sample size;
it is a coverage-oriented design, not a claim of a precomputed precision target.

Exclude exact-text families represented in current and previous development
packets, inspected candidate examples and historical quality annotations.
Performance estimates consequently apply to the documented remaining frame,
not automatically to excluded development families. Rare positives may still
be too scarce for useful recall or platform-period estimates. Report undefined
or imprecise results honestly, rather than replacing them with a favorable zero.

Two reviewers independently apply all five binary categories, the separate
relevance field, and an uncertainty flag. Negative answers denote a judged
absence; blanks denote incomplete work. Uncertain cases require documented
adjudication or separate reporting. Do not interpret overlapping categories as
disagreement. Keep reviewer identities, dates and codebook version in the
annotation provenance. A separate adjudicator records final judgments with
identity/date fields; no algorithm creates consensus.

`evaluate_human_validation.py` rejects incomplete reviewer labels. It reports
sample agreement and Cohen's kappa, and design-weighted category performance
only when actual adjudicated labels are supplied. Sample agreement is descriptive
of the stratified packet; it is not automatically population-weighted reliability.
Use the inverse inclusion probabilities for frame-level confusion counts and
precision/recall. Report uncertain-case exclusions, positive supports, both
platforms, all months, candidate coverage and noise/unclassified performance.
Stratified bootstrap uncertainty may be added once real labels and their supports
are available; the current paper contains no invented validation intervals.

Freeze codebook and assignment hashes before opening labels. If inspection of
errors changes the rules, the existing sample becomes development evidence and
a fresh independent set is required. Packet preparation refuses to overwrite
any existing completed human judgment. Independent validation is the expected
remaining scientific step; it does not block the candidate analysis supplied now.
