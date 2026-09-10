"""Rebuild a deterministic activity corpus from identified source snapshots.

The code contains no DLD outcome or downstream association selection. Human labels
are preserved as historical development evidence, never silently adjudicated.
"""
from pathlib import Path
import ast
import hashlib
import html
import json
import re
import sys
import importlib.metadata as md
import numpy as np
import pandas as pd
import emoji

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
OLD=ROOT/'analysis/paper_strengthening_2026_09_09/private'
P=HERE/'private'
OUT=HERE/'results'
P.mkdir(exist_ok=True);OUT.mkdir(exist_ok=True)

def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(2**20),b''):h.update(b)
    return h.hexdigest()

def clean(v,platform='reddit'):
    v='' if pd.isna(v) else html.unescape(str(v))
    if platform=='x':
        v=emoji.demojize(v,delimiters=(' :',': '))
        v=re.sub(r'@\w+',' ',v)
        v=re.sub(r'#(\w+)',r'\1',v)
    v=re.sub(r'https?://\S+|www\.\S+',' ',v,flags=re.I)
    return re.sub(r'\s+',' ',v).strip()

def idclean(s):return s.fillna('').astype(str).str.replace(r'^t[13]_','',regex=True).str.strip()
def phrase_pattern(words):return re.compile(r'(?<!\w)(?:'+'|'.join(re.escape(w) for w in sorted(words,key=len,reverse=True))+r')(?!\w)',re.I)

# Reuse the source lexicon but exclude geographically/generically broad words as
# sufficient property evidence; retain named property communities and developers.
nb=json.loads((ROOT/'notebooks/twitter_reddit_merge.ipynb').read_text(encoding='utf8'))
env={'sorted':sorted,'set':set}
for c in nb['cells']:
    if c['cell_type']!='code':continue
    try:tree=ast.parse(''.join(c['source']))
    except SyntaxError:continue
    for node in tree.body:
        if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id in ['DOMAIN_KEYWORDS'] for t in node.targets):
            exec(compile(ast.Module(body=[node],type_ignores=[]),'reviewed_literal_lexicon','exec'),env)
generic={'dubai','uae','home','homes','unit','units','land','buy','buying','buyer','buyers','sell','selling','seller','sellers','purchase','launch','project','agent','agents','broker','brokers','studio','studios','bedroom','mag','marina','downtown','dip'}
terms=sorted((set(env['DOMAIN_KEYWORDS'])-generic)|{'rents','tenancy','renters','renter','rental contract','housing affordability','housing prices','house prices','property prices','property agent','property broker','real estate broker','real estate agents','property developer','developers','renting out','house purchase','property purchase'})
DOMAIN=phrase_pattern(terms)
CONTACT=phrase_pattern(['whatsapp','call now','contact us','contact me','contact for','dm me','dm for','dm details','send me a dm','pm me','book viewing','schedule a viewing','book your unit','register your interest','link in bio'])
LISTING=phrase_pattern(['for sale','for rent','selling my','available now','ready to move','limited offer','exclusive offer','starting at','motivated seller','distress deal','below original price','below op','dld waiver','rera permit','permit no','reference no'])
SPEC=re.compile(r'\b(?:aed|sq\s*ft|sqft|[1-9]\s*(?:br|b/r)|fully furnished|payment plan|brand new|vacant)\b',re.I)
SOLICIT=re.compile(r'\b(?:i(?: am|\x27m)?|we(?: are|\x27re)?|my|our)\b.{0,55}\b(?:offer|offering|selling|leasing|listing|inventory|broker|agent)\b',re.I)
CONTACT_ONLY=re.compile(r'^(?:(?:hi|hello|hey|please|pls|kindly|just|i|you|your|a|me|my|have|the|in|for|and|sent|send|check|checked|message|messaged|dm|dmed|pm|inbox|private|chat|connect|connected|details|interested|thanks|thank|already|you)\W*){1,14}$',re.I)
REACTION=phrase_pattern(['thanks','thank you','thx','lol','lmao','bump','following'])
DELETED=re.compile(r'^\s*\[(?:deleted|removed)\]\s*$',re.I)

