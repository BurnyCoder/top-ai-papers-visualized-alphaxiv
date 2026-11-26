"""Original-space nearest neighbors, independent UMAP fits and preregistered census-level metrics."""
from __future__ import annotations

import io
import hashlib
import os
import warnings
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from contextlib import ExitStack
import numpy as np
from scipy.spatial.distance import cdist
from scipy.spatial import cKDTree
from scipy.stats import t
from sklearn.cluster import HDBSCAN
from sklearn.decomposition import PCA
from sklearn.metrics import adjusted_rand_score
from threadpoolctl import threadpool_limits

from .io import LOG, read_json, save_bytes, save_json

SEEDS = tuple(range(42,52))


def save_arrays(path, **arrays):
    """Use a single atomic archive so resumed runs cannot mix partial coordinates and IDs."""
    buffer = io.BytesIO()
    np.savez_compressed(buffer, **arrays)
    save_bytes(path, buffer.getvalue())


def load_arrays(path):
    with np.load(path, allow_pickle=False) as archive:
        return {key:archive[key] for key in archive.files}


def lowest(values,k):
    """Partial selection with the exact same row-ID tie break as a stable full sort."""
    split=np.argpartition(values,k-1,axis=1)[:,:k]
    chosen=np.take_along_axis(values,split,axis=1)
    last=chosen.max(axis=1,keepdims=True)
    order=np.lexsort((split,chosen),axis=1)
    result=np.take_along_axis(split,order,axis=1)
    boundary=(values==last).sum(axis=1)>(chosen==last).sum(axis=1)
    for row in np.flatnonzero(boundary):result[row]=np.argsort(values[row],kind="stable")[:k]
    return result


def neighborhood(vectors, count=30):
    """Stable sort by original row (group ID) on exact cosine ties; self is explicit column zero."""
    unit = vectors / np.linalg.norm(vectors,axis=1,keepdims=True)
    # Row blocks bound temporary memory as the eligible census grows.
    ids=np.empty((len(unit),count),dtype=np.int32)
    values=np.zeros(ids.shape,dtype=np.float32)
    ids[:,0]=np.arange(len(unit))
    for start in range(0,len(unit),256):
        stop=min(start+256,len(unit))
        dist=np.clip(1-unit[start:stop] @ unit.T,0,2)
        dist[np.arange(stop-start),np.arange(start,stop)]=np.inf
        other=lowest(dist,count-1)
        ids[start:stop,1:]=other
        values[start:stop,1:]=np.take_along_axis(dist,other,axis=1)
    return ids, values


def exact_graph(vectors,count,progress=None):
    """Rank every eligible group in float64; append explicit self and cast only selected distances."""
    def normalized(rows):
        x=np.array(rows,dtype=np.float64,copy=True)
        x/=np.sqrt(np.einsum("ij,ij->i",x,x))[:,None]
        return x
    n=len(vectors);gpu=None
    if n>15000:
        # Optional FP64 cuBLAS multiplication; the independent CPU audit checks every rank.
        try:
            import cupy
            if cupy.cuda.runtime.memGetInfo()[0]>vectors.size*8+256*1024**2:
                # Normalize host tiles identically to CPU retrieval, then retain only the device copy.
                gpu=cupy.empty(vectors.shape,dtype=cupy.float64)
                for start in range(0,n,1024):
                    stop=min(start+1024,n)
                    gpu[start:stop].set(normalized(vectors[start:stop]))
                cupy.asnumpy(gpu[:1] @ gpu[:1].T)
                LOG.info("Using local CUDA FP64 for exhaustive original-space similarities")
        except (ImportError,OSError,RuntimeError,MemoryError) as error:
            gpu=None
            LOG.info("Using CPU BLAS for exhaustive original-space similarities (%s)",type(error).__name__)
    unit=normalized(vectors) if gpu is None else None
    ids=np.empty((n,count),dtype=np.int32)
    distances=np.zeros(ids.shape,dtype=np.float32)
    ids[:,0]=np.arange(n)
    block=128 if n>60000 else 256
    for start in range(0,n,block):
        stop=min(start+block,n)
        similarity=(unit[start:stop] @ unit.T if gpu is None else cupy.asnumpy(gpu[start:stop] @ gpu.T))
        np.negative(similarity,out=similarity)
        similarity[np.arange(stop-start),np.arange(start,stop)]=np.inf
        ranked=lowest(similarity,count-1)
        ids[start:stop,1:]=ranked
        distances[start:stop,1:]=np.clip(1+np.take_along_axis(similarity,ranked,axis=1),0,2)
        if progress and (start%(block*32)==0 or stop==n):
            progress("Exact cosine neighbors",stop,n,device="CUDA" if gpu is not None else "CPU")
    return ids,distances


