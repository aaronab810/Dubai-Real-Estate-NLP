"""Rebuild the supplied ten-domain comparisons from frozen activity records.

Preserves the exact supplied domain lists. No semantic reassignment or model fit.
Outputs are candidate measurements pending independent semantic validation.
The revised user domain lists cover all topics. The workbook has 43 categories.
"""
from pathlib import Path
import hashlib
import json
import textwrap
import zipfile
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.backends.backend_pdf import PdfPages
from scipy.stats import spearmanr

HERE = Path(__file__).resolve().parent
OUT = HERE / 'results' / 'domain_graphs'
DOMAINS = HERE / 'user_domains_10.json'
SOCIAL = HERE / 'private' / 'social_with_topics.parquet'
DLD = HERE.parent / 'private' / 'dld_sales_registrations.parquet'
WEEKS = pd.date_range('2026-01-05', '2026-04-20', freq='W-MON')
# Defined before examining these results. Descriptive exploratory associations,
# not a preregistration or confirmatory test family.
PRIMARY = [(1, 'median_sale_amount_aed'), (3, 'offplan_count'),
           (3, 'ready_count'), (9, 'sales_registrations')]

def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()

def corr(x, y):
    x, y = np.asarray(x, float), np.asarray(y, float)
    if np.std(x) == 0 or np.std(y) == 0:
        return np.nan
    return float(np.corrcoef(x, y)[0, 1])

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    domains = json.loads(DOMAINS.read_text(encoding='utf8'))['domains']
    s = pd.read_parquet(SOCIAL)
    assert s.record_key.is_unique and len(s) == 71239
    s['week'] = pd.to_datetime(s.date_local).dt.to_period('W-SUN').dt.start_time
    assert (s.topic.ge(0).sum(), s.topic.eq(-1).sum()) == (34647, 36592)
    union = set().union(*(set(d['topics']) for d in domains))
    assert union <= set(range(367))
    missing = sorted(set(range(367)) - union)
    missing_rows = s[s.topic.isin(missing)]
    missing_rows.groupby(['topic', 'platform']).size().rename('activity_records').reset_index().to_csv(OUT/'unmapped_topic_counts.csv', index=False)
    s = s[s.week.isin(WEEKS)].copy()
    assert len(s) == 68083
    dld = pd.read_parquet(DLD)
    assert dld.registration_key.is_unique
    dld['week'] = pd.to_datetime(dld.INSTANCE_DATE).dt.to_period('W-SUN').dt.start_time
    dld = dld[dld.week.isin(WEEKS)].copy()
    assert len(dld) == 59229
    assert set(dld.IS_OFFPLAN_EN) == {'Off-Plan', 'Ready'}
    market = dld.groupby('week').agg(
        sales_registrations=('registration_key', 'size'),
        sales_value_aed=('TRANS_VALUE', 'sum'),
        median_sale_amount_aed=('TRANS_VALUE', 'median'),
        mean_sale_amount_aed=('TRANS_VALUE', 'mean')).reindex(WEEKS)
    for label, value in [('offplan', 'Off-Plan'), ('ready', 'Ready')]:
        g = dld[dld.IS_OFFPLAN_EN.eq(value)].groupby('week')
        market[label+'_count'] = g.size().reindex(WEEKS, fill_value=0)
        market[label+'_median_amount_aed'] = g.TRANS_VALUE.median().reindex(WEEKS)
    assert (market.offplan_count + market.ready_count).equals(market.sales_registrations)
    market.index.name = 'week'
    market.to_csv(OUT/'dld_weekly.csv')
    rows = []
    for domain in domains:
        ids = set(domain['topics'])
        for (platform, week), g in s.groupby(['platform', 'week']):
            assigned = int(g.topic.ge(0).sum())
            count = int(g.topic.isin(ids).sum())
            unique = g.drop_duplicates('training_key')
            rows.append(dict(domain_id=domain['id'], domain=domain['name'],
                platform=platform, week=week, count=count,
                eligible_records=len(g), topic_assigned_records=assigned,
                share_all=count/len(g), share_assigned=count/assigned,
                topic_coverage=assigned/len(g),
                share_unique=unique.topic.isin(ids).mean()))
    weekly = pd.DataFrame(rows).sort_values(['domain_id', 'platform', 'week'])
    assert len(weekly) == 320
    assert np.allclose(weekly.share_all, weekly.share_assigned*weekly.topic_coverage)
    weekly.to_csv(OUT/'domain_weekly.csv', index=False)
    results = []
    for domain_id, outcome in PRIMARY:
        for platform in ['x', 'reddit']:
            g = weekly[(weekly.domain_id == domain_id) & (weekly.platform == platform)].set_index('week').reindex(WEEKS)
            for specification in ['share_all', 'share_assigned', 'share_unique', 'count']:
                for lag in [0, 1, 2]:
                    x = g[specification].to_numpy()[:len(WEEKS)-lag]
                    y = market[outcome].to_numpy()[lag:]
                    loo = [corr(np.delete(x, i), np.delete(y, i)) for i in range(len(x))]
                    results.append(dict(domain_id=domain_id, platform=platform,
                        outcome=outcome, specification=specification,
                        forward_registration_lag_weeks=lag, n=len(x),
                        pearson_r=corr(x,y), spearman_rho=float(spearmanr(x,y).statistic),
                        difference_n=len(x)-1, difference_r=corr(np.diff(x),np.diff(y)),
                        leave_one_out_min=min(loo), leave_one_out_max=max(loo)))
    stats = pd.DataFrame(results)
    stats.to_csv(OUT/'primary_associations_and_sensitivities.csv', index=False)
    primary = stats[(stats.specification == 'share_all') & (stats.forward_registration_lag_weeks == 0)]
    primary.to_csv(OUT/'primary_contemporaneous.csv', index=False)
    plt.rcParams.update({'font.size': 10, 'axes.spines.top': False,
                         'axes.spines.right': False, 'savefig.dpi': 180})
    colors = {'x': '#3264a8', 'reddit': '#c66429'}
    interpretations = []
    with PdfPages(OUT/'ten_domain_graphs.pdf') as pdf:
        for domain in domains:
            g = weekly[weekly.domain_id == domain['id']]
            fig, ax = plt.subplots(3, 2, figsize=(12, 10), sharex=True, constrained_layout=True)
            fig.suptitle('\n'.join(textwrap.wrap(domain['name'], 70)) + '\nCandidate topic-inherited assignments', fontsize=15)
            for platform, color in colors.items():
                p = g[g.platform == platform]
                name = 'X' if platform == 'x' else 'Reddit'
                ax[0,0].plot(p.week, 100*p.share_all, color=color, marker='.', label=name)
                ax[0,1].plot(p.week, p['count'], color=color, marker='.', label=name)
                ax[1,0].plot(p.week, 100*p.share_assigned, color=color, marker='.', label=name)
                ax[1,1].plot(p.week, 100*p.topic_coverage, color=color, marker='.', label=name)
            ax[0,0].set_title('Domain share of all eligible records'); ax[0,0].set_ylabel('% of platform records')
            ax[0,1].set_title('Domain activity'); ax[0,1].set_ylabel('Records (posts and comments)')
            ax[1,0].set_title('Domain share of topic-assigned records'); ax[1,0].set_ylabel('% of assigned platform records')
            ax[1,1].set_title('Topic-assignment coverage'); ax[1,1].set_ylabel('% of platform records')
            ax[2,0].plot(WEEKS, market.sales_registrations, color='#303947', label='All sales')
            ax[2,0].plot(WEEKS, market.offplan_count, color='#148174', label='Off-plan sales')
            ax[2,0].plot(WEEKS, market.ready_count, color='#9165a9', label='Ready sales')
            ax[2,0].set_title('DLD sales activity'); ax[2,0].set_ylabel('Unique registrations')
            ax[2,1].plot(WEEKS, market.median_sale_amount_aed/1e6, color='#303947', label='Median')
            ax[2,1].plot(WEEKS, market.mean_sale_amount_aed/1e6, color='#9165a9', label='Mean')
            ax[2,1].set_title('DLD amount per sales registration'); ax[2,1].set_ylabel('Million AED (composition-sensitive)')
            for a in ax.flat:
                a.grid(axis='y', alpha=.2); a.legend(fontsize=8, loc='best')
                a.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=mdates.MO, interval=3))
                a.xaxis.set_major_formatter(mdates.DateFormatter('%d %b'))
                a.set_ylim(bottom=0)
            fig.supxlabel('Monday–Sunday weeks, 5 January–26 April 2026. Aligned panels show co-movement, not causal effects.', fontsize=10)
            pdf.savefig(fig)
            fig.savefig(OUT/f'domain_{domain["id"]:02d}.png')
            plt.close(fig)
            desc = []
            for platform in ['x','reddit']:
                p = g[g.platform == platform]
                peak = p.loc[p.share_all.idxmax()]
                desc.append(f'{platform.upper() if platform == "x" else "Reddit"}: {p["count"].sum():,} domain records; weekly share {100*p.share_all.min():.1f}–{100*p.share_all.max():.1f}%, peaking in the week starting {peak.week:%d %B}.')
            interpretations.append('### '+domain['name']+'\n\n'+' '.join(desc))
    note = '''# Reading the domain graphs

These figures use the revised ten domain lists supplied by the authors, covering all 367 non-noise topics. The workbook separately contains 43 finer categories, numbered SMDI-01 through SMDI-43. The domain lists are an overlapping topic-to-domain mapping; they do not necessarily preserve whole finer categories as a strict hierarchy. All assignments remain candidates pending independent semantic validation.

Read each page from top to bottom. The top-left panel measures the share of all eligible platform records assigned to the domain. The top-right shows its activity count. The middle-left conditions on receiving any BERTopic topic; the middle-right shows how much of the platform corpus receives a topic. A change in counts can reflect platform volume; a change in the assigned-only share can also reflect changing coverage. The two bottom panels show contemporaneous DLD sales registrations and registration amounts, with matched calendar weeks.

Domains can overlap, so their percentages must not be summed to 100%. Each record is counted once within a domain. Noise records remain in the all-eligible denominator but have unknown semantic membership. This measures identified discussion, not the true prevalence of all category-relevant discourse.

DLD amounts are not a constant-quality price index. Sales do not measure rents, mortgages or political attitudes. The domain pages for rental, legal, living and communication themes provide descriptive context rather than direct administrative validation of those constructs. The political/geopolitical/social domain also includes reactions and humour, so it cannot be interpreted as a pure geopolitical-risk index.

The companion association table contains eight conceptually selected contemporaneous comparisons: pricing with median sale amount, developer discussion with off-plan and ready counts, and the broad political/social domain with sales counts, each separately for X and Reddit. All are exploratory. Sensitivities include Spearman correlation, first differences, leave-one-week-out, unique-text-within-platform-week weighting, both denominators, raw counts and one/two-week forward registration lags. Lagging pairs social week t with DLD week t+k (16, 15 and 14 pairs). No significance or forecasting claim is inferred from these short series.

## Observed domain activity

'''
    (OUT/'graph_explanations.md').write_text(note+'\n\n'.join(interpretations), encoding='utf8')
    manifest = dict(status='revised exact supplied domain mapping; independent semantic validation pending',
        common_social_records=len(s), common_sales_registrations=len(dld), weeks=16,
        missing_domain_topics=missing, omitted_domain_activity_all_corpus=len(missing_rows),
        primary_pairs=PRIMARY, independent_semantic_validation=False,
        input_sha256={str(p):sha(p) for p in [DOMAINS,SOCIAL,DLD,Path(__file__)]},
        output_sha256={p.name:sha(p) for p in sorted(OUT.iterdir()) if p.suffix in ['.csv','.png','.pdf','.md']})
    (OUT/'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf8')
    with zipfile.ZipFile(OUT.parent/'domain_graphs_provisional.zip', 'w', zipfile.ZIP_DEFLATED) as z:
        for p in sorted(OUT.iterdir()):
            if p.is_file(): z.write(p, p.name)
    print(json.dumps({k:v for k,v in manifest.items() if k not in ['input_sha256','output_sha256']},indent=2))
    print(primary.to_string(index=False))

if __name__ == '__main__':
    main()
