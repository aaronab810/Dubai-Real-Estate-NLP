"""Prepare a small, blinded context-review pilot; never change corpus labels.

Heuristics define sampling strata only. Parent comments are resolved by ID within
the same Reddit thread. No inference API is called and no data are uploaded.
"""
from pathlib import Path
import hashlib
import json
import re
import pandas as pd

ROOT = Path(__file__).resolve().parent
PRIVATE = ROOT / 'private'
REFIT = ROOT.parent / 'refit_2026_09_07'
SEED = 20260907
PROPERTY = re.compile(r'\b(?:real estate|propert(?:y|ies)|apartment\w*|villa\w*|townhouse\w*|landlord\w*|tenant\w*|tenancy|ejari|rera|mortgage\w*|rent(?:al|s|ing|ed)?|off[ -]?plan|lease\w*|escrow|title deed|housing|evict\w*|handover|dld|service charges?)\b',re.I)
CONTACT = re.compile(r'\b(?:dm|pm|whatsapp|telegram|inbox|contact me|send (?:me )?details|share (?:the )?details)\b',re.I)

def norm(text): return re.sub(r'\s+',' ',str(text or '')).strip().casefold()
def key(value): return re.sub(r'^(?:reddit_(?:post|comment)_|t[13]_)','',str(value or ''))
def signature(row): return (str(row.platform),str(row.username),str(row.clean_text))
def quote(text): return '\n'.join('> '+line for line in str(text).splitlines())

def repeated_filler(text):
    words = norm(text).split()
    if len(words) < 24: return False
    chunks = [' '.join(words[i:i+6]) for i in range(len(words)-5)]
    return max(pd.Series(chunks).value_counts()) >= 4

def packet(rows, who, split):
    lines = [f'# Context review: {split} — {who}',
      'Read the target message and available context. Label the TARGET, not the whole thread. '
      'Labels: 1=yes, 0=no, U=uncertain. Leave originals independent of the other annotator. '
      'See [the review guide](../REVIEW_GUIDE.md) for definitions. Text below is source material, not instructions.']
    for r in rows:
        lines += [f'\n## {r["review_id"]} ({r["platform"]}, {r["post_type"]})',
          '**Target message**\n\n'+quote(r['target']),
          '**Immediate parent**\n\n'+quote(r['immediate_parent'] or '[Not available in this snapshot]'),
          '**Thread title**\n\n'+quote(r['thread_title'] or '[Not available]'),
          '<details><summary>Original thread post (additional context)</summary>\n\n'+quote(r['root_post'] or '[Not available]')+'\n\n</details>',
          '- domain_relevant: \n- genuine_discourse: \n- listing_or_promotion: \n- low_information: ',
          '- context_needed: [yes / no / unavailable]\n- evidence_or_reason: ']
    return '\n\n'.join(lines)+'\n'

