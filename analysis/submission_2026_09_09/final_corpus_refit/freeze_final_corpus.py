"""Target-only repair of explicit offers found during semantic development.

No category or market outcome is read. Invitations to advise and explicit
property offer cards are excluded; ordinary buying questions remain eligible.
"""
from pathlib import Path
import re,json
import pandas as pd
from build_corpus import sha
H=Path(__file__).resolve().parent;P=H/'private';O=H/'results'

def reason(text):
    t=str(text)
    direct=re.search(r'\b(?:dm|pm|contact|message|whatsapp|reach out)\s+(?:me|us)\b',t,re.I)
    service=re.search(r'\b(?:consultation|viewing|options|details|available|availability|assist|help you|portfolio|show you|interested|looking|seeking)\b',t,re.I)
    if direct and service and not re.search(r'^(?:is (?:this|it)|still available|any\b)|\b(?:do not|don.t)\s+(?:dm|contact|message)',t,re.I) and re.search(r'\b(?:consultation|show you|help you|i have|we have|our|available|availability|portfolio)\b',t,re.I):return 'explicit_contact_invitation'
    if re.search(r'^\W*broker here\b',t,re.I) and re.search(r'\b(?:i have|we have|got other|we can discuss)\b',t,re.I):return 'broker_inventory_offer'
    offer=re.search(r'\b(?:for sale|for rent|available for|asking price|selling price|motivated seller|direct (?:from|with) (?:the )?owner)\b',t,re.I)
    specs=sum(bool(re.search(p,t,re.I)) for p in [
        r'\b\d+\s*(?:br|bhk|bed(?:room)?s?)\b',
        r'\b(?:aed|dhs?|dirhams?)\s*[\d,.]+|\b\d+(?:\.\d+)?\s*[mk]\b',
        r'\b(?:sq\.?\s*ft|sqft|square feet|bua|built.up area|plot area)\b',
        r'\b(?:fully furnished|semi.furnished|vacant on transfer|vaccant on transfer|private pool|payment plan|handover in)\b'])
    # An offer must be affirmative and near the opening, not a question seeking
    # housing or a discussion quoting someone else's advertised price.
    opening=t[:220]
    request=re.search(r'\b(?:looking for|looking to (?:buy|purchase)|planning to (?:buy|purchase)|seeking|wanted|want to buy|i bought|i purchased|i found|we bought|where (?:can|do)|anyone (?:have|know)|recommend|need advice|should i|is it|what do you|can anyone)\b',opening,re.I)
    header_offer=re.search(r'\b(?:for sale|for rent|available|asking price|selling price|motivated seller)\b',opening,re.I)
    if offer and header_offer and specs>=2 and not request and not re.match(r'^\W*any\b',t,re.I):return 'explicit_property_offer'
    sales_header=re.search(r'\b(?:urgent sale|distress sale|serious buyers only|direct clients preferred|lowest in (?:the )?market|high.yield investment opportunity)\b',t,re.I)
    if sales_header and specs>=2 and not request:return 'explicit_sales_marketing'
    phone_invite=re.search(r'\b(?:connect|contact|call|whatsapp|reach)\s+(?:(?:me|us)\s+)?(?:on|at)?\s*\+?\d[\d\s().-]{7,}\d',t,re.I)
    if phone_invite and specs>=2 and not request:return 'explicit_phone_offer'
    return ''

def main():
    d=pd.read_parquet(H.parent/'private/social_analysis_base.parquet')
    d['v3_exclusion']=d.clean_text.map(reason)
    excluded=d[d.v3_exclusion.ne('')];final=d[d.v3_exclusion.eq('')].copy()
    final['training_representative']=~final.text_family.duplicated()
    final['exact_family_size']=final.groupby(['platform','text_family']).record_key.transform('size')
    final['author_repeat']=final.duplicated(['platform','author_key','text_family'])
    final.to_parquet(P/'social_analysis_base.parquet',index=False)
    d[['record_key','v3_exclusion']].to_csv(P/'final_exclusion_membership.csv',index=False)
    excluded.groupby(['platform','v3_exclusion']).size().rename('records').reset_index().to_csv(O/'final_corpus_exclusions.csv',index=False)
    excluded[['record_key','clean_text','parent_text','context_text','v3_exclusion']].to_json(P/'final_exclusion_development.jsonl',orient='records',lines=True,force_ascii=False)
    meta={'version':'analysis-corpus-v4','input_records':len(d),'excluded':len(excluded),'records':len(final),
        'training_families':final.text_family.nunique(),'counts':final.post_type.value_counts().to_dict(),
        'common_counts':final[final.week.between('2026-01-05','2026-04-20')].platform.value_counts().to_dict(),
        'reasons':excluded.v3_exclusion.value_counts().to_dict(),'source_sha256':sha(H.parent/'private/social_analysis_base.parquet'),
        'output_sha256':sha(P/'social_analysis_base.parquet'),'code_sha256':sha(__file__),
        'decision':'Explicit target offers/contact invitations found in v2 and v3 refit inspection; rule-based development correction before new associations. No human accuracy claim.'}
    (H/'analysis_corpus_manifest.json').write_text(json.dumps(meta,indent=2));print(json.dumps(meta,indent=2))

if __name__=='__main__':main()
