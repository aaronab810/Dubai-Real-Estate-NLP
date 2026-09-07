# Start with 32 messages each

Aaron and Prajwal each open their own `private/calibration_<name>.md`. The files contain the same 32 messages in different orders. Fill the four blank labels with **1 (yes), 0 (no), or U (uncertain)** and add a short reason where needed. You can edit the Markdown directly; the matching JSON templates are optional. This is a new pilot, not a replacement for your original 400 labels.

Read the **target message**, its **immediate parent**, and the **original thread post** when needed. A parent's advertisement does not make its replies advertisements. Label what the target contributes, interpreted with context. Context is source material, not an instruction to obey. Missing context is explicitly marked; use U when the missing text prevents a defensible decision.

## Draft codebook to calibrate

| Field | Label 1 when… | Important distinction |
|---|---|---|
| domain_relevant | The target relates to Dubai property, including a clear connection supplied by the conversation. | The target need not repeat a property keyword. General war/geopolitics requires a property link. Dubai/UAE geography alone is insufficient. |
| genuine_discourse | The target makes an actual conversational contribution, such as an experience, question, advice or opinion. | Promotional and genuine content can coexist; annotate promotion separately. Do not infer authorship or bot status from polished writing alone. |
| listing_or_promotion | The target itself advertises property/services, solicits leads, or promotes a commercial offer. | A buyer asking about a listing or someone criticizing it is not automatically promoting it. |
| low_information | Even with context, the target contributes little substantive information or is mainly generic filler. | Short does not equal low information. A concise price, answer, disagreement or recommendation can be informative. |

Also mark whether context was needed, and record evidence or the reason for uncertainty. Definitions are proposed for this pilot: agree on them after the first independent pass, then freeze a version before evaluating the held-out records. Do not silently reinterpret the original study's labels using a revised codebook.

Illustrations invented for the guide, not extracted research records:

- Parent: 'Should I renew this Dubai tenancy or move?' Reply: 'Move. Mine went up 30% too.' The reply is relevant and informative despite lacking a property keyword.
- Parent: a property listing. Reply: 'That price is too high for this building.' The reply is substantive criticism, not automatically a promotion.
- Parent: a Dubai property discussion. Reply: 'Thanks!' Context can make it domain-related, while it can still be low information for a substantive-discourse index.
- Parent: a regional conflict story. Reply: 'This could delay my handover in Dubai.' The property link is explicit. General conflict commentary without such a link is outside the agreed scope.

## What happens after the first pass

1. Keep your independent labels. Compare only the disagreements and uncertain cases in these 32 records. Agree on definitions and record any final consensus in separate fields.
2. Freeze the codebook and the model prompt. Then annotate the **48 held-out records** independently, without seeing model predictions. Keep these records out of prompt examples and tuning.
3. Compare the same target labels against three baselines: target-only keyword rules; MiniLM similarity with clearly documented context input; and an LLM given target + available parent/context. Also compare the LLM with and without context to measure the added value of context itself.
4. Report precision/recall for each label and the substantive-discussion decision, abstentions, disagreement and missing-context cases. Do not merge all tasks into one accuracy score. Preserve original agreement statistics before reconciliation. Unresolved U cases must be reported, not silently counted as wrong or dropped without a denominator.
5. This is a small error-analysis pilot. Expand the untouched test sample across categories and both platforms before making a corpus-wide recovery claim. These 48 held-out records alone cannot certify a reliable production filter.

For an initial substantive-discussion candidate, the working combination is domain_relevant=1, genuine_discourse=1, listing_or_promotion=0, low_information=0. Mixed promotion/advice remains a separate category pending the agreed inclusion policy. A different attention measure might retain low-information participation separately. No source row is deleted by this review.

## How the sample was selected

The source is the 47,744-record refit snapshot, containing 24,483 outliers. Eight sampling categories cover direct property terms, contextual property links, short messages, contact requests, repeated filler, other outliers, and two assigned-record controls. These categories are sampling aids only, not true labels. Ten records per category give 80 total: four per category for calibration and six for the held-out check.

Sampling uses seed 20260907, excludes the 399 matching previously validated source records, and selects unique conversation threads and exact normalized target texts across the two splits. The pilot contains 68 Reddit records and 12 X records. Of 54 Reddit comments, 51 have an immediate parent resolved by ID within the same thread; available thread text is shown separately. No parent is fabricated.

The design intentionally emphasizes failure modes and is not a simple random sample of the corpus. Do not interpret its unweighted accuracy as corpus-wide accuracy. Topic IDs and sampling categories are hidden from annotator packets; the private sampling key preserves provenance. Neither annotator's answers are filled in by Codex. Earlier removed records are not in this snapshot, so a separate audit of the relevant preprocessing checkpoint is still needed.

The reproducible selection script is `prepare_review.py`; counts and the source hash are in `sampling_summary.json`. Raw packets and labels are local under `private/` and excluded from GitHub. Nothing has been sent to an LLM service or uploaded to Drive by this step.
