"""Original-space nearest neighbors, independent UMAP fits and preregistered census-level metrics."""
from __future__ import annotations

import io
import hashlib
import warnings
from collections import Counter
import numpy as np
from scipy.spatial.distance import cdist
from scipy.stats import t
from sklearn.cluster import HDBSCAN
from sklearn.decomposition import PCA
from sklearn.metrics import adjusted_rand_score
from threadpoolctl import threadpool_limits

from .io import read_json, save_bytes, save_json

SEEDS = tuple(range(42,52))


def save_arrays(path, **arrays):
    """Use a single atomic archive so resumed runs cannot mix partial coordinates and IDs."""
    buffer = io.BytesIO()
    np.savez_compressed(buffer, **arrays)
    save_bytes(path, buffer.getvalue())


def load_arrays(path):
    with np.load(path, allow_pickle=False) as archive:
        return {key:archive[key] for key in archive.files}


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
        other=np.argsort(dist,axis=1,kind="stable")[:,:count-1]
        ids[start:stop,1:]=other
        values[start:stop,1:]=np.take_along_axis(dist,other,axis=1)
    return ids, values


def original_neighbors(vectors):
    """Rank the archived vectors in float64 to resolve close cosine ties before publishing recommendations."""
    unit=np.asarray(vectors,dtype=np.float64)
    unit=unit/np.linalg.norm(unit,axis=1,keepdims=True)
    ids=np.empty((len(unit),10),dtype=np.int32)
    for start in range(0,len(unit),256):
        stop=min(start+256,len(unit))
        similarity=unit[start:stop] @ unit.T
        similarity[np.arange(stop-start),np.arange(start,stop)]=-np.inf
        ids[start:stop]=np.argsort(-similarity,axis=1,kind="stable")[:,:10]
    return ids


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
    """Corpus average intersection fraction, with stable exact Euclidean retrieval in blocks."""
    n = len(xy)
    total = 0
    target = np.sort(neighbors[:,:10],axis=1)
    for start in range(0,n,256):
        stop = min(start+256,n)
        dist = cdist(xy[start:stop],xy,metric="sqeuclidean")
        dist[np.arange(stop-start),np.arange(start,stop)] = np.inf
        near = np.argsort(dist,axis=1,kind="stable")[:,:10]
        total += np.any(near[:,:,None]==target[start:stop,None,:],axis=2).sum()
    return float(total/(n*10))


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
    with threadpool_limits(limits=4):
        for seed in SEEDS:
            stage = folder / "work" / f"metric-{seed}.json"
            if stage.exists() and read_json(stage).get("reference_sha256")==reference_hash:
                row = read_json(stage)
            else:
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
