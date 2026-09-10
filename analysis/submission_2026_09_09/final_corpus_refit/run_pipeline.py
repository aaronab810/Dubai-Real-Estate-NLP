"""Minimal ordered reproduction entry point within the existing repository."""
from pathlib import Path
import argparse,subprocess,sys,shutil,json,hashlib
H=Path(__file__).resolve().parent

def sha(path):
    digest=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(2**20),b''): digest.update(block)
    return digest.hexdigest()

def check_current_inputs():
    """Require the exact frozen inputs used by the current results."""
    manifest=json.loads((H/'frozen_input_hashes.json').read_text())
    problems=[]
    for name,expected in manifest['inputs'].items():
        path=H/name
        if not path.is_file():
            problems.append('Missing '+name);continue
        if sha(path)!=expected: problems.append('Checksum mismatch '+name)
    if problems:
        raise SystemExit('Frozen-input check failed:\n'+'\n'.join(problems)+
                         '\nUse --verify for aggregate-only reproduction. No analysis was started.')
    print('Frozen inputs present; recorded input checksums match.',flush=True)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fit',action='store_true',help='Refit all six models; otherwise use the completed frozen models')
    parser.add_argument('--legacy-five-category',action='store_true',help='Explicitly reproduce the superseded five-category development workflow')
    parser.add_argument('--verify',action='store_true',help='Verify current aggregate results without private records or a model fit')
    parser.add_argument('--check-inputs',action='store_true',help='Check restricted frozen inputs without running the analysis')
    args=parser.parse_args()
    if (args.verify or args.check_inputs) and (args.fit or args.legacy_five_category):
        parser.error('Current verification options cannot be combined with legacy/refit options.')
    if args.verify:
        subprocess.run([sys.executable,'-X','utf8',str(H/'verify_domain_aggregates.py')],check=True)
        return
    if args.check_inputs:
        check_current_inputs();return
    if not args.legacy_five_category:
        if args.fit:
            parser.error('The current semantic mappings are tied to frozen Pass-1 topics. A new fit requires separate mapping review; it cannot automatically reuse these topic IDs.')
        check_current_inputs()
        for name in ['build_domain_graphs.py','domain_paper_analysis.py','make_domain_comparisons.py']:
            print('Running current domain analysis:',name,flush=True)
            subprocess.run([sys.executable,'-X','utf8',str(H/name)],check=True,cwd=H.parents[2])
        return
    if not args.fit:
        meta=json.loads((H/'topic_manifest.json').read_text())
        assert meta['corpus_sha256']==sha(H/'private/social_analysis_base.parquet'),'Complete the final-corpus fit first'
        assert meta['code_sha256']==sha(H/'fit_topics.py'),'The fitted and current topic scripts differ'
    assert sha(H.parent/'private/social_analysis_base.parquet')=='62a98235cf89a03803a61b3f7d12f0f31c5e73cd39d48aa21cddcff4194a833f'
    for sub in ['private','results','models']:(H/sub).mkdir(exist_ok=True)
    for n in ['near_families.parquet','annotation_mapping.csv','dld_sales_registrations.parquet']:
        src=H.parent/'private'/n;dst=H/'private'/n
        if not dst.exists():shutil.copy2(src,dst)
        assert sha(src)==sha(dst)
    for src in list((H.parent/'results').glob('dld*'))+[H.parent/'results/annotation_reliability.csv']:
        dst=H/'results'/src.name
        if not dst.exists():shutil.copy2(src,dst)
        assert sha(src)==sha(dst)
    steps=(['freeze_final_corpus.py','fit_topics.py'] if args.fit else [])+['assign_semantics.py','analyse_associations.py','spatial_feasibility.py','final_diagnostics.py','strengthen_diagnostics.py','check_analysis.py','prepare_validation.py','make_paper_assets.py']
    for name in steps:
        print('Running',name,flush=True)
        subprocess.run([sys.executable,'-X','utf8',str(H/name)],check=True,cwd=H.parents[2])

if __name__=='__main__':main()
