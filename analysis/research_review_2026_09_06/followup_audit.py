"""Recheck annotation versions, author repeats, and triage every outlier.

Triage labels are transparent rule-based CANDIDATES, not validated relevance
judgments or new BERTopic assignments. No source rows are deleted or relabelled.
"""
from pathlib import Path
import json
import re
import argparse
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'followup'
OUT.mkdir(exist_ok=True)
parser=argparse.ArgumentParser()
parser.add_argument('--annotator2',type=Path,required=True)
args=parser.parse_args()
def save(df,name): df.to_csv(OUT/name,index=False)
def norm(s): return s.fillna('').astype(str).str.lower().str.replace(r'\s+',' ',regex=True).str.strip()
def normalize_id(s): return s.fillna('').astype(str).str.replace(r'^(?:reddit_post_|t3_)','',regex=True)

a=pd.read_csv(ROOT/'inputs/annotator1_drive.csv')
b=pd.read_csv(ROOT/'inputs/annotator2_drive.csv')
supplied=pd.read_csv(args.annotator2)
old=pd.read_csv(ROOT/'inputs/disagreements_drive.csv')
assert b.fillna('').equals(supplied.fillna(''))
paired=a.merge(b,on='validation_id',suffixes=('_a1','_a2'),validate='one_to_one')
labels=['domain_relevant','genuine_discourse','listing_or_promotion','low_information']
paired['any_disagreement']=False
for label in labels:
    paired['any_disagreement'] |= paired['annotator_label_'+label+'_a1'].ne(paired['annotator_label_'+label+'_a2'])
old_link=old.merge(a,on='domain_context_text',validate='one_to_one').merge(b[['validation_id']+['annotator_label_'+l for l in labels]],on='validation_id',suffixes=('_current_a1','_current_a2'),validate='one_to_one')
assert len(old_link)==120
old_link['any_a1_version_difference']=False
version_counts={}
for label in labels:
    different=old_link[label+'_A1'].ne(old_link['annotator_label_'+label+'_current_a1'])
    old_link[label+'_a1_version_difference']=different
    old_link['any_a1_version_difference'] |= different
    assert old_link[label+'_A2'].eq(old_link['annotator_label_'+label+'_current_a2']).all()
    version_counts[label]=int(different.sum())
save(old_link[['validation_id','domain_context_text','any_a1_version_difference']+
    [c for c in old_link if c.endswith('_A1') or c.endswith('_A2') or c.endswith('_current_a1') or c.endswith('_current_a2')]],'annotation_version_comparison.csv')

d=pd.read_csv(ROOT/'inputs/smdi_posts.csv',low_memory=False,dtype={'id':str})
d['_text']=norm(d.clean_text)
d['_author']=norm(d.username)
d.loc[d._author.isin(['[deleted]','deleted','none','nan','unknown','[removed]']),'_author']=''
d['_date']=pd.to_datetime(d.date,utc=True)
g=d[d.semantic_group.eq(16)&d.topic.ne(-1)].copy().sort_values(['_date','id'])
group_rows=[]
for (platform,text),z in g.groupby(['platform','_text'],sort=False):
    if len(z)<2: continue
    known=z[z._author.ne('')]
    same=len(known)-known._author.nunique()
    cross=max(known._author.nunique()-1,0)
    group_rows.append(dict(platform=platform,normalized_text=text,rows=len(z),
        known_authors=known._author.nunique(),authors=' | '.join(z._author.unique()),
        same_author_extras=same,cross_author_extras=cross,
        unknown_author_extras=len(z)-1-same-cross,
        thread_count=z.thread_id.nunique(),topic_count=z.topic.nunique()))
