"""Outcome-blind BERTopic discovery and bounded structural comparisons."""
import os
os.environ.setdefault('TOKENIZERS_PARALLELISM','false')
os.environ.setdefault('HF_HUB_OFFLINE','1')
from pathlib import Path
import json, time, sys, importlib.metadata as md
import numpy as np
import pandas as pd
import torch
from sentence_transformers import SentenceTransformer
from bertopic import BERTopic
from sklearn.feature_extraction.text import CountVectorizer
from hdbscan import HDBSCAN
from umap import UMAP
from scipy.spatial.distance import pdist, squareform
from scipy.cluster.hierarchy import linkage, fcluster
from sklearn.metrics import silhouette_score, adjusted_rand_score
from build_corpus import sha

HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[2]
P=HERE/'private';M=HERE/'models';OUT=HERE/'results'
M.mkdir(exist_ok=True)
MODEL_REV='1110a243fdf4706b3f48f1d95db1a4f5529b4d41'
def main():
    started=time.time();torch.set_num_threads(4)
    data=pd.read_parquet(P/'social_analysis_base.parquet')
    train=data.drop_duplicates('text_family').copy().reset_index(drop=True)
    texts=train.clean_text.tolist()
    encoder=SentenceTransformer(str(ROOT/'analysis/refit_2026_09_07/inputs/hf_cache/models--sentence-transformers--all-MiniLM-L6-v2/snapshots'/MODEL_REV),device='cpu')
    old=pd.read_parquet(ROOT/'analysis/refit_2026_09_07/outputs/fit_input.parquet')
    oldemb=np.load(ROOT/'analysis/refit_2026_09_07/outputs/embeddings.npy',mmap_mode='r')
    lookup=dict(zip(old.clean_text,range(len(old))))
    embpath=M/'embeddings.npy'
    if embpath.exists() and (M/'training_order.txt').exists() and (M/'training_order.txt').read_text()== '\n'.join(train.record_key):
        E=np.load(embpath);missing=[]
    else:
        positions=np.array([lookup.get(t,-1) for t in texts]);missing=np.flatnonzero(positions<0)
        E=np.empty((len(train),384),dtype=np.float32);E[positions>=0]=oldemb[positions[positions>=0]]
        check=np.random.default_rng(42).choice(np.flatnonzero(positions>=0),min(32,(positions>=0).sum()),replace=False)
        np.testing.assert_allclose(E[check],encoder.encode([texts[i] for i in check],normalize_embeddings=True),atol=1e-5)
        print(json.dumps({'training_texts':len(train),'new_embeddings':len(missing)}),flush=True)
        E[missing]=encoder.encode([texts[i] for i in missing],batch_size=64,normalize_embeddings=True,show_progress_bar=True)
        np.save(embpath,E);(M/'training_order.txt').write_text('\n'.join(train.record_key),encoding='utf8')
    assert E.shape==(len(train),384) and np.isfinite(E).all()
    lengths=[len(encoder.tokenizer.encode(t,truncation=False)) for t in texts]
    train['encoder_tokens']=lengths
    configs=[(42,20,10,'primary'),(42,20,5,'density_20_5'),(42,40,10,'density_40_10'),(42,40,5,'density_40_5'),(17,20,10,'seed_17'),(73,20,10,'seed_73')]
    comparison=[];base=None
    for seed,size,samples,name in configs:
        t0=time.time();print('Fitting '+name,flush=True)
        um=UMAP(n_neighbors=30,n_components=5,min_dist=0,metric='cosine',random_state=seed)
        # A fit on each bounded specification is saved, not merely proposed.
        model=BERTopic(embedding_model=None,umap_model=um,hdbscan_model=HDBSCAN(min_cluster_size=size,min_samples=samples,metric='euclidean',prediction_data=True,core_dist_n_jobs=4),vectorizer_model=CountVectorizer(stop_words='english',ngram_range=(1,2),min_df=2),calculate_probabilities=False,verbose=False)
        topics,strength=model.fit_transform(texts,E)
        topics=np.asarray(topics);np.save(M/(name+'_topics.npy'),topics)
        info=model.get_topic_info();info.to_csv(P/(name+'_topic_info.csv'),index=False)
        assigned=topics>=0
        centroids=np.stack([E[topics==i].mean(axis=0) for i in sorted(set(topics)-{-1})]);centroids/=np.linalg.norm(centroids,axis=1,keepdims=True)
        cos=np.sum(E[assigned]*centroids[topics[assigned]],axis=1)
        words=[w for i in sorted(set(topics)-{-1}) for w,_ in model.get_topic(i)[:10]]
        row=dict(specification=name,seed=seed,min_cluster_size=size,min_samples=samples,training_records=len(train),topics=len(set(topics)-{-1}),assigned=int(assigned.sum()),outliers=int((~assigned).sum()),assigned_fraction=float(assigned.mean()),median_within_topic_cosine=float(np.median(cos)),topic_word_diversity=len(set(words))/len(words),elapsed_seconds=time.time()-t0)
        if base is not None:row['adjusted_rand_including_noise']=adjusted_rand_score(base,topics)
        comparison.append(row)
        if name=='primary':
            base=topics.copy();model.save(str(M/'bertopic_primary.pkl'),serialization='pickle',save_embedding_model=False)
            np.save(M/'umap_primary.npy',model.umap_model.embedding_);np.save(M/'topic_centroids.npy',centroids)
            train['topic']=topics;train['assignment_strength']=strength
            train.to_parquet(P/'training_with_topics.parquet',index=False)
            lut=train.set_index('training_key').topic
            data['topic']=data.training_key.map(lut).astype(int)
            data['assignment_strength']=data.training_key.map(train.set_index('training_key').assignment_strength)
            data.to_parquet(P/'social_with_topics.parquet',index=False)
            # Five deterministic random documents plus three representative docs
            # per topic, with target and immediate/submission context for review.
            packet=[]
            for topic,g in train[train.topic>=0].groupby('topic'):
                rep=set(model.representative_docs_.get(topic,[]))
                chosen=pd.concat([g[g.clean_text.isin(rep)].head(3),g.sample(min(5,len(g)),random_state=20260909)]).drop_duplicates('record_key')
                for _,rr in chosen.iterrows():packet.append({'topic':int(topic),'topic_size':len(g),'keywords':'; '.join(w for w,_ in model.get_topic(topic)[:10]),'record_key':rr.record_key,'representative':rr.clean_text in rep,'target':rr.clean_text,'parent':rr.parent_text,'submission':rr.context_text,'platform':rr.platform})
            pd.DataFrame(packet).to_json(P/'topic_review_packet.jsonl',orient='records',lines=True,force_ascii=False)
            # Compare true embedding centroids, never UMAP display coordinates.
            dist=squareform(pdist(centroids,'cosine'));np.fill_diagonal(dist,0)
            reductions=[]
            sizes=train[train.topic>=0].topic.value_counts().sort_index().values
            for method in ['single','average','complete','ward']:
                Z=linkage(centroids,method='ward',metric='euclidean') if method=='ward' else linkage(squareform(dist,checks=False),method=method)
                for criterion,cut in [('maxclust',25),('distance',.35),('distance',.45),('distance',.55)]:
                    if method=='ward' and criterion=='distance':continue
                    labels=fcluster(Z,cut,criterion=criterion)
                    groups=[np.flatnonzero(labels==k) for k in np.unique(labels)]
                    reductions.append({'method':method,'criterion':criterion,'cut':cut,'groups':len(groups),'largest_training_group':int(max(sizes[g].sum() for g in groups)),'largest_topic_group':max(len(g) for g in groups),'max_cosine_diameter':float(max(dist[np.ix_(g,g)].max() for g in groups)),'silhouette_cosine':float(silhouette_score(dist,labels,metric='precomputed')) if 1<len(groups)<len(centroids) else None})
                if method=='complete':np.save(M/'complete_linkage.npy',Z)
            pd.DataFrame(reductions).to_csv(OUT/'hierarchical_comparison.csv',index=False)
            # Native automatic reduction is a structural comparator, not an SMDI.
            model.reduce_topics(texts,nr_topics='auto')
            native=model.get_topic_info();native.to_csv(P/'native_auto_topic_info.csv',index=False)
            (OUT/'native_reduction.json').write_text(json.dumps({'topics_excluding_noise':int(native.Topic.ge(0).sum()),'noise_training_records':int(native.loc[native.Topic.eq(-1),'Count'].sum()),'largest_assigned_group':int(native.loc[native.Topic.ge(0),'Count'].max())},indent=2))
        pd.DataFrame(comparison).to_csv(OUT/'topic_specifications.csv',index=False)
        print(json.dumps(row),flush=True)
    meta={'corpus_sha256':sha(P/'social_analysis_base.parquet'),'primary_specification':'Final-corpus refit: settings inherited from prior run; no association-based selection','embedding':'all-MiniLM-L6-v2','revision':MODEL_REV,'training_unique_texts':len(train),'activity_records':len(data),'max_seq_length':encoder.max_seq_length,'training_over_limit':sum(n>encoder.max_seq_length for n in lengths),'token_length_quantiles':{str(q):float(np.quantile(lengths,q)) for q in [.5,.9,.95,.99,1]},'vectorizer':{'stop_words':'english','ngram_range':[1,2],'min_df':2},'selection_note':'Primary maintains the pre-existing density settings; alternatives quantify structural sensitivity without optimizing market association or claiming automated coherence is construct validity.','model_sha256':sha(M/'bertopic_primary.pkl'),'code_sha256':sha(__file__),'packages':{k:md.version(k) for k in ['bertopic','sentence-transformers','umap-learn','hdbscan','scikit-learn','numpy','pandas']},'elapsed_seconds':time.time()-started}
    (HERE/'topic_manifest.json').write_text(json.dumps(meta,indent=2),encoding='utf8')
    print(json.dumps(meta,indent=2),flush=True)
if __name__=='__main__':main()
