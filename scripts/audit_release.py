"""Independently recheck snapshot coverage, geometry, scores, uncertainty and release identities."""
import csv
import hashlib
import json
import sys
from pathlib import Path
import numpy as np
from scipy import stats
from sklearn.neighbors import NearestNeighbors
from threadpoolctl import threadpool_limits
from atlas.io import ROOT, papers_at, read_json, save_json


def audit(snapshot):
    folder=ROOT/"results"/snapshot
    manifest=read_json(folder/"manifest.json"); papers=papers_at(folder)
    ev=read_json(folder/"evaluation.json");labels=read_json(folder/"labels.json")
    geo=np.load(folder/"geometry.npz",allow_pickle=False)
    vectors=np.load(folder/"embeddings.npy",allow_pickle=False)
    api=list(map(json.loads,(folder/"api-usage.jsonl").read_text(encoding="utf-8").splitlines()))
    traces=list(map(json.loads,(folder/"label-traces.jsonl").read_text(encoding="utf-8").splitlines()))
    passes=manifest["passes"][-2:]
    assert all(p["inversions"]==0 and p["eligible"]==len(papers) for p in passes)
    assert all(p["last_page"]["max_likes"] is None or p["last_page"]["max_likes"]<=100 for p in passes)
    assert not any(manifest["differences"][-1].values()) and min(p["likes"] for p in papers)>100
    ids=[p["id"] for p in papers];by_public={p["paper_id"]:i for i,p in enumerate(papers)}
    assert ids==sorted(set(ids))
    public=read_json(ROOT/"docs/atlas.json")
    with (ROOT/"docs/papers.csv").open(encoding="utf-8-sig",newline="") as stream:
        assert ids==[p["id"] for p in csv.DictReader(stream)]==[p["id"] for p in public["papers"]]
    for g,record in labels.items():
        assert 2<=len(record["evidence"])<=4 and set(record["evidence"])<=set(record["representatives"])
        assert all(geo["labels"][by_public[i]]==int(g) for i in record["evidence"])
    for filename,digest in read_json(folder/"checksums.json").items():
        assert hashlib.sha256((folder/filename).read_bytes()).hexdigest()==digest,filename
    # Compute all cosine ranks in float64 using an independent sklearn retrieval implementation.
    with threadpool_limits(limits=4):
        reference=NearestNeighbors(n_neighbors=10,algorithm="brute",metric="cosine",n_jobs=1).fit(vectors.astype("float64")).kneighbors(return_distance=False)
    def overlap(a,b):
        return sum(len(set(x).intersection(y)) for x,y in zip(a,b,strict=True))/(10*len(a))
    neighbor_agreement=overlap(reference,geo["neighbors"])
    if neighbor_agreement!=1:raise AssertionError(f"Original-space cross-check {neighbor_agreement}")
    reference=geo["neighbors"]
    def independently_measure(points):
        near=NearestNeighbors(n_neighbors=10,algorithm="kd_tree").fit(points).kneighbors(return_distance=False)
        return overlap(near,reference)
    r=ev["seeds"][0]
    x=independently_measure(geo["xy"]);baseline=independently_measure(geo["pca"][:,:2])
    control=independently_measure(geo["xy"][np.random.default_rng(42).permutation(len(papers))])
    assert np.allclose([x,baseline,control],[r["umap_recall"],r["pca_recall"],r["shuffled_recall"]],atol=1e-10)
    with np.load(folder/"seed-layouts.npz",allow_pickle=False) as layouts:
        assert str(layouts["paper_sha256"])==manifest["content_sha256"]
        for row in ev["seeds"]:
            seed=row["seed"]
            points=layouts[f"seed_{seed}_xy"]
            perm=np.random.default_rng(seed).permutation(len(papers))
            assert independently_measure(points)==row["umap_recall"]
            assert independently_measure(points[perm])==row["shuffled_recall"]
            assert int((layouts[f"seed_{seed}_labels"]<0).sum())==row["unassigned"]
    d=np.array([v["umap_recall"]-v["pca_recall"] for v in ev["seeds"]])
    interval=stats.t.interval(.95,df=len(d)-1,loc=d.mean(),scale=stats.sem(d))
    assert np.allclose(interval,ev["primary"]["ci95"])
    same_names=len(labels)-len({g["name"].casefold() for g in labels.values()})
    result=dict(paper_ids=len(ids),independent_neighbor_overlap=neighbor_agreement,independent_seed42_recall=x,
                independent_pca_recall=baseline,independent_shuffled_recall=control,independent_ci95=list(interval),
                seed_layouts_rechecked=len(ev["seeds"]),clusters_with_validated_evidence=len(labels),extra_duplicate_names=same_names,
                embedding_requests=sum(x["phase"]=="embeddings" for x in api),label_requests=sum(x["phase"]=="labels" for x in api),
                complete_label_responses=len(traces),vector_norm_max_abs_error=float(abs(np.linalg.norm(vectors,axis=1)-1).max()))
    save_json(folder/"audit.json",result)
    report=f"""# Release review · {snapshot}

## Independent scientific checks

Two complete feed passes agreed on all {len(ids):,} research-paper group IDs. Both crossed the strict boundary, with no observed inversion. The JSONL, static map and CSV contain those IDs in the same order. The build independently round-trips the Parquet IDs too. All archived SHA-256 digests verified.

Recomputing all nearest neighbors with scikit-learn in float64 recovered {neighbor_agreement:.6%} of the published top-ten entries. The archived vectors are float32 and the ranking uses float64 arithmetic. The maximum absolute vector-norm error was {result['vector_norm_max_abs_error']:.3g}. A separate kd-tree implementation reproduced the display-seed UMAP, PCA and shuffled recall values ({x:.6f}, {baseline:.6f}, {control:.6f}), plus UMAP and shuffled recall for all {len(ev['seeds'])} archived layouts. An independent Student t calculation reproduced the registered interval. All {len(labels)} assigned groups have valid evidence from their own members.

## Interpretation and limitations

The procedure samples highly liked public research papers from a non-atomic feed and measures compression of a hosted representation. It cannot establish research quality, a community-wide topic distribution, or causal differences between fields. Shared tags may reflect broad fields and cross-listing. The 95% interval describes optimizer seed variation on this corpus. Pairs are dependent and larger clusters contribute more pairs to the subject statistic.

There were {same_names} repeated topic names beyond their first occurrence. The browser distinguishes those clusters by group ID while preserving Luna’s source response. Unassigned papers retain metadata and recommendations. The source-space control and PCA ablation are included even when their behavior is less useful for browsing.

## Engineering checks

API keys are read in the local pipeline. Model instructions and paper text remain outside the static code path. Browser-facing paper text is assigned through textContent. Completed embedding batches and labels survive interruption. Both the raw measurements and the standalone build are versioned. The regression and real-browser checks are documented in the reproduction guide.

[Raw audit](../../results/{snapshot}/audit.json) · [Per-seed results](../../results/{snapshot}/evaluation.json) · [Preregistration](../preregistration.md)
"""
    (ROOT/"reports/reviews/release.md").write_text(report,encoding="utf-8")
    print(json.dumps(result,indent=2))


if __name__=="__main__":
    audit(sys.argv[1])