groups=pd.DataFrame(group_rows).sort_values('rows',ascending=False)
assert groups.same_author_extras.sum()+groups.cross_author_extras.sum()+groups.unknown_author_extras.sum()==2418
save(groups,'repeated_text_172_groups.csv')
g['same_author_repeat']=g._author.ne('')&g.duplicated(['platform','_author','_text'])
g['same_thread_same_author_repeat']=g._author.ne('')&g.thread_id.notna()&g.duplicated(['platform','_author','thread_id','_text'])
g['known_automoderator']=g.platform.eq('reddit')&g._author.eq('automoderator')
cols=['id','platform','post_type','username','thread_id','topic','date','clean_text','same_author_repeat','same_thread_same_author_repeat','known_automoderator']
save(g.loc[g.same_author_repeat,cols],'same_author_repeats_2328.csv')
same_nonbot=g[g.same_author_repeat&~g.known_automoderator]
save(same_nonbot[cols],'same_author_nonbot_repeats.csv')
retained=g[~g.same_author_repeat].copy()
retained['cross_author_extra']=retained._author.ne('')&retained.duplicated(['platform','_text'])
save(retained.loc[retained.cross_author_extra,cols],'different_author_extras_90.csv')
save(g[g.known_automoderator][cols],'group16_automoderator_rows.csv')
save(g.groupby(['platform','_author']).agg(records=('id','size'),same_author_extras=('same_author_repeat','sum'),same_thread_extras=('same_thread_same_author_repeat','sum')).reset_index().sort_values('same_author_extras',ascending=False),'repeat_counts_by_author.csv')

# Reconstruct only parent-post context that exists in this snapshot.
parents=d[d.post_type.eq('reddit_post')].copy()
parents['_post_key']=normalize_id(parents.id)
parent_text=parents.drop_duplicates('_post_key').set_index('_post_key').clean_text
o=d[d.topic.eq(-1)].copy()
o['source_row_zero_based']=o.index
o['parent_context']=normalize_id(o.thread_id).map(parent_text).where(o.post_type.eq('reddit_comment'))
o['parent_context_available']=o.parent_context.notna()
o['parent_context_source']=''
o.loc[o.parent_context_available,'parent_context_source']='reddit parent post in the same smdi_posts.csv snapshot'