def original_neighbors(vectors):
    return exact_graph(vectors,11)[0][:,1:]


def projection(vectors, indices, distances, dim, seed):
    """The precomputed exact graph is shared, but each dimension and seed gets its own optimizer."""
    from umap import UMAP
    reducer = UMAP(n_components=dim,n_neighbors=indices.shape[1],metric="cosine",min_dist=.1 if dim==2 else 0.,
                   random_state=seed,n_jobs=1,force_approximation_algorithm=True,compatibility_layout=True,
                   precomputed_knn=(indices.copy(), distances.copy(), None))
    with warnings.catch_warnings():
        # This atlas embeds a closed corpus and never calls UMAP.transform() for future points.
        warnings.filterwarnings("ignore",message=".*precomputed_knn.*NNDescent.*")
        return reducer.fit_transform(vectors)


def membership(coords):
    model = HDBSCAN(min_cluster_size=20,min_samples=5,cluster_selection_method="eom",metric="euclidean",n_jobs=1,copy=False)
    return model.fit_predict(coords), model.probabilities_


def run_seed(folder, vectors, indices, distances, seed):
    path = folder / "work" / f"seed-{seed}.npz"
    if path.exists():
        return load_arrays(path)
    xy = projection(vectors,indices,distances,2,seed)
    z = projection(vectors,indices,distances,10,seed)
    labels, strength = membership(z)
    save_arrays(path, xy=xy, z10=z, labels=labels, strength=strength)
    return dict(xy=xy,z10=z,labels=labels,strength=strength)


def prepare_seed(folder,seed):
    """Workers share the read-only vector file and commit only their own seed checkpoint."""
    vectors=np.load(folder/"embeddings.npy",mmap_mode="r",allow_pickle=False)
    with np.load(folder/"geometry.npz",allow_pickle=False) as archive,threadpool_limits(limits=4):
        run_seed(folder,vectors,archive["knn"],archive["knn_dist"],seed)


def geometry(folder, vectors, progress):
    path = folder / "geometry.npz"
    if path.exists():
        main=load_arrays(path)
        if "neighbors" not in main:
            with threadpool_limits(limits=4):
                main["neighbors"]=original_neighbors(vectors)
            save_arrays(path,**main)
        return main
    if len(vectors)<31:
        raise ValueError("The preregistered configuration requires at least 31 qualifying papers")
    progress("Original neighbors and PCA",0,2)
    with threadpool_limits(limits=4):
        if read_json(folder/"manifest.json")["threshold_exclusive"]==10:
            checkpoint=folder/"work"/"exact-graph.npz"
            if not checkpoint.exists():
                indices,distances=exact_graph(vectors,30,progress)
                save_arrays(checkpoint,indices=indices,distances=distances)
            else:
                cached=load_arrays(checkpoint);indices,distances=cached["indices"],cached["distances"]
            exact=indices[:,1:11]
        else:
            indices, distances = neighborhood(vectors)
            exact = original_neighbors(vectors)
        pca = PCA(n_components=10,svd_solver="full").fit_transform(vectors)
        pca_labels, _ = membership(pca)
        progress("Primary UMAP and HDBSCAN",1,2,seed=42)
        main = run_seed(folder,vectors,indices,distances,42)
    main.update(knn=indices,knn_dist=distances,neighbors=exact,pca=pca,pca_labels=pca_labels,
                paper_sha256=np.array(read_json(folder/"manifest.json")["content_sha256"]),
                vector_sha256=np.array(read_json(folder/"embedding-info.json")["vectors_sha256"]))
    save_arrays(path,**main)
    return main


def recall_at_ten(xy, neighbors):
    """Exact Euclidean tree queries with stable original row order at a distance tie."""
    points=np.asarray(xy,dtype=np.float64)
    distances,indices=cKDTree(points).query(points,k=min(12,len(points)),eps=0)
    distances[indices==np.arange(len(points))[:,None]]=np.inf
    order=np.lexsort((indices,distances),axis=1)
    near=np.take_along_axis(indices,order[:,:10],axis=1)
    sorted_dist=np.take_along_axis(distances,order,axis=1)
    for row in np.flatnonzero(sorted_dist[:,9]==sorted_dist[:,10]):
        exact=cdist(points[row:row+1],points,"sqeuclidean")[0];exact[row]=np.inf
        near[row]=np.argsort(exact,kind="stable")[:10]
    return float(np.any(near[:,:,None]==neighbors[:,None,:10],axis=2).mean())


