"""Finite, fully reported candidate-SMDI associations; no predictive/causal test."""
from pathlib import Path
import json, warnings, argparse
import numpy as np
import pandas as pd
from scipy.stats import pearsonr,spearmanr,rankdata
from build_corpus import sha
H=Path(__file__).resolve().parent;P=H/'private';O=H/'results'
W=pd.date_range('2026-01-05',periods=16,freq='7D')
PAIRS=[('geopolitical','sales_registrations'),('geopolitical','sales_value_aed'),('valuation','sales_registrations'),('valuation','median_sale_amount_aed'),('development','offplan_count'),('development','ready_count')]
BOOT=4999

def corr(x,y,method='pearson'):
    x=np.asarray(x,dtype=float);y=np.asarray(y,dtype=float)
    mask=np.isfinite(x)&np.isfinite(y);x=x[mask];y=y[mask]
    if len(x)<4 or np.ptp(x)==0 or np.ptp(y)==0:return np.nan,np.nan
    f=pearsonr if method=='pearson' else spearmanr
    r,p=f(x,y);return float(r),float(p)

def bootstrap_indices(n,block,seed=20260909):
    rng=np.random.default_rng(seed+int(block)*100+n);out=np.empty((BOOT,n),int)
    out[:,0]=rng.integers(n,size=BOOT)
    for i in range(1,n):out[:,i]=np.where(rng.random(BOOT)<1/block,rng.integers(n,size=BOOT),(out[:,i-1]+1)%n)
    return out

def batch_corr(x,y,idx,method='pearson'):
    a=np.asarray(x,float)[idx];b=np.asarray(y,float)[idx]
    if method=='spearman':a=rankdata(a,axis=1);b=rankdata(b,axis=1)
    a=a-a.mean(axis=1,keepdims=True);b=b-b.mean(axis=1,keepdims=True)
    den=np.sqrt((a*a).sum(axis=1)*(b*b).sum(axis=1))
    with np.errstate(divide='ignore',invalid='ignore'):return (a*b).sum(axis=1)/den

def detrend(x):
    z=np.column_stack([np.ones(len(x)),np.arange(len(x))]);return x-z@np.linalg.lstsq(z,x,rcond=None)[0]