property_pattern=r'\b(?:real estate|propert(?:y|ies)|apartment(?:s)?|villa(?:s)?|townhouse(?:s)?|landlord(?:s)?|tenant(?:s)?|tenancy|ejari|rera|mortgage(?:s)?|rental(?:s)?|rent(?:s|ing|ed)?|off[ -]?plan|lease(?:s|hold)?|freehold|escrow|title deed|service charges?|security deposit|handover|housing|home prices?|house prices?|eviction|evict(?:ed|ing)?|dld|rental dispute|conveyanc(?:ing|er))\b'
geo_pattern=r'\b(?:dubai|uae|abu dhabi|sharjah|ajman|jvc|jvt|jlt|jbr|jumeirah|meydan|arjan|emaar|damac|sobha|nakheel|azizi|binghatti|deira|barsha|al furjan|business bay|dubai south|dubai hills|international city|dubai marina|palm jumeirah)\b'
housing_specific=r'\b(?:apartment|villa|townhouse|landlord|tenant|tenancy|ejari|rera|mortgage|off[ -]?plan|leasehold|freehold|title deed|housing|dld|eviction)\b'
own=o._text
context=norm(o.parent_context)
o['property_terms']=own.str.findall(property_pattern).apply(lambda z:' | '.join(sorted(set(z))))
o['own_property_signal']=o.property_terms.ne('')
o['parent_property_signal']=context.str.contains(property_pattern,regex=True)
o['geography_signal']=(own.str.contains(geo_pattern,regex=True)|context.str.contains(geo_pattern,regex=True)|norm(o.subreddit).isin(['dubai','dubairealestate'])|norm(o.url).str.contains(r'/r/(?:dubai|dubairealestate)/',regex=True))
o['word_count']=own.str.split().str.len()
o['contact_signal']=own.str.contains(r'\bdm\b|whatsapp|contact me|message me|call me|check (?:your )?inbox',regex=True)
o['offer_signal']=own.str.contains(r'\b(?:for sale|for rent|selling price|asking price|unit details|exclusive listing|distress deals?|i have (?:a |an |one |[0-9])|i can offer|book (?:a |your )?viewing|payment plan|limited units|investment opportunity|start your .*investment journey)\b',regex=True)
o['marketing_signal']=own.str.contains(r'\b(?:check out my latest|i just published|our clients|our latest|contact us|book now|register now|dm me for|for more details dm|experience the|introducing our|start your .*investment journey)\b',regex=True)
o['listing_features']=own.str.findall(r'\b(?:bedrooms?|bathrooms?|bua|sq\.?\s*ft|sqft|plot|payment plan|selling price|asking price|property details|unit details)\b').apply(lambda x:len(set(x)))
o['listing_format_signal']=o.listing_features.ge(4)&own.str.contains(r'\b(?:price|aed|[0-9]+\.?[0-9]*m)\b',regex=True)
o['general_uae_geopolitics']=o.geography_signal&own.str.contains(r'\b(?:war|missile|drone|iran|israel|conflict|bomb|attack|ceasefire|geopolitic\w*)\b',regex=True)&~o.own_property_signal&~o.parent_property_signal
o['automated_signal']=o._author.str.contains(r'^(?:automoderator|autotldr)$',regex=True)|own.str.contains(r'i am a bot, and this action was performed automatically',regex=False)
o['vehicle_rental_ambiguity']=own.str.contains(r'car rental|rent(?:ing)? (?:a |the )?car|rental car|private jet|rent.free (?:in|inside)',regex=True)&~own.str.contains(housing_specific,regex=True)
o['triage']='uncertain_or_other'
o['triage_reason']='No sufficiently explicit rule-based property-discussion evidence; may still contain relevant records.'
def route(mask,name,reason):
    o.loc[mask,'triage']=name
    o.loc[mask,'triage_reason']=reason

route(o.general_uae_geopolitics,'geopolitics_excluded_no_property_link','Outside the user-confirmed recovery scope: general Dubai/UAE geopolitical discussion without a detected property link in the record or available parent context. Rule-based exclusion remains reviewable.')
route(o.parent_context_available&o.parent_property_signal&~o.own_property_signal&~o.general_uae_geopolitics,'context_dependent','Parent post has property terms; this record needs its conversation to establish its contribution.')
route(o.geography_signal&o.own_property_signal&o.word_count.ge(12)&~o.vehicle_rental_ambiguity,'property_discussion_candidates','Explicit property terms and Dubai/UAE context, at least 12 words; relevance/discourse candidate only, not a validated acceptance.')
route(o.geography_signal&o.own_property_signal&o.word_count.lt(12),'short_property_context_needed','Explicit property terms but fewer than 12 words; preserve for contextual interpretation.')
route(o.geography_signal&(o.own_property_signal|o.parent_property_signal)&((o.contact_signal&o.offer_signal)|o.marketing_signal|o.listing_format_signal),'property_promotion_candidates','Property context plus offer-and-contact cues, explicit marketing or listing-format language; candidate, not a validated advertising label.')
route(o.automated_signal,'automated_candidates','Known bot account or explicit automated-action notice.')

# Preserve every original outlier, all original columns and auditable rule evidence.
o=o.drop(columns=['_text','_author','_date'])
assert len(o)==41887 and o.id.nunique()==41887
save(o,'all_outliers_with_triage.csv')
for label,subset in o.groupby('triage'):
    save(subset,f'outliers_{label}.csv')
triage_summary=o.groupby('triage').agg(rows=('id','size'),with_parent_context=('parent_context_available','sum')).reset_index()
save(triage_summary,'outlier_triage_summary.csv')
samples=pd.concat([z.sample(min(20,len(z)),random_state=42) for _,z in o.groupby('triage')])
save(samples[['source_row_zero_based','id','triage','triage_reason','clean_text','parent_context','property_terms']],'outlier_triage_review_sample.csv')