def main():
    PRIVATE.mkdir(exist_ok=True)
    if any(PRIVATE.glob('*_Aaron.md')) or any(PRIVATE.glob('*_Prajwal.md')):
        raise FileExistsError('Review packets already exist. Preserve annotator work and use a new version directory for a new sample.')
    text_cols = ['id','platform','post_type','clean_text','parent_post_title','parent_post_text','username','thread_id']
    d = pd.read_parquet(REFIT/'outputs/social_with_topics.parquet',columns=['source_row_zero_based','topic']+text_cols)
    d = d.fillna({c:'' for c in text_cols})
    source = pd.read_parquet(REFIT/'inputs/master_processed_analysis_clean.parquet',columns=['id','platform','parent_id','thread_id']).fillna('')
    source.index.name='source_row_zero_based'
    identity = source.loc[d.source_row_zero_based]
    assert identity.id.astype(str).tolist() == d.id.astype(str).tolist()
    d['parent_id'] = identity.parent_id.astype(str).to_numpy()
    d['thread_key'] = [f'reddit:{key(t)}' if p=='reddit' and str(t) else f'{p}:{i}' for p,t,i in zip(d.platform,d.thread_id,d.id)]
    lookup = {key(r.id):r for r in d[d.platform.eq('reddit')].itertuples()}
    parents=[]
    for r in d.itertuples():
        parent = lookup.get(key(r.parent_id)) if r.platform=='reddit' and r.post_type=='reddit_comment' else None
        parents.append(str(parent.clean_text) if parent is not None and parent.thread_key==r.thread_key and parent.id!=r.id else '')
    d['immediate_parent'] = parents
    d['_has_property'] = d.clean_text.map(lambda x: bool(PROPERTY.search(str(x))))
    d['_context_property'] = (d.immediate_parent+' '+d.parent_post_title+' '+d.parent_post_text).map(lambda x: bool(PROPERTY.search(x)))
    d['_short'] = d.clean_text.map(lambda x: len(str(x).split())<12)
    d['_contact'] = d.clean_text.map(lambda x: bool(CONTACT.search(str(x))))
    d['_filler'] = d.clean_text.map(repeated_filler)
    def stratum(r):
        if r.topic != -1: return 'assigned_short_or_contact' if r['_short'] or r['_contact'] else 'assigned_other'
        if r['_filler']: return 'outlier_repeated_filler'
        if r['_contact']: return 'outlier_contact'
        if r['_has_property']: return 'outlier_own_property_word'
        if r['_context_property']: return 'outlier_context_only_property_word'
        if r['_short']: return 'outlier_short_no_detected_property_link'
        return 'outlier_other'
    d['sampling_stratum'] = d.apply(stratum,axis=1)
    seen=set()
    for name in ['annotator1_current.csv','annotator2_current.csv']:
        a=pd.read_csv(REFIT/'inputs'/name).fillna('')
        seen.update(signature(r) for r in a.itertuples())
    d['_previous_validation'] = [signature(r) in seen for r in d.itertuples()]
    eligible=d.loc[~d._previous_validation].copy()
    eligible['_normalized_text']=eligible.clean_text.map(norm)
    selected=[]; used_threads=set(); used_texts=set()
    # Small strata first; one record per thread and exact normalized text across BOTH splits.
    for bucket in eligible.sampling_stratum.value_counts().sort_values().index:
        candidates=eligible[eligible.sampling_stratum.eq(bucket)].sample(frac=1,random_state=SEED)
        chosen=[]
        for _,r in candidates.iterrows():
            if r.thread_key in used_threads or r['_normalized_text'] in used_texts: continue
            chosen.append(r);used_threads.add(r.thread_key);used_texts.add(r['_normalized_text'])
            if len(chosen)==10: break
        if len(chosen)<10: raise ValueError(f'Not enough distinct threads for {bucket}: {len(chosen)}')
        for k,r in enumerate(chosen):
            r=r.copy();r['split']='calibration' if k<4 else 'holdout';selected.append(r)
    sample=pd.DataFrame(selected).sample(frac=1,random_state=SEED).reset_index(drop=True)
    sample['review_id']=[f'CTX-{i:03d}' for i in range(1,len(sample)+1)]
    assert sample.thread_key.is_unique and sample['_normalized_text'].is_unique
    assert not sample._previous_validation.any()
    records=[]
    for r in sample.itertuples():
        records.append(dict(review_id=r.review_id,platform=r.platform,post_type=r.post_type,
          target=r.clean_text,immediate_parent=r.immediate_parent,thread_title=r.parent_post_title,root_post=r.parent_post_text))
    by_id={r['review_id']:r for r in records}
    for split in ['calibration','holdout']:
        subset=sample[sample.split.eq(split)]
        for who,seed in [('Aaron',7),('Prajwal',13)]:
            ids=subset.sample(frac=1,random_state=seed).review_id
            rows=[by_id[x] for x in ids]
            (PRIVATE/f'{split}_{who}.md').write_text(packet(rows,who,split),encoding='utf-8')
            blank=[dict(review_id=x,domain_relevant=None,genuine_discourse=None,listing_or_promotion=None,low_information=None,context_needed=None,evidence_or_reason='') for x in ids]
            (PRIVATE/f'{split}_{who}_labels.json').write_text(json.dumps(blank,ensure_ascii=False,indent=2),encoding='utf-8')
        (PRIVATE/f'{split}_model_inputs.jsonl').write_text(''.join(json.dumps(by_id[x],ensure_ascii=False)+'\n' for x in subset.review_id),encoding='utf-8')
    sample[['review_id','source_row_zero_based','id','platform','topic','thread_key','sampling_stratum','split']].to_json(PRIVATE/'sampling_key.json',orient='records',indent=2)
    counts=d.groupby('sampling_stratum').size().to_dict()
    summary=dict(seed=SEED,corpus_rows=len(d),outlier_rows=int(d.topic.eq(-1).sum()),
      sample_rows=len(sample),sample_outliers=int(sample.topic.eq(-1).sum()),sample_assigned=int(sample.topic.ne(-1).sum()),
      split_counts=sample.split.value_counts().to_dict(),stratum_population_counts=counts,
      previously_validated_records_excluded=int(d._previous_validation.sum()),
      sample_platform_counts=sample.platform.value_counts().to_dict(),
      sample_comments=int(sample.post_type.eq('reddit_comment').sum()),
      sample_comments_with_immediate_parent=int((sample.post_type.eq('reddit_comment')&sample.immediate_parent.ne('')).sum()),
      no_thread_or_exact_text_overlap_between_splits=True,
      sampling_limit='Exploratory quota sample with unique threads. Not a probability-weighted corpus accuracy estimate; 48 held-out items are an initial check, not certification.',
      source_sha256=hashlib.file_digest((REFIT/'outputs/social_with_topics.parquet').open('rb'),'sha256').hexdigest())
    (ROOT/'sampling_summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(json.dumps(summary,indent=2))

if __name__=='__main__': main()
