"""Additional domain checks and source-derived assets for the revised paper.

Run after build_domain_graphs.py. No topic refit or new semantic labels.
"""
from pathlib import Path
import json, sys, hashlib, zipfile, importlib.metadata
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from scipy.stats import spearmanr
from build_domain_graphs import HERE, OUT, WEEKS, PRIMARY, SOCIAL, DLD, DOMAINS, sha, corr
from analyse_associations import bootstrap_indices, batch_corr, detrend

PAPER = HERE.parents[2] / 'paper'

def tex(s):
    return str(s).replace('&',r'\&').replace('%',r'\%').replace('_',r'\_')

def aggregate(s, domain, weight=None):
    x = s.copy()
    x['_w'] = 1. if weight is None else weight
    x['_n'] = x.topic.isin(domain['topics']).astype(float)*x._w
    g = x.groupby(['platform','week'])[['_w','_n']].sum()
    return (g._n/g._w).rename('share')

def main():
    # Archive the obsolete five-category paper once, before source edits.
    archive = HERE/'archive_five_category_paper.zip'
    if not archive.exists():
        with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
            for p in PAPER.rglob('*'):
                if p.is_file() and p.suffix in ['.tex','.bib','.pdf','.cls','.bst']:
                    z.write(p,p.relative_to(PAPER))
    s = pd.read_parquet(SOCIAL)
    s['week'] = s.date_local.dt.tz_localize(None).dt.to_period('W-SUN').dt.start_time
    domains = json.loads(DOMAINS.read_text())['domains']
    code = json.loads((HERE/'supplied_smdi_workbook.json').read_text(encoding='utf8'))
    mapping = pd.DataFrame(code['SMDI Mapping'])
    summary = pd.DataFrame(code['SMDI Summary'])
    training = pd.read_parquet(HERE/'private/training_with_topics.parquet')
    actual = training[training.topic.ge(0)].groupby('topic').size()
    assert mapping['Topic ID'].is_unique and set(mapping['Topic ID']) == set(range(367))
    assert mapping['SMDI ID'].nunique() == 43
    assert all(actual.loc[r['Topic ID']] == r['Topic Size'] for _,r in mapping.iterrows())
    assert set().union(*(set(d['topics']) for d in domains)) == set(range(367))
    coverage = []
    memberships = np.zeros(len(s),int)
    for domain in domains:
        mask = s.topic.isin(domain['topics'])
        memberships += mask.to_numpy()
        row = {'domain_id':domain['id'],'domain':domain['name'],'topics':len(domain['topics'])}
        for platform in ['x','reddit']:
            frame = s[s.platform.eq(platform)]
            row[platform+'_count'] = int(frame.topic.isin(domain['topics']).sum())
            row[platform+'_percent'] = 100*row[platform+'_count']/len(frame)
        coverage.append(row)
    cov = pd.DataFrame(coverage)
    cov.to_csv(OUT/'domain_coverage_all_corpus.csv',index=False)
    mapping.to_csv(OUT/'topic_to_fine_category.csv',index=False)
    pd.DataFrame([{'domain_id':d['id'],'domain':d['name'],'topic':t} for d in domains for t in d['topics']]).to_csv(OUT/'topic_to_domain.csv',index=False)
    summary.to_csv(OUT/'fine_category_codebook.csv',index=False)
    qc = mapping['QC Flag'].value_counts().to_dict()
    assert np.count_nonzero(memberships) == 34647
    complete = s[s.week.isin(WEEKS)].copy()
    weekly = pd.read_csv(OUT/'domain_weekly.csv',parse_dates=['week'])
    market = pd.read_csv(OUT/'dld_weekly.csv',parse_dates=['week']).set_index('week').reindex(WEEKS)
    sales = pd.read_parquet(DLD)
    sales = sales[sales.week.isin(WEEKS)].copy()
    flags = pd.read_parquet(HERE/'private/social_semantic.parquet',columns=['record_key','administrative_recap_flag','equity_discourse_flag'])
    assert set(flags.record_key) == set(s.record_key)
    s = s.merge(flags,on='record_key',validate='one_to_one')
    near = pd.read_parquet(HERE/'private/near_families.parquet')
    s = s.merge(near,on='record_key',validate='one_to_one')
    assert s.near_family.notna().all()
    # Unknown threads get their own record key; never pool all missing threads.
    s['_thread'] = s.thread_id.fillna('').astype(str)
    s['_thread'] = s._thread.where(s.platform.eq('reddit') & s._thread.ne(''),s.record_key)
    weights = {}
    for name,key in [('thread','_thread'),('author','author_key'),('near_family','near_family')]:
        unit = s[key].fillna(s.record_key)
        weights[name] = 1/s.assign(_unit=unit).groupby(['platform','week','_unit']).record_key.transform('size')
    samples = {'exclude_promotion_flags':s[~s.promotion_ambiguous_flag],
               'exclude_short_context':s[~s.short_context_flag],
               'exclude_equity_discourse':s[~s.equity_discourse_flag],
               'exclude_administrative_recaps':s[~s.administrative_recap_flag]}
    utc=s.copy();utc['week']=utc.timestamp_utc.dt.tz_localize(None).dt.to_period('W-SUN').dt.start_time
    samples['utc_calendar']=utc
    extra=[]; series=[]; intervals=[]; contrasts=[]
    base = pd.read_csv(OUT/'primary_associations_and_sensitivities.csv')
    for did,outcome in PRIMARY:
        domain=next(d for d in domains if d['id']==did)
        specs={k:aggregate(s,domain,w) for k,w in weights.items()}
        specs.update({k:aggregate(v,domain) for k,v in samples.items()})
        # Narrower existing workbook category is a measurement sensitivity,
        # not a relabeling or alternative chosen by its market coefficient.
        narrow_ids={1:['SMDI-03'],3:['SMDI-27'],9:['SMDI-14']}[did]
        narrow={'topics':mapping.loc[mapping['SMDI ID'].isin(narrow_ids),'Topic ID'].tolist()}
        specs['narrow_workbook_category']=aggregate(s,narrow)
        for platform in ['x','reddit']:
            b=weekly[(weekly.domain_id==did)&(weekly.platform==platform)].set_index('week').reindex(WEEKS)
            x=b.share_all.to_numpy();y=market[outcome].to_numpy()
            for spec,v in specs.items():
                xx=v.loc[platform].reindex(WEEKS).to_numpy()
                assert np.isfinite(xx).all()
                for week,value in zip(WEEKS,xx):series.append(dict(domain_id=did,platform=platform,specification=spec,week=week,share=value))
                extra.append(dict(domain_id=did,platform=platform,outcome=outcome,specification=spec,n=16,r=corr(xx,y),rho=float(spearmanr(xx,y).statistic)))
            extra.append(dict(domain_id=did,platform=platform,outcome=outcome,specification='linear_detrend',n=16,r=corr(detrend(x),detrend(y)),rho=float(spearmanr(detrend(x),detrend(y)).statistic)))
            # Recompute fortnight medians from individual registrations.
            f=sales.copy();f['fortnight']=f.week.map(dict(zip(WEEKS,np.arange(16)//2)))
            fx=b[['count','eligible_records']].groupby(np.arange(16)//2).sum();fx=fx['count']/fx.eligible_records
            fy=f.groupby('fortnight').TRANS_VALUE.median().to_numpy() if outcome=='median_sale_amount_aed' else market[outcome].groupby(np.arange(16)//2).sum().to_numpy()
            extra.append(dict(domain_id=did,platform=platform,outcome=outcome,specification='fortnight',n=8,r=corr(fx,fy),rho=float(spearmanr(fx,fy).statistic)))
            if outcome=='median_sale_amount_aed':
                flats=sales[(sales.PROP_SB_TYPE_EN=='Flat') & sales.PROCEDURE_AREA.gt(0)].copy()
                flats['_ratio']=flats.TRANS_VALUE/flats.PROCEDURE_AREA
                for label,yy in [('mean_sale_amount',market.mean_sale_amount_aed),('flat_median_per_transacted_sqm',flats.groupby('week')._ratio.median().reindex(WEEKS))]:
                    extra.append(dict(domain_id=did,platform=platform,outcome=outcome,specification=label,n=16,r=corr(x,yy),rho=float(spearmanr(x,yy).statistic)))
            for lag in [0,1,2]:
                xx=x[:16-lag];yy=y[lag:]
                for block in [2,3,4]:
                    for method in ['pearson','spearman']:
                        vals=batch_corr(xx,yy,bootstrap_indices(len(xx),block),method)
                        vals=vals[np.isfinite(vals)];lo,hi=np.quantile(vals,[.025,.975])
                        intervals.append(dict(domain_id=did,platform=platform,outcome=outcome,lag=lag,block=block,method=method,n=len(xx),low=lo,high=hi,valid=len(vals)))
        xx=weekly[(weekly.domain_id==did)&(weekly.platform=='x')].set_index('week').reindex(WEEKS).share_all.to_numpy()
        rr=weekly[(weekly.domain_id==did)&(weekly.platform=='reddit')].set_index('week').reindex(WEEKS).share_all.to_numpy()
        yy=market[outcome].to_numpy();idx=bootstrap_indices(16,3)
        boot=batch_corr(xx,yy,idx)-batch_corr(rr,yy,idx);lo,hi=np.nanquantile(boot,[.025,.975])
        contrasts.append(dict(domain_id=did,outcome=outcome,contrast='X minus Reddit',difference=corr(xx,yy)-corr(rr,yy),low=lo,high=hi))
    extra=pd.DataFrame(extra);extra.to_csv(OUT/'additional_sensitivities.csv',index=False)
    pd.DataFrame(series).drop_duplicates().to_csv(OUT/'additional_weekly_series.csv',index=False)
    pd.DataFrame(intervals).to_csv(OUT/'bootstrap_intervals.csv',index=False)
    pd.DataFrame(contrasts).to_csv(OUT/'platform_contrasts.csv',index=False)
    # Share of domain records contributed by the largest Reddit thread per week.
    concentration=[]
    for domain in domains:
        r=s[s.week.isin(WEEKS)&s.platform.eq('reddit')&s.topic.isin(domain['topics'])]
        for week,g in r.groupby('week'):
            counts=g._thread.value_counts()
            concentration.append(dict(domain_id=domain['id'],week=week,records=len(g),threads=len(counts),largest_thread_share=counts.iloc[0]/len(g)))
    pd.DataFrame(concentration).to_csv(OUT/'reddit_thread_concentration.csv',index=False)
    tables=PAPER/'tables'
    short=['Market and pricing','Investment and finance','Developers and projects','Locations and characteristics','Rental and tenancy','Transactions and services','Regulation and ownership','Management and living','Political, geopolitical and social','Communication and platform']
    lines=[]
    for r,name in zip(coverage,short):
        lines.append(f"{r['domain_id']}. {name} & {r['topics']} & {r['x_count']:,} ({r['x_percent']:.1f}) & {r['reddit_count']:,} ({r['reddit_percent']:.1f})"+r' \\')
    (tables/'domain_coverage.tex').write_text('\n'.join(lines)+'\n')
    ints=pd.DataFrame(intervals)
    lines=[]
    for _,r in base[(base.specification=='share_all')&(base.forward_registration_lag_weeks==0)].iterrows():
        ci=ints[(ints.domain_id==r.domain_id)&(ints.platform==r.platform)&(ints.outcome==r.outcome)&(ints.lag==0)&(ints.block==3)&(ints.method=='pearson')].iloc[0]
        outcome={'median_sale_amount_aed':'Median amount','offplan_count':'Off-plan count','ready_count':'Ready count','sales_registrations':'Sales count'}[r.outcome]
        lines.append(f"{'X' if r.platform=='x' else 'Reddit'} & {int(r.domain_id)} & {outcome} & {r.pearson_r:.2f} & {r.spearman_rho:.2f} & {r.difference_r:.2f} & [{ci.low:.2f}, {ci.high:.2f}]"+r' \\')
    (tables/'domain_correlations.tex').write_text('\n'.join(lines)+'\n')
    plt.rcParams.update({'font.size':9,'axes.spines.top':False,'axes.spines.right':False})
    fig,axes=plt.subplots(2,2,figsize=(7,5.6),sharex=True,layout='constrained')
    for ax,did,title in zip(axes.flat,[1,3,9],['Market and pricing (D1)','Developers and projects (D3)','Political, geopolitical and social (D9)']):
        for platform,color in [('x','#3264a8'),('reddit','#c66429')]:
            f=weekly[(weekly.domain_id==did)&(weekly.platform==platform)]
            ax.plot(f.week,100*f.share_all,label='X' if platform=='x' else 'Reddit',color=color)
        ax.set_title(title,fontsize=9);ax.set_ylabel('Eligible records (%)');ax.legend(fontsize=8);ax.set_ylim(bottom=0)
    ax=axes[1,1]
    for c,label,color in [('offplan_count','Off-plan','#148174'),('ready_count','Ready','#9165a9')]:
        ax.plot(WEEKS,market[c],label=label,color=color)
    ax.set_title('DLD sales registrations');ax.set_ylabel('Registrations');ax.legend(fontsize=8);ax.set_ylim(bottom=0)
    for ax in axes.flat:
        ax.grid(axis='y',alpha=.2);ax.xaxis.set_major_locator(mdates.MonthLocator());ax.xaxis.set_major_formatter(mdates.DateFormatter('%b'))
    fig.savefig(PAPER/'figures/domain_weekly.pdf');fig.savefig(OUT/'paper_domain_weekly.png',dpi=180);plt.close(fig)
    # Full category definitions are separate from the conference narrative.
    lines=[r'\documentclass[10pt]{article}',r'\usepackage[T1]{fontenc}',r'\usepackage[a4paper,margin=22mm]{geometry}',r'\usepackage{longtable,booktabs,array}',r'\begin{document}',r'\section*{Candidate SMDI codebook and topic mappings}',
        'The supplied workbook defines 43 finer categories. Each BERTopic topic has one finer-category assignment. The separately supplied ten-domain mapping overlaps at topic level and is not a strict nesting of whole finer categories. All assignments await independent semantic validation. Counts below refer to unique training texts, not activity records.',
        r'\section*{Assignment and review rules}',
        'A record inherits the category and domain memberships of its frozen Pass-1 topic. Topic $-1$ abstains. A domain counts a record once even when multiple thematic rationales apply. Target text is primary evidence; parent context resolves reference without transferring a parent-only theme. A mixed-topic flag is a review warning, not evidence that all members express every theme. Independent reviewers should distinguish category evidence, absent evidence, ambiguous meaning and insufficient context, allowing multiple domains where justified. Disagreement must be measured before adjudication. This specification does not contain completed independent annotation results.',
        r'\section*{Finer categories}']
    for _,r in summary.iterrows():
        lines += [r'\subsection*{'+tex(r['SMDI ID']+': '+r['SMDI Label'])+'}',tex(r['SMDI Description']),r'\par Topics: '+tex(r['Topic IDs'])+'.',r'\par Unique texts: '+f"{r['Posts']:,}"+'.']
    lines += [r'\section*{Broader domains}']
    for d in domains:lines += [r'\subsection*{'+str(d['id'])+'. '+tex(d['name'])+'}', 'Topics: '+', '.join(map(str,d['topics']))+'.']
    lines += [r'\end{document}']
    (PAPER/'semantic_codebook.tex').write_text('\n\n'.join(lines),encoding='utf8')
    meta={'categories':43,'topics':367,'unique_assigned_texts':32561,'activity_assigned':int(np.count_nonzero(memberships)),
        'activity_overlap_domains':int((memberships>1).sum()),'activity_assignment_percent':100*np.count_nonzero(memberships)/len(s),
        'qc_flags':qc,'missing_domain_topics':[],'bootstrap_draws':4999,'bootstrap_seed_rule':'20260909 + 100*block + n',
        'packages':{k:importlib.metadata.version(k) for k in ['numpy','pandas','scipy','matplotlib']},
        'inputs':{str(p):sha(p) for p in [SOCIAL,DLD,DOMAINS,HERE/'supplied_smdi_workbook.json',HERE/'topic_manifest.json',Path(__file__),HERE/'analyse_associations.py',HERE/'private/social_semantic.parquet',HERE/'private/near_families.parquet']}}
    (OUT/'paper_analysis_manifest.json').write_text(json.dumps(meta,indent=2))
    print(json.dumps({k:v for k,v in meta.items() if k not in ['inputs','packages']},indent=2))
    print(extra.to_string(index=False))

if __name__=='__main__':main()