# Fields sufficient for extra descriptive indicators; no new sentiment scores.
d['week']=d._date.dt.tz_localize(None).dt.to_period('W').dt.start_time
stats=[]
for (week,platform,label),z in d[d.SMDI.notna()].groupby(['week','platform','SMDI']):
    platform_week=d[d.week.eq(week)&d.platform.eq(platform)]
    authors=z[z._author.ne('')]
    p=authors._author.value_counts(normalize=True)
    stats.append(dict(week=week,platform=platform,SMDI=label,frequency=len(z),
        platform_theme_share_pct=100*len(z)/len(platform_week),
        identified_authors=authors._author.nunique(),author_id_coverage_pct=100*len(authors)/len(z),
        author_hhi=float((p*p).sum()) if len(p) else np.nan,
        top_author_share_pct=float(p.max()*100) if len(p) else np.nan,
        distinct_threads=z.thread_id.nunique() if platform=='reddit' else np.nan,
        engagement_observed=int(z.platform_interaction_value.notna().sum()),
        median_engagement=z.platform_interaction_value.median(),
        mean_engagement=z.platform_interaction_value.mean()))
metrics=pd.DataFrame(stats).sort_values(['platform','SMDI','week'])
# Only full social weeks for week-to-week comparisons. Include true zero theme weeks.
full_weeks=pd.date_range('2026-01-05','2026-04-20',freq='W-MON')
index=pd.MultiIndex.from_product([full_weeks,sorted(d.platform.unique()),sorted(d.SMDI.dropna().unique())],names=['week','platform','SMDI'])
metrics=metrics.set_index(['week','platform','SMDI']).reindex(index).reset_index().sort_values(['platform','SMDI','week'])
metrics['frequency']=metrics.frequency.fillna(0)
for c in ['platform_theme_share_pct','identified_authors','distinct_threads','engagement_observed']:
    if c!='distinct_threads':metrics[c]=metrics[c].fillna(0)
metrics['frequency_change']=metrics.groupby(['platform','SMDI']).frequency.diff()
metrics['previous_four_week_mean']=metrics.groupby(['platform','SMDI']).frequency.transform(lambda x:x.shift(1).rolling(4,min_periods=4).mean())
metrics['surge_ratio_vs_previous_four_weeks']=metrics.frequency.div(metrics.previous_four_week_mean.where(metrics.previous_four_week_mean.ne(0)))
save(metrics,'weekly_additional_indicators.csv')
summary=dict(annotator2_drive_equals_user_attachment=True,old_disagreement_contexts_matched=len(old_link),
    current_disagreement_rows=int(paired.any_disagreement.sum()),
    old_rows_with_different_current_annotator1=int(old_link.any_a1_version_difference.sum()),
    annotator1_field_differences=version_counts,annotator2_field_differences=0,
    repeated_text_groups=len(groups),same_author_extras=int(groups.same_author_extras.sum()),
    cross_author_extras=int(groups.cross_author_extras.sum()),unknown_author_extras=int(groups.unknown_author_extras.sum()),
    automoderator_rows=int(g.known_automoderator.sum()),automoderator_repeat_extras=int((g.known_automoderator&g.same_author_repeat).sum()),
    same_author_nonbot_extras=len(same_nonbot),same_thread_same_author_extras=int(g.same_thread_same_author_repeat.sum()),
    outlier_triage=triage_summary.to_dict('records'),all_outliers_preserved=len(o),
    triage_is_validated=False,triage_changes_topic_assignments=False,
    geopolitical_relevance_policy='Require a property link; general geopolitical discussion alone is outside outlier-recovery scope.')
(OUT/'followup_summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
print(json.dumps(summary,indent=2))