def aggregate(d,cols,weight=None):
    d=d.copy();d['_weight']=1. if weight is None else weight
    for c in cols:d[c+'_num']=d[c].astype(float)*d._weight
    nums=[c+'_num' for c in cols]
    w=d.groupby(['week','platform'])[['_weight']+nums].sum()
    w=w.rename(columns={'_weight':'denominator'})
    for c in cols:w[c]=w[c+'_num']/w.denominator.replace(0,np.nan)
    return w.reset_index()

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--development-only',action='store_true',help='Compatibility flag: all runs are exploratory and do not certify category validity')
    args=parser.parse_args()
    d=pd.read_parquet(P/'social_semantic.parquet')
    assert d.record_key.is_unique
    cols=[c for c in d if c.startswith('cat_')]
    base=aggregate(d,cols);base.to_csv(O/'smdi_weekly.csv',index=False)
    market=pd.read_csv(O/'dld_weekly.csv',parse_dates=['week']).set_index('week').reindex(W)
    assert market.sales_registrations.notna().all()
    near=pd.read_parquet(P/'near_families.parquet');d=d.merge(near,on='record_key',validate='one_to_one')
    specs={'primary':base}
    for name,keys in [('exact_family',['week','platform','text_family']),('near_family',['week','platform','near_family']),('author',['week','platform','author_key'])]:
        weight=1/d.groupby(keys).record_key.transform('size');specs[name]=aggregate(d,cols,weight)
    # X posts are their own units; never treat empty X thread IDs as one thread.
    threadkey=d.thread_id.where(d.platform.eq('reddit'),d.record_key)
    weight=1/d.assign(_thread=threadkey).groupby(['week','platform','_thread']).record_key.transform('size')
    specs['thread']=aggregate(d,cols,weight)
    specs['exclude_promotion_flags']=aggregate(d[~d.promotion_ambiguous_flag],cols)
    specs['exclude_short_context']=aggregate(d[~d.short_context_flag],cols)
    specs['exclude_administrative_recaps']=aggregate(d[~d.administrative_recap_flag],cols)
    specs['exclude_equity_discourse']=aggregate(d[~d.equity_discourse_flag],cols)
    for name,frame in pd.read_csv(O/'semantic_model_weekly.csv',parse_dates=['week']).groupby('specification'):
        if name!='primary':
            specs['semantic_'+name]=frame.rename(columns={c[4:]:c for c in cols})
    utc=d.copy();utc['week']=utc.timestamp_utc.dt.tz_localize(None).dt.to_period('W-SUN').dt.start_time
    specs['utc_calendar']=aggregate(utc,cols)
    if all('cue_'+c[4:] in d for c in cols):
        cue=d.copy()
        for c in cols:cue[c]=cue['cue_'+c[4:]]
        specs['document_cue_baseline']=aggregate(cue,cols)
    for name,series in specs.items():series.assign(specification=name).to_csv(O/('smdi_weekly_'+name+'.csv'),index=False)
    rows=[];sensitivity=[]
    for platform in ['x','reddit']:
        s=base[base.platform.eq(platform)].set_index('week').reindex(W)
        assert s.denominator.gt(0).all()
        for category,outcome in PAIRS:
            xx=s['cat_'+category].to_numpy(float);yy=market[outcome].to_numpy(float)
            for lag in [0,1,2]:
                x=xx[:len(xx)-lag] if lag else xx;y=yy[lag:] if lag else yy
                for method in ['pearson','spearman']:
                    r,p=corr(x,y,method);loo=[corr(np.delete(x,j),np.delete(y,j),method)[0] for j in range(len(x))]
                    shifts=[corr(x,np.roll(y,j),method)[0] for j in range(len(x))]
                    row=dict(platform=platform,category=category,outcome=outcome,lag=lag,method=method,n=len(x),r=r,p_iid_reference=p,circular_shift_reference_p=float(np.mean(np.abs(shifts)>=abs(r)-1e-12)) if np.isfinite(r) else np.nan,first_difference_r=corr(np.diff(x),np.diff(y),method)[0],linear_detrended_r=corr(detrend(x),detrend(y),method)[0],leave_one_out_min=float(np.nanmin(loo)),leave_one_out_max=float(np.nanmax(loo)),x_lag1=corr(x[:-1],x[1:])[0],y_lag1=corr(y[:-1],y[1:])[0])
                    for block in [2,3,4]:
                        boot=batch_corr(x,y,bootstrap_indices(len(x),block),method);valid=boot[np.isfinite(boot)]
                        low,high=np.quantile(valid,[.025,.975]) if len(valid) else [np.nan,np.nan]
                        row.update({f'bootstrap_b{block}_low':low,f'bootstrap_b{block}_high':high,f'bootstrap_b{block}_valid':len(valid)})
                    rows.append(row)
                    for name,frame in specs.items():
                        ss=frame[frame.platform.eq(platform)].set_index('week').reindex(W)['cat_'+category].to_numpy(float)
                        xs=ss[:-lag] if lag else ss
                        sensitivity.append(dict(platform=platform,category=category,outcome=outcome,lag=lag,method=method,specification=name,r=corr(xs,y,method)[0]))
                    sensitivity.append(dict(platform=platform,category=category,outcome=outcome,lag=lag,method=method,specification='absolute_category_volume',r=corr((s['cat_'+category+'_num'].to_numpy(float))[:len(x)],y,method)[0]))
            # Nonoverlapping fortnightly aggregates: sum counts then divide.
            fortnight=s[['denominator','cat_'+category+'_num']].groupby(np.arange(16)//2).sum()
            fx=(fortnight['cat_'+category+'_num']/fortnight.denominator).to_numpy()
            # Medians cannot be summed: use raw sale records for this outcome.
            sales=pd.read_parquet(P/'dld_sales_registrations.parquet');sales=sales[sales.week.isin(W)].copy();sales['fortnight']=sales.week.map(dict(zip(W,np.arange(16)//2)))
            fy=sales.groupby('fortnight').TRANS_VALUE.median().to_numpy() if outcome=='median_sale_amount_aed' else market[outcome].groupby(np.arange(16)//2).sum().to_numpy()
            for method in ['pearson','spearman']:sensitivity.append(dict(platform=platform,category=category,outcome=outcome,lag=0,method=method,specification='fortnightly_n8',r=corr(fx,fy,method)[0]))
            # Value skew and composition checks are tied to the relevant pair.
            alt='winsor99_sales_value_aed' if outcome=='sales_value_aed' else 'flat_median_aed_per_transacted_sqm' if outcome=='median_sale_amount_aed' else None
            if alt:
                for method in ['pearson','spearman']:sensitivity.append(dict(platform=platform,category=category,outcome=outcome,lag=0,method=method,specification=alt,r=corr(xx,market[alt].to_numpy(float),method)[0]))
    table=pd.DataFrame(rows);valid=table.p_iid_reference.notna();pv=table.loc[valid,'p_iid_reference'];order=np.argsort(pv.values);ordered=pv.values[order];q=np.minimum.accumulate((ordered*len(pv)/np.arange(1,len(pv)+1))[::-1])[::-1].clip(0,1);mapped=np.empty(len(pv));mapped[order]=q;table.loc[valid,'q_bh_iid_reference']=mapped
    table.to_csv(O/'associations_all.csv',index=False);pd.DataFrame(sensitivity).to_csv(O/'associations_sensitivity.csv',index=False)
    # Direct dependent-correlation contrasts: one shared index matrix per calendar.
    contrasts=[]
    for category,outcome in PAIRS:
        arrays=[base[base.platform.eq(p)].set_index('week').reindex(W)['cat_'+category].to_numpy(float) for p in ['x','reddit']]
        y=market[outcome].to_numpy(float)
        for method in ['pearson','spearman']:
            idx=bootstrap_indices(16,3);boot=batch_corr(arrays[0],y,idx,method)-batch_corr(arrays[1],y,idx,method)
            lo,hi=np.nanquantile(boot,[.025,.975]);contrasts.append(dict(contrast='X minus Reddit',category=category,outcome=outcome,method=method,difference=corr(arrays[0],y,method)[0]-corr(arrays[1],y,method)[0],low=lo,high=hi))
    for platform in ['x','reddit']:
        x=base[base.platform.eq(platform)].set_index('week').reindex(W).cat_development.to_numpy(float)
        y=market.offplan_count.to_numpy(float);z=market.ready_count.to_numpy(float)
        for method in ['pearson','spearman']:
            idx=bootstrap_indices(16,3);boot=batch_corr(x,y,idx,method)-batch_corr(x,z,idx,method);lo,hi=np.nanquantile(boot,[.025,.975]);contrasts.append(dict(contrast='off-plan minus ready: '+platform,category='development',outcome='registration_count',method=method,difference=corr(x,y,method)[0]-corr(x,z,method)[0],low=lo,high=hi))
    pd.DataFrame(contrasts).to_csv(O/'association_contrasts.csv',index=False)
    meta={'estimates':len(table),'pair_platform_lag_estimates':len(table)//2,'calendar_weeks':16,'resamples':BOOT,'block_lengths':[2,3,4],'minimum_circular_shift_p':float(table.circular_shift_reference_p.min()),'iid_bh_below_05':int(table.q_bh_iid_reference.lt(.05).sum()),'first_difference_sign_changes':int((np.sign(table.r)!=np.sign(table.first_difference_r)).sum()),'source_sha256':sha(P/'social_semantic.parquet'),'code_sha256':sha(__file__),'semantic_status':'candidate assignments, independent human category validation unavailable','uncertainty_note':'IID/BH references are not valid serial dependence corrections. Bootstrap assumes local stationarity; 14-16 observations cannot calibrate long-run uncertainty. No causal or predictive claim.'}
    meta['analysis_role']='exploratory candidate-SMDI associations; independent category validation pending; no independently validated measurement or confirmatory inference claim'
    (H/'association_manifest.json').write_text(json.dumps(meta,indent=2));print(json.dumps(meta,indent=2))
if __name__=='__main__':
    warnings.filterwarnings('ignore',message='All-NaN slice encountered')
    main()
