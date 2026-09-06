"""Retrospective evaluation against existing human labels; no invented gold labels.

The validation sample comes from a previously filtered corpus, not a random
sample of all outliers. Results describe matched records only, not population
precision/recall. Labels are evaluated separately for each annotator.
"""
from pathlib import Path
import json
import hashlib
import pandas as pd

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'evaluation'
OUT.mkdir(exist_ok=True)
o = pd.read_csv(ROOT / 'followup/all_outliers_with_triage.csv', low_memory=False)
a = pd.read_csv(ROOT / 'inputs/annotator1_drive.csv')
b = pd.read_csv(ROOT / 'inputs/annotator2_drive.csv')
keys = ['platform', 'username', 'clean_text']
for frame in [o, a, b]:
    for key in keys:
        frame[key] = frame[key].fillna('').astype(str)

# Conservative matching: exclude any non-unique source key rather than inflate n.
unique_o = o.loc[~o.duplicated(keys, keep=False)]
paired = a.merge(b[['validation_id'] + [c for c in b if c.startswith('annotator_label_')]],
                 on='validation_id', suffixes=('_a1', '_a2'), validate='one_to_one')
assert not paired.duplicated(keys).any()
matched = paired.merge(unique_o[keys + ['id', 'triage', 'parent_context', 'triage_reason']],
                       on=keys, how='inner', validate='one_to_one')
rows = []
def metrics(y, pred):
    tp, fp = int((y & pred).sum()), int((~y & pred).sum())
    fn, tn = int((y & ~pred).sum()), int((~y & ~pred).sum())
    return dict(n=len(y), tp=tp, fp=fp, fn=fn, tn=tn,
                precision=tp/(tp+fp) if tp+fp else None,
                recall=tp/(tp+fn) if tp+fn else None,
                f1=2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else None)

for annotator in ['a1', 'a2']:
    domain = matched[f'annotator_label_domain_relevant_{annotator}'].eq(1)
    substantive = (domain & matched[f'annotator_label_genuine_discourse_{annotator}'].eq(1)
                   & matched[f'annotator_label_listing_or_promotion_{annotator}'].eq(0)
                   & matched[f'annotator_label_low_information_{annotator}'].eq(0))
    matched[f'reference_substantive_{annotator}'] = substantive
    for name, categories, truth in [
        ('strict_discussion_candidates', ['property_discussion_candidates'], substantive),
        ('discussion_plus_context_review', ['property_discussion_candidates', 'context_dependent', 'short_property_context_needed'], substantive),
        ('property_domain_review', ['property_discussion_candidates', 'context_dependent', 'short_property_context_needed', 'property_promotion_candidates'], domain),
    ]:
        pred = matched.triage.isin(categories)
        rows.append(dict(annotator=annotator, policy=name, **metrics(truth, pred)))
matched.to_csv(OUT/'matched_existing_labels.csv', index=False)
pd.DataFrame(rows).to_csv(OUT/'existing_label_metrics.csv', index=False)

# Fresh sample for qualitative inspection. Source text/context only, shuffled;
# predictions are withheld from the review sheet. This is NOT human gold data.
sample = pd.concat([g.sample(min(10, len(g)), random_state=20260907)
                    for _, g in o.groupby('triage')]).sample(frac=1, random_state=17).reset_index(drop=True)
sample['review_id'] = ['OUT_REVIEW_%03d' % (i+1) for i in range(len(sample))]
sample[['review_id', 'id', 'triage']].to_csv(OUT/'fresh_sample_key.csv', index=False)
review = sample[['review_id','id','platform','clean_text','parent_context']].copy()
review['reviewer_property_link'] = ''
review['reviewer_substantive_discussion'] = ''
review['reviewer_reason'] = ''
review.to_csv(OUT/'fresh_sample_review.csv', index=False)

summary = dict(matched_records=len(matched), total_validation_records=len(a),
               ambiguous_outlier_key_rows=int(o.duplicated(keys, keep=False).sum()),
               matched_categories=matched.triage.value_counts().to_dict(),
               reference_type='Existing human labels, annotators evaluated separately; version independence unresolved',
               generalization='Matched prefiltered validation records only; not population estimates',
               fresh_review_sample=len(sample),
               frozen_triage_sha256=hashlib.sha256((ROOT/'followup/all_outliers_with_triage.csv').read_bytes()).hexdigest(),
               metrics=rows)
(OUT/'evaluation_summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
print(json.dumps(summary, indent=2))