def main():
    x=pd.read_parquet(OLD/'x_merged.parquet').copy()
    x['id']=x.id.astype(str);x['platform']='x';x['post_type']='x_post'
    x['raw_text']=x.text.fillna('');x['clean_text']=x.raw_text.map(lambda z:clean(z,'x'))
    x['source_date']=x.date.astype(str)
    x['timestamp_utc']=pd.to_datetime(x.id.map(lambda v:(int(v)>>22)+1288834974657),unit='ms',utc=True)
    assert x.timestamp_utc.dt.date.eq(pd.to_datetime(x.date,utc=True).dt.date).all()
    x['timestamp_source']='x_snowflake_ms';x['thread_id']='';x['parent_id']='';x['context_text']='';x['parent_text']='';x['subreddit']=''
    x['source_english']=x.lang.str.lower().isin(['en','english'])
    x['platform_interaction_value']=sum(pd.to_numeric(x[c],errors='coerce').fillna(0) for c in ['likeCount','retweetCount','replyCount','quoteCount'])
    x['source_file']='x_merged.parquet'
    rp=pd.read_csv(OLD/'combined_reddit_posts.csv',low_memory=False).fillna('')
    rc=pd.read_csv(OLD/'combined_reddit_comments.csv',low_memory=False).fillna('')
    posts=pd.DataFrame({'id':idclean(rp.post_id),'platform':'reddit','post_type':'reddit_post','raw_text':(rp.title+' '+rp.selftext).str.strip(),'username':rp.post_author,'subreddit':rp.subreddit,'source_date':rp.date,'thread_id':idclean(rp.post_id),'parent_id':'','url':rp.permalink,'platform_interaction_value':pd.to_numeric(rp.post_score,errors='coerce'),'source_file':'combined_reddit_posts.csv','source_english':True})
    posts['clean_text']=posts.raw_text.map(clean);posts['timestamp_utc']=pd.to_datetime(posts.source_date,utc=True);posts['timestamp_source']='reddit_source_seconds';posts['context_text']='';posts['parent_text']=''
    postlookup=dict(zip(posts.id,posts.clean_text));sublut=dict(zip(posts.id,posts.subreddit))
    # All available comments form the parent lookup, regardless of analytic eligibility.
    commentlookup=dict(zip('t1_'+idclean(rc.comment_id),rc.body.map(clean)))
    parentlookup={**{'t3_'+k:v for k,v in postlookup.items()},**commentlookup}
    rderaw=pd.read_csv(OLD/'rde_raw_comments.csv',usecols=['id','subreddit'],low_memory=False)
    rdesub=dict(zip(idclean(rderaw.id),rderaw.subreddit))
    comments=pd.DataFrame({'id':idclean(rc.comment_id),'platform':'reddit','post_type':'reddit_comment','raw_text':rc.body,'username':rc.comment_author,'source_date':rc.date,'thread_id':idclean(rc.post_id),'parent_id':rc.parent_id.astype(str),'url':rc.permalink,'platform_interaction_value':pd.to_numeric(rc.comment_score,errors='coerce'),'source_file':'combined_reddit_comments.csv','source_english':True})
    comments['subreddit']=comments.thread_id.map(sublut).fillna(comments.id.map(rdesub)).fillna('unknown')
    comments['clean_text']=comments.raw_text.map(clean)
    comments['timestamp_utc']=pd.to_datetime(comments.source_date,utc=True);comments['timestamp_source']='reddit_source_seconds'
    comments['context_text']=comments.thread_id.map(postlookup).fillna('')
    comments['parent_text']=comments.parent_id.map(parentlookup).fillna('')
    # Markers remain represented by IDs, never as substantive linguistic context.
    comments.loc[comments.parent_text.str.match(DELETED),'parent_text']=''
    fields=['id','platform','post_type','raw_text','clean_text','username','subreddit','source_date','timestamp_utc','timestamp_source','thread_id','parent_id','context_text','parent_text','url','platform_interaction_value','source_file','source_english']
    d=pd.concat([x[fields],posts[fields],comments[fields]],ignore_index=True)
    d['record_key']=d.platform+':'+d.post_type+':'+d.id
    d['source_row']=np.arange(len(d))
    assert not d.record_key.duplicated().any()
    d['date_local']=d.timestamp_utc.dt.tz_convert('Asia/Dubai')
    d['week']=d.date_local.dt.tz_localize(None).dt.to_period('W-SUN').dt.start_time
    d['word_count']=d.clean_text.str.findall(r'\b\w+\b').str.len()
    d['has_target_property_cue']=d.clean_text.str.contains(DOMAIN)
    d['has_context_property_cue']=(d.context_text+' '+d.parent_text).str.contains(DOMAIN)
    d['domain_relevant_rule']=d.has_target_property_cue | (d.post_type.eq('reddit_comment') & d.has_context_property_cue)
    d['contact_cue']=d.clean_text.str.contains(CONTACT)
    d['listing_cue']=d.clean_text.str.contains(LISTING)
    d['spec_cue']=d.clean_text.str.contains(SPEC)
    d['solicitation_cue']=d.clean_text.str.contains(SOLICIT)
    # Text from a parent may establish relevance, but never causes target ad exclusion.
    d['target_promotion_rule']=(d.contact_cue & (d.has_target_property_cue|d.spec_cue|d.listing_cue)) | (d.listing_cue & d.spec_cue & d.solicitation_cue)
    d['promotion_ambiguous_flag']=(d.contact_cue|d.listing_cue|d.solicitation_cue) & ~d.target_promotion_rule
    d['contact_only_rule']=d.post_type.eq('reddit_comment') & d.clean_text.str.fullmatch(CONTACT_ONLY) & d.word_count.le(14)
    d['reaction_only_rule']=d.post_type.eq('reddit_comment') & d.clean_text.str.fullmatch(REACTION) & d.word_count.le(3)
    # Numeric answers, yes/no, questions and dissent are not deleted for brevity.
    d['short_context_flag']=d.post_type.eq('reddit_comment') & d.word_count.le(5)
    d['known_moderator']=d.platform.eq('reddit') & d.username.fillna('').str.strip().str.casefold().str.replace(r'^/?u/','',regex=True).eq('automoderator')
    d['generic_username_bot_flag']=d.username.fillna('').str.contains(r'bot|auto|crawler|scraper|spam',case=False)
    d['missing_submission_context']=d.post_type.eq('reddit_comment') & d.context_text.eq('')
    d['missing_immediate_parent']=d.post_type.eq('reddit_comment') & d.parent_text.eq('')
    # Non-Latin scripts are flags: no claim of a validated multilingual/English detector.
    d['non_latin_flag']=d.clean_text.str.contains(re.compile('[\u0600-\u06ff\u0900-\u097f\u4e00-\u9fff]'))
    d['exact_text_key']=d.clean_text.str.casefold().str.replace(r'\s+',' ',regex=True).str.strip()
    d['text_family']=d.exact_text_key.map(lambda z:hashlib.sha256(z.encode()).hexdigest()[:24])
    d['exclusion_reason']=''
    conditions=[('invalid_or_outside_utc_capture_window',d.timestamp_utc.isna()|d.timestamp_utc.lt('2026-01-01')|d.timestamp_utc.ge('2026-05-01')),('empty_or_deleted_target',d.clean_text.eq('')|d.raw_text.str.match(DELETED)),('x_non_english_metadata',~d.source_english),('known_reddit_automoderator',d.known_moderator),('no_property_evidence',~d.domain_relevant_rule),('target_solicitation',d.target_promotion_rule),('contact_only',d.contact_only_rule),('reaction_only',d.reaction_only_rule)]
    flow=[];current=pd.Series(True,index=d.index)
    for step,mask in conditions:
        remove=current&mask;d.loc[remove,'exclusion_reason']=step;current &= ~mask
        for kind in ['x_post','reddit_post','reddit_comment']:
            flow.append(dict(stage=step,post_type=kind,removed=int((remove&d.post_type.eq(kind)).sum()),retained=int((current&d.post_type.eq(kind)).sum())))
    d['eligible']=current
    eligible=d[d.eligible].sort_values(['timestamp_utc','record_key']).copy().reset_index(drop=True)
    eligible['exact_family_size']=eligible.groupby(['platform','text_family']).id.transform('size')
    author=eligible.username.fillna('').str.strip().str.casefold().replace({'[deleted]':'','deleted':''})
    eligible['author_key']=author.where(author.ne(''),eligible.record_key)
    eligible['author_repeat']=eligible.duplicated(['platform','author_key','text_family'])
    eligible['training_representative']=~eligible.text_family.duplicated()
    eligible['training_key']=eligible.text_family
    # Preserve historical membership and annotation joins without sample-only edits.
    oldfit=pd.read_parquet(ROOT/'analysis/refit_2026_09_07/outputs/fit_input.parquet')
    oldkeys=set(oldfit.platform.replace({'twitter':'x'})+':'+oldfit.post_type.replace({'tweet':'x_post'})+':'+oldfit.id.astype(str))
    eligible['in_september_baseline']=eligible.record_key.isin(oldkeys)
    a=pd.read_csv(ROOT/'analysis/refit_2026_09_07/inputs/annotator1_verified_2026_09_09.csv').fillna('')
    b=pd.read_csv(ROOT/'analysis/refit_2026_09_07/inputs/annotator2_verified_2026_09_09.csv').fillna('')
    assert a.validation_id.equals(b.validation_id)
    joins=[]
    for r in a.itertuples():
        kind={'tweet':'x_post'}.get(r.post_type,r.post_type);p={'twitter':'x'}.get(r.platform,r.platform)
        candidates=d[d.platform.eq(p)&d.post_type.eq(kind)&d.clean_text.eq(r.clean_text)]
        method='exact_text'
        if len(candidates)!=1:
            # Source URL and author jointly identify the one documented text discrepancy.
            candidates=d[d.platform.eq(p)&d.post_type.eq(kind)&d.url.eq(r.url)&d.username.eq(r.username)]
            method='url_author'
        if len(candidates)!=1:
            legacy=oldfit[oldfit.clean_text.eq(r.clean_text)]
            if len(legacy)!=1:
                legacy=oldfit[oldfit.url.eq(r.url)&oldfit.username.eq(r.username)]
            if len(legacy)==1:
                candidates=d[d.platform.eq(p)&d.post_type.eq(kind)&d.id.eq(str(legacy.id.iloc[0]))]
                method='legacy_text_to_source_id'
        joins.append({'validation_id':r.validation_id,'matches':len(candidates),'record_key':candidates.record_key.iloc[0] if len(candidates)==1 else '', 'match_method':method,'eligible':bool(candidates.eligible.iloc[0]) if len(candidates)==1 else None})
    pd.DataFrame(joins).to_csv(P/'annotation_mapping.csv',index=False)
    assert all(j['matches']==1 for j in joins), 'Every original annotation must map uniquely'
    rel=[]
    for col in [c for c in a if c.startswith('annotator_label_')]:
        av=pd.to_numeric(a[col]);bv=pd.to_numeric(b[col]);po=float(av.eq(bv).mean());pe=float(av.mean()*bv.mean()+(1-av.mean())*(1-bv.mean()))
        rel.append(dict(criterion=col.replace('annotator_label_',''),n=len(a),both_yes=int((av.eq(1)&bv.eq(1)).sum()),both_no=int((av.eq(0)&bv.eq(0)).sum()),a_yes_b_no=int((av.eq(1)&bv.eq(0)).sum()),a_no_b_yes=int((av.eq(0)&bv.eq(1)).sum()),agreement=po,kappa=(po-pe)/(1-pe)))
    pd.DataFrame(rel).to_csv(OUT/'annotation_reliability.csv',index=False)
    eligible.to_parquet(P/'social_eligible.parquet',index=False)
    d.to_parquet(P/'social_all_flags.parquet',index=False)
    pd.DataFrame(flow).to_csv(OUT/'corpus_flow.csv',index=False)
    eligible.groupby(['platform','post_type','subreddit'],dropna=False).size().rename('records').reset_index().to_csv(OUT/'corpus_counts.csv',index=False)
    (eligible.groupby(['week','platform']).agg(records=('id','size'),threads=('thread_id','nunique'),authors=('author_key','nunique'),ambiguous_promotion=('promotion_ambiguous_flag','sum'),short_context=('short_context_flag','sum'),same_author_repeats=('author_repeat','sum')).reset_index()).to_csv(OUT/'weekly_corpus.csv',index=False)
    cross=d.assign(old=d.record_key.isin(oldkeys)).groupby(['old','eligible']).size().reset_index(name='records');cross.to_csv(OUT/'corpus_membership_reconciliation.csv',index=False)
    manifest={'version':'submission-corpus-v1','status':'computational freeze; target-quality rules are development decisions, not newly human-validated','raw_rows':len(d),'eligible_records':len(eligible),'training_unique_texts':int(eligible.training_representative.sum()),'counts':eligible.post_type.value_counts().to_dict(),'excluded':d.loc[~d.eligible,'exclusion_reason'].value_counts().to_dict(),'restored_x_timestamps':len(x),'snowflake_date_matches':len(x),'annotation_joins':pd.DataFrame(joins).matches.value_counts().to_dict(),'annotation_retained':int(pd.DataFrame(joins).eligible.fillna(False).sum()),'missing_submission_context_eligible':int(eligible.missing_submission_context.sum()),'missing_immediate_parent_eligible':int(eligible.missing_immediate_parent.sum()),'non_latin_flags':int(eligible.non_latin_flag.sum()),'input_hashes':{f.name:sha(f) for f in [OLD/'x_merged.parquet',OLD/'combined_reddit_posts.csv',OLD/'combined_reddit_comments.csv',OLD/'rde_raw_comments.csv']},'output_sha256':sha(P/'social_eligible.parquet'),'code_sha256':sha(__file__),'python':sys.version,'emoji':md.version('emoji'),'window':'source UTC capture Jan 1-Apr 30; analysis restricted to 16 complete Asia/Dubai weeks Jan 5-Apr 26','unresolved':'Independent target-level quality adjudication and semantic validation are human tasks; no generated judgments are represented as human.'}
    (HERE/'corpus_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
    (HERE/'property_lexicon.json').write_text(json.dumps(terms,indent=2),encoding='utf8')
    print(json.dumps(manifest,indent=2))

if __name__=='__main__':main()