def tag_overlap(labels, masks):
    """Exact pooled within-cluster pair agreement with multi-category cross-listings counted once."""
    matching = pairs = 0
    for group in np.unique(labels[labels>=0]):
        counts = Counter(int(m) for m in masks[labels==group] if m)
        values = list(counts.items())
        n = sum(counts.values())
        pairs += n*(n-1)//2
        for i,(tag,number) in enumerate(values):
            matching += number*(number-1)//2
            matching += sum(number*other_count for other_tag,other_count in values[i+1:] if tag & other_tag)
    return dict(shared=matching,pairs=pairs,fraction=matching/pairs if pairs else None)


def cluster_metrics(labels, base, masks, seed):
    assigned = labels>=0
    shared = assigned & (base>=0)
    rng = np.random.default_rng(seed)
    shuffled = masks.copy()
    tagged = masks!=0
    shuffled[tagged] = rng.permutation(masks[tagged])
    return dict(clusters=len(set(labels[assigned].tolist())), unassigned=int((~assigned).sum()),
                unassigned_fraction=float((~assigned).mean()), jointly_assigned_fraction=float(shared.mean()),
                ari_all=float(adjusted_rand_score(base,labels)),
                ari_joint=float(adjusted_rand_score(base[shared],labels[shared])) if shared.sum()>1 and
                    len(np.unique(base[shared]))>1 and len(np.unique(labels[shared]))>1 else None,
                tag_agreement=tag_overlap(labels,masks), shuffled_tag_agreement=tag_overlap(labels,shuffled))


def evaluate(folder,papers,vectors,progress):
    output = folder / "evaluation.json"
    main = geometry(folder,vectors,progress)
    reference = main["neighbors"]
    reference_hash=hashlib.sha256(reference.astype("<i4").tobytes()).hexdigest()
    if output.exists() and read_json(output).get("reference_sha256")==reference_hash:
        return read_json(output)
    pca_score = recall_at_ten(main["pca"][:,:2],reference)
    subjects = sorted({s for paper in papers for s in paper["subjects"]})
    bits = {s:1<<i for i,s in enumerate(subjects)}
    masks = np.array([sum(bits[s] for s in p["subjects"]) for p in papers],dtype=object)
    scores = []
    workers=max(1,min(4,int(os.environ.get("ATLAS_SEED_WORKERS","1"))))
    with ExitStack() as context:
        context.enter_context(threadpool_limits(limits=4))
        jobs={}
        if workers>1:
            pool=context.enter_context(ProcessPoolExecutor(max_workers=workers))
            jobs={s:pool.submit(prepare_seed,folder,s) for s in SEEDS if s!=42 and not (folder/"work"/f"seed-{s}.npz").exists()}
        for seed in SEEDS:
            stage = folder / "work" / f"metric-{seed}.json"
            if stage.exists() and read_json(stage).get("reference_sha256")==reference_hash:
                row = read_json(stage)
            else:
                if seed in jobs:jobs[seed].result()
                geometry_seed = main if seed==42 else run_seed(folder,vectors,main["knn"],main["knn_dist"],seed)
                xy = geometry_seed["xy"]
                score = recall_at_ten(xy,reference)
                shuffled = xy[np.random.default_rng(seed).permutation(len(xy))]
                row = dict(seed=seed, reference_sha256=reference_hash, umap_recall=score, pca_recall=pca_score,
                           shuffled_recall=recall_at_ten(shuffled,reference),difference=score-pca_score,
                           **cluster_metrics(geometry_seed["labels"],main["labels"],masks,seed))
                save_json(stage,row)
            scores.append(row)
            progress("Seed evaluation",len(scores),len(SEEDS),seed=seed,recall_at_10=round(row["umap_recall"],4))
    delta = np.array([s["difference"] for s in scores])
    mean = float(delta.mean())
    radius = float(t.ppf(.975,len(delta)-1)*delta.std(ddof=1)/np.sqrt(len(delta)))
    result = dict(snapshot=folder.name,reference_sha256=reference_hash,seeds=scores, primary=dict(mean_difference=mean,ci95=[mean-radius,mean+radius],
                  conclusion="supported" if mean-radius>0 else "falsified" if mean+radius<=0 else "inconclusive"),
                  pca_ablation=cluster_metrics(main["pca_labels"],main["labels"],masks,42),
                  n=len(papers), tagged=int(np.sum(masks!=0)), k=10)
    save_json(output,result)
    return result
