"""Refit the saved notebook's BERTopic configuration on the final clean corpus.

Run with the isolated environment documented in README.md. Raw inputs, model
artifacts and row-level outputs stay in ignored directories. No topic -1 recovery
or semantic-group/SMDI assignment is performed by this script.
"""
from pathlib import Path
import hashlib
import json
import os
import platform
import subprocess
import sys
import time

os.environ.setdefault('TOKENIZERS_PARALLELISM', 'false')
os.environ.setdefault('HF_HUB_DISABLE_XET', '1')
import numpy as np
import pandas as pd
import torch
from bertopic import BERTopic
from hdbscan import HDBSCAN
from sentence_transformers import SentenceTransformer
from umap import UMAP

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'outputs'
OUT.mkdir(exist_ok=True)
OLD = ROOT.parent / 'research_review_2026_09_06' / 'inputs'
MODEL = 'sentence-transformers/all-MiniLM-L6-v2'

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(2**20), b''):
            h.update(chunk)
    return h.hexdigest()

def bot_mask(d):
    author = d.username.fillna('').astype(str).str.strip().str.casefold().str.replace(r'^/?u/', '', regex=True)
    return d.platform.fillna('').astype(str).str.strip().str.casefold().eq('reddit') & author.eq('automoderator')

def main():
    start = time.time()
    torch.set_num_threads(4)
    source = ROOT / 'inputs/master_processed_analysis_clean.parquet'
    cols = ['id','platform','source_label','post_type','date','clean_text','domain_context_text',
            'parent_post_title','parent_post_text','username','url','subreddit','thread_id',
            'platform_interaction_value','platform_interaction_definition']
    d = pd.read_parquet(source, columns=cols).reset_index(drop=True)
    d.insert(0, 'source_row_zero_based', np.arange(len(d)))
    assert not d.duplicated(['platform','id']).any(), 'Duplicate ingestion IDs require resolution'
    bots = bot_mask(d)
    blank = d.clean_text.fillna('').astype(str).str.strip().eq('') & ~bots
    removed = d.loc[bots | blank].copy()
    removed['exclusion_reason'] = np.where(bots[bots | blank], 'known_reddit_automoderator', 'empty_clean_text')
    removed.to_parquet(OUT / 'excluded_records.parquet', index=False)
    n_source, n_bots, n_blank = len(d), int(bots.sum()), int(blank.sum())
    d = d.loc[~(bots | blank)].copy().reset_index(drop=True)
    docs = d.clean_text.astype(str).tolist()
    assert len(d) + len(removed) == n_source and not bot_mask(d).any()
    dates = pd.to_datetime(d.date, utc=True)
    assert dates.min() >= pd.Timestamp('2026-01-01', tz='UTC')
    assert dates.max() < pd.Timestamp('2026-05-01', tz='UTC')
    print(json.dumps({'source_rows': n_source, 'bots_removed': n_bots, 'blank_removed': n_blank, 'fit_rows': len(d)}), flush=True)
    old = pd.read_csv(OLD / 'smdi_posts.csv', usecols=['id','platform','clean_text','topic'], dtype={'id':str})
    cached = np.load(OLD / 'embeddings.npy', mmap_mode='r')
    assert cached.shape == (len(old),384)
    lookup = dict(zip(old.drop_duplicates('clean_text').clean_text, old.drop_duplicates('clean_text').index))
    positions = np.array([lookup.get(t, -1) for t in docs])
    encoder = SentenceTransformer(MODEL, device='cpu', cache_folder=str(ROOT / 'inputs/hf_cache'))
    check = np.random.default_rng(42).choice(np.flatnonzero(positions >= 0), size=32, replace=False)
    check_vectors = encoder.encode([docs[i] for i in check], normalize_embeddings=True, show_progress_bar=False)
    delta = float(np.max(np.abs(check_vectors - cached[positions[check]])))
    reuse = delta < 1e-4
    print(json.dumps({'embedding_cache_max_abs_difference_32':delta,'reuse_cache':reuse}), flush=True)
    embeddings = np.empty((len(d),384), dtype=np.float32)
    if reuse:
        embeddings[positions >= 0] = cached[positions[positions >= 0]]
        missing = np.flatnonzero(positions < 0)
    else:
        missing = np.arange(len(d))
    unique_missing = list(dict.fromkeys(docs[i] for i in missing))
    new = encoder.encode(unique_missing, batch_size=64, normalize_embeddings=True, show_progress_bar=True)
    new_lookup = {text:i for i,text in enumerate(unique_missing)}
    for i in missing:
        embeddings[i] = new[new_lookup[docs[i]]]
    assert np.isfinite(embeddings).all()
    np.testing.assert_allclose(np.linalg.norm(embeddings,axis=1),1,atol=1e-4)
    np.save(OUT / 'embeddings.npy', embeddings)
    d.to_parquet(OUT / 'fit_input.parquet', index=False)
    print('Embedding alignment verified; fitting UMAP and HDBSCAN.', flush=True)
    model = BERTopic(embedding_model=None,
        umap_model=UMAP(n_neighbors=30,n_components=5,min_dist=0.0,metric='cosine',random_state=42),
        hdbscan_model=HDBSCAN(min_cluster_size=20,min_samples=10,metric='euclidean',prediction_data=True,core_dist_n_jobs=4),
        calculate_probabilities=False, verbose=True)
    topics, probabilities = model.fit_transform(docs, embeddings)
    d['topic'] = topics
    d['assignment_strength'] = probabilities
    # Semantic groups require fresh content review; historical IDs cannot be reused.
    d['semantic_group'] = pd.Series(pd.NA, index=d.index, dtype='Int64')
    d.to_parquet(OUT / 'social_with_topics.parquet', index=False)
    info = model.get_topic_info()
    info.to_csv(OUT / 'topic_info.csv', index=False)
    np.save(OUT / 'umap_projection.npy', model.umap_model.embedding_)
    model.save(str(OUT / 'bertopic_model.pkl'), serialization='pickle', save_embedding_model=False)
    loaded = BERTopic.load(str(OUT / 'bertopic_model.pkl'))
    assert loaded.topics_ == topics
    assert int(info.Count.sum()) == len(d)
    assert d.loc[d.topic.eq(-1), 'semantic_group'].isna().all()
    manifest = {
        'input_drive_id':'1oNOz1KpfpLDTVyyoZs3veXYq-ZwDX11R',
        'input_drive_path':'Dubai_Real_Estate_Data/final_pipeline_outputs/master_processed_analysis_clean.parquet',
        'input_sha256':sha(source), 'source_rows':n_source, 'automoderator_removed':n_bots,
        'empty_text_removed':n_blank, 'fit_rows':len(d), 'non_outlier_rows':int(d.topic.ne(-1).sum()),
        'outlier_rows':int(d.topic.eq(-1).sum()), 'discovered_topics_excluding_minus1':int(d.loc[d.topic.ne(-1),'topic'].nunique()),
        'platform_counts':d.platform.value_counts().to_dict(),
        'date_min':str(dates.min()), 'date_max':str(dates.max()),
        'embedding_model':MODEL,'normalized_embeddings':True,
        'embedding_model_revision':getattr(encoder[0].auto_model.config, '_commit_hash', None),
        'cache_reused_rows':int((positions >= 0).sum()) if reuse else 0,
        'newly_encoded_unique_texts':len(unique_missing), 'cache_check_size':32,
        'cache_check_max_abs_difference':delta,
        'old_embeddings_sha256':sha(OLD / 'embeddings.npy'),
        'umap':{'n_neighbors':30,'n_components':5,'min_dist':0.0,'metric':'cosine','random_state':42},
        'hdbscan':{'min_cluster_size':20,'min_samples':10,'metric':'euclidean','prediction_data':True},
        'calculate_probabilities':False,
        'probability_note':'Assigned-cluster strengths only; all-topic membership matrix disabled. This does not change clustering.',
        'grouping_note':'No 25-group reduction, no outlier reassignment, no historical SMDI mappings applied.',
        'model_reload_verified':True,'elapsed_seconds':round(time.time()-start,1),
        'python':sys.version,'os':platform.platform(),
        'output_sha256':{name:sha(OUT / name) for name in ['embeddings.npy','fit_input.parquet','social_with_topics.parquet','topic_info.csv','bertopic_model.pkl','umap_projection.npy','excluded_records.parquet']},
    }
    (ROOT / 'refit_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    (ROOT / 'requirements-lock.txt').write_text(subprocess.check_output([sys.executable,'-m','pip','freeze'],text=True),encoding='utf-8')
    print(json.dumps(manifest,indent=2),flush=True)

if __name__ == '__main__':
    main()
