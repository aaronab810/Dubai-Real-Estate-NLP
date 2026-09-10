"""Conservative literal geographic mention feasibility, not geolocation."""
from pathlib import Path
import re,json
import pandas as pd
from build_corpus import sha
H=Path(__file__).resolve().parent;P=H/'private';O=H/'results'
def norm(t):return re.sub(r'\s+',' ',str(t).casefold()).strip()
def main():
    d=pd.read_parquet(P/'social_semantic.parquet');s=pd.read_parquet(P/'dld_sales_registrations.parquet')
    W=pd.date_range('2026-01-05',periods=16,freq='7D');s=s[s.week.isin(W)].copy();d=d[d.week.isin(W)].copy()
    s['area_key']=s.AREA_EN.map(norm)
    # Landmark/generic strings lack a sufficiently specific administrative meaning.
    excluded={'burj khalifa','horizon','business park','world islands','the world'}
    names=sorted(set(s.area_key)-excluded,key=len,reverse=True)
    names=[n for n in names if len(n)>=5]
    pat=re.compile(r'(?<!\w)(?:'+'|'.join(re.escape(n) for n in names)+r')(?!\w)',re.I)
    d['area_mentions']=d.clean_text.map(lambda t:sorted(set(norm(m.group()) for m in pat.finditer(t))))
    d['geographic_status']=d.area_mentions.map(lambda a:'none' if not a else 'single_literal' if len(a)==1 else 'multiple_literal')
    d[['record_key','area_mentions','geographic_status']].to_parquet(P/'geographic_candidates.parquet',index=False)
    rows=[]
    single=d[d.geographic_status.eq('single_literal')].copy();single['area_key']=single.area_mentions.str[0]
    for (platform,area),g in single.groupby(['platform','area_key']):
        market=s[s.area_key.eq(area)]
        rows.append(dict(platform=platform,area=area,records=len(g),weeks=g.week.nunique(),threads=g.thread_id.nunique() if platform=='reddit' else 0,authors=g.author_key.nunique(),sales=len(market),market_weeks=market.week.nunique(),max_week_records=int(g.week.value_counts().max())))
    table=pd.DataFrame(rows);table.to_csv(O/'spatial_feasibility.csv',index=False)
    d.groupby(['platform','geographic_status']).size().rename('records').reset_index().to_csv(O/'geographic_coverage.csv',index=False)
    sample=d[d.geographic_status.ne('none')].sample(min(100,d.geographic_status.ne('none').sum()),random_state=20260909)
    sample[['record_key','clean_text','area_mentions']].assign(human_valid_area='',human_notes='').to_csv(P/'geographic_review.csv',index=False)
    meta={'method':'case-insensitive whitespace-normalized exact AREA_EN phrase matching in target only, longest match first, no abbreviation/fuzzy aliases','excluded_ambiguous_literals':sorted(excluded),'distinct_source_area_strings':int(s.AREA_EN.nunique()),'normalized_area_keys':int(s.area_key.nunique()),'eligible_literals':len(names),'single_literal_records':len(single),'any_literal_records':int(d.geographic_status.ne('none').sum()),'single_area_platform_cells':len(table),'cells_all_16_weeks':int(table.weeks.eq(16).sum()),'unmapped_jvc_mentions':int(d.clean_text.str.contains(r'\bjvc\b',case=False).sum()),'geographic_status':'unvalidated mentions, not user/property geolocation; no community correlations estimated','source_sha256':sha(P/'social_semantic.parquet'),'code_sha256':sha(__file__)}
    (H/'spatial_manifest.json').write_text(json.dumps(meta,indent=2));print(json.dumps(meta,indent=2));print(table.sort_values('records',ascending=False).head(12).to_string(index=False))
if __name__=='__main__':main()
