"""Verify the reported domain coefficients using shareable weekly data only."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr
H=Path(__file__).resolve().parent;O=H/'results/domain_graphs'

def main():
    w=pd.read_csv(O/'domain_weekly.csv',parse_dates=['week'])
    d=pd.read_csv(O/'dld_weekly.csv',parse_dates=['week']).set_index('week').sort_index()
    rows=pd.read_csv(O/'primary_associations_and_sensitivities.csv')
    assert len(w)==320 and len(d)==16
    assert np.allclose(w.share_all,w['count']/w.eligible_records)
    assert np.allclose(w.share_assigned,w['count']/w.topic_assigned_records)
    assert np.allclose(w.share_all,w.share_assigned*w.topic_coverage)
    assert (d.offplan_count+d.ready_count).equals(d.sales_registrations)
    assert d.sales_registrations.sum()==59229
    assert w[w.domain_id==1].eligible_records.sum()==68083
    for _,r in rows.iterrows():
        x=w[(w.domain_id==r.domain_id)&(w.platform==r.platform)].set_index('week').loc[d.index,r.specification].to_numpy()
        lag=int(r.forward_registration_lag_weeks);x=x[:len(x)-lag];y=d[r.outcome].to_numpy()[lag:]
        assert len(x)==r.n and len(x)-1==r.difference_n
        assert np.isclose(pearsonr(x,y).statistic,r.pearson_r,atol=1e-12)
        assert np.isclose(spearmanr(x,y).statistic,r.spearman_rho,atol=1e-12)
        assert np.isclose(pearsonr(np.diff(x),np.diff(y)).statistic,r.difference_r,atol=1e-12)
        loo=[pearsonr(np.delete(x,i),np.delete(y,i)).statistic for i in range(len(x))]
        assert np.isclose(min(loo),r.leave_one_out_min,atol=1e-12)
        assert np.isclose(max(loo),r.leave_one_out_max,atol=1e-12)
    primary=pd.read_csv(O/'primary_contemporaneous.csv')
    pd.testing.assert_frame_equal(primary.reset_index(drop=True),rows[(rows.specification=='share_all')&(rows.forward_registration_lag_weeks==0)].reset_index(drop=True))
    extra=pd.read_csv(O/'additional_sensitivities.csv')
    series=pd.read_csv(O/'additional_weekly_series.csv',parse_dates=['week'])
    checked=0
    for _,r in extra.iterrows():
        g=series[(series.domain_id==r.domain_id)&(series.platform==r.platform)&(series.specification==r.specification)].set_index('week')
        if g.empty:continue
        x=g.loc[d.index,'share'].to_numpy();y=d[r.outcome].to_numpy()
        if np.ptp(x)==0:
            assert pd.isna(r.r) and pd.isna(r.rho)
        else:
            assert np.isclose(pearsonr(x,y).statistic,r.r,atol=1e-12)
            assert np.isclose(spearmanr(x,y).statistic,r.rho,atol=1e-12)
        checked+=1
    result={'status':'passed','primary_specification_rows_verified':len(rows),'additional_weighted_or_filtered_rows_verified':checked,'weeks':16,'semantic_validation':'not performed by this numerical check'}
    (O/'aggregate_verification.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
