"""Focused comparisons requested by the authors, with explicit outcome scope."""
import json
import textwrap
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.backends.backend_pdf import PdfPages
from build_domain_graphs import HERE, OUT, WEEKS

PAIRS = [
 (1,'median_sale_amount_aed','Median sale amount','Primary: registered transaction size, not a price index'),
 (2,'median_sale_amount_aed','Median sale amount','Context only: does not measure investment returns or financing conditions'),
 (3,'offplan_count','Off-plan sales registrations','Primary: discussion of developers versus off-plan registration activity'),
 (3,'ready_count','Ready sales registrations','Primary segment comparison: developer discussion versus ready sales'),
 (4,'sales_registrations','Sales registrations','Context only: aggregate registrations do not validate location-specific discourse'),
 (5,'sales_registrations','Sales registrations','Context only: no rental-registration series is available'),
 (6,'sales_registrations','Sales registrations','Exploratory: transaction-related discussion versus sales registration activity'),
 (7,'sales_registrations','Sales registrations','Context only: sales counts do not measure regulatory changes or disputes'),
 (8,'sales_registrations','Sales registrations','Context only: sales counts do not measure living conditions or management quality'),
 (9,'sales_registrations','Sales registrations','Primary: broad political/social attention versus sales activity, not pure geopolitical risk'),
 (10,'sales_registrations','Sales registrations','Context only: no corresponding administrative measure of platform behaviour')]

def z(v): return (v-v.mean())/v.std(ddof=1)

def plot(ax,x,y,platform,label):
    ax.plot(WEEKS,z(x),color='#2764a0',linewidth=2,marker='o',markersize=3,label=f'{platform}: group share')
    ax.plot(WEEKS,z(y),color='#9b4d16',linewidth=2,linestyle='--',marker='s',markersize=3,label=f'DLD: {label.lower()}')
    ax.axhline(0,color='.7',linewidth=.7)
    ax.set_title(platform,fontsize=11)
    ax.set_ylabel('Standard deviations from own mean')
    ax.xaxis.set_major_locator(mdates.MonthLocator());ax.xaxis.set_major_formatter(mdates.DateFormatter('%b'))
    ax.grid(axis='y',alpha=.2);ax.legend(fontsize=8,loc='best')

def main():
    dest=OUT/'comparisons';dest.mkdir(exist_ok=True)
    domains=json.loads((HERE/'user_domains_10.json').read_text())['domains']
    weekly=pd.read_csv(OUT/'domain_weekly.csv',parse_dates=['week'])
    market=pd.read_csv(OUT/'dld_weekly.csv',parse_dates=['week']).set_index('week').reindex(WEEKS)
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    with PdfPages(dest/'domain_market_comparisons.pdf') as pdf:
        for did,outcome,label,scope in PAIRS:
            name=next(d['name'] for d in domains if d['id']==did)
            fig,axes=plt.subplots(1,2,figsize=(11,4.4),sharex=True,sharey=True,layout='constrained')
            fig.suptitle('\n'.join(textwrap.wrap(name+' vs '+label,88)),fontsize=14)
            for ax,p in zip(axes,['x','reddit']):
                g=weekly[(weekly.domain_id==did)&(weekly.platform==p)].set_index('week').reindex(WEEKS)
                plot(ax,g.share_all,market[outcome],'X' if p=='x' else 'Reddit',label)
            fig.supxlabel(scope+'\n16 Monday–Sunday weeks, January–April 2026. Standardisation compares movement, not units or causal effects.',fontsize=9)
            pdf.savefig(fig);fig.savefig(dest/f'domain_{did:02d}_{outcome}.png',dpi=180)
            plt.close(fig)
    pd.DataFrame(PAIRS,columns=['domain_id','dld_column','label','scope']).to_csv(dest/'pairing_rationale.csv',index=False)
    mainpairs=[PAIRS[0],PAIRS[2],PAIRS[3],PAIRS[9]]
    fig,axes=plt.subplots(4,2,figsize=(4.8,6.8),sharex=True,layout='constrained')
    for row,(did,outcome,label,scope) in enumerate(mainpairs):
        for col,p in enumerate(['x','reddit']):
            g=weekly[(weekly.domain_id==did)&(weekly.platform==p)].set_index('week').reindex(WEEKS)
            ax=axes[row,col];plot(ax,g.share_all,market[outcome],'X' if p=='x' else 'Reddit',label)
            short={'median_sale_amount_aed':'median amount','offplan_count':'off-plan sales','ready_count':'ready sales','sales_registrations':'all sales'}[outcome]
            ax.set_title(f"{'X' if p=='x' else 'Reddit'}: G{did} / {short}",fontsize=8)
            ax.set_ylabel('z-score',fontsize=8)
            ax.tick_params(labelsize=8)
            ax.get_legend().remove()
    fig.savefig(HERE.parents[2]/'paper/figures/domain_comparisons.pdf')
    fig.savefig(dest/'paper_comparisons.png',dpi=180);plt.close(fig)
    print('Created 11 direct comparison figures covering all ten domains; six domains explicitly contextual.')

if __name__=='__main__':main()
