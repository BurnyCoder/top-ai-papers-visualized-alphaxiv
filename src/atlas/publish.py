"""Offline export of the exact same group IDs to the browser, table, dataset and paper."""
from __future__ import annotations

import colorsys
import csv
import hashlib
import io
import json
import shutil
from collections import Counter
from pathlib import Path
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

from .figures import figures
from .geometry import SEEDS, load_arrays, save_arrays
from .io import COLLECTION, GITHUB, HUB, PACKAGE, PAGES, ROOT, RESULTS, papers_at, read_json, save_bytes, save_json
from .paper import make_paper, pct


def color_for(group):
    if group<0: return "#91988e"
    palette=["#06765b","#a25238","#7763a6","#287aa4","#bd6c23","#427c39","#b75c82","#287f84","#8f6940","#786890"]
    if group<len(palette):return palette[group]
    r,g,b=colorsys.hls_to_rgb((group*.61803398875)%1,.39+.045*(group%3),.48+.06*(group%2))
    return "#{:02x}{:02x}{:02x}".format(round(r*255),round(g*255),round(b*255))


def export_data(folder, docs, manifest, papers, A, labels):
    """The compact browser neighbor arrays index the unmodified snapshot row order."""
    groups=Counter(map(int,A["labels"]))
    clusters={}
    for group,count in groups.items():
        entry=labels[str(group)] if group>=0 else {"name":"Unassigned","evidence":[],"representatives":[],"terms":[]}
        clusters[str(group)]={**entry,"count":count,"color":color_for(group)}
    repeated=Counter(c["name"].casefold() for c in clusters.values())
    for group,entry in clusters.items():
        if repeated[entry["name"].casefold()]>1:
            entry["display_name"]=entry["name"]+f" · group {group}"
    if set(labels)!=set(str(g) for g in groups if g>=0):
        raise ValueError("Host label IDs and assigned groups differ")
    ids=[p["id"] for p in papers]; public_ids={p["paper_id"] for p in papers}
    if len(set(ids))!=len(papers) or len(public_ids)!=len(papers) or len(A["xy"])!=len(papers):
        raise ValueError("Paper or coordinate identity mismatch")
    lookup={p["paper_id"]:int(A["labels"][i]) for i,p in enumerate(papers)}
    for g,c in clusters.items():
        if any(lookup.get(id_)!=int(g) for id_ in c["evidence"]):
            raise ValueError("A label cites a paper outside its cluster")
    if not np.isfinite(A["xy"]).all():
        raise ValueError("Nonfinite map coordinates")
    atlas_rows=[];table=[]
    for i,p in enumerate(papers):
        neigh=list(map(int,A["neighbors"][i]))
        if len(set(neigh))!=10 or i in neigh or min(neigh)<0 or max(neigh)>=len(papers) or p["likes"]<=100:
            raise ValueError("Invalid neighborhood or threshold in snapshot")
        record={**p,"x":float(A["xy"][i,0]),"y":float(A["xy"][i,1]),"cluster":int(A["labels"][i]),"neighbors":neigh}
        atlas_rows.append(record)
        table.append({**record,"neighbors":[papers[j]["paper_id"] for j in neigh],
                "cluster_name":clusters[str(record["cluster"])]["name"],"membership_strength":float(A["strength"][i])})
    save_json(docs/"atlas.json",dict(snapshot=folder.name,date=manifest["ended_at"][:10],papers=atlas_rows,clusters=clusters,
              cluster_count=sum(g>=0 for g in groups),unassigned=groups.get(-1,0)),compact=True)
    stream=io.StringIO(newline="")
    writer=csv.DictWriter(stream,fieldnames=list(table[0]),lineterminator="\n");writer.writeheader()
    for row in table:
        writer.writerow({k:json.dumps(v,ensure_ascii=False) if isinstance(v,list) else v for k,v in row.items()})
    save_bytes(docs/"papers.csv",stream.getvalue().encode("utf-8-sig"))
    pq.write_table(pa.Table.from_pylist(table), folder/"papers.parquet", compression="zstd")
    with (docs/"papers.csv").open(encoding="utf-8-sig",newline="") as f:
        csv_ids=[r["id"] for r in csv.DictReader(f)]
    web_ids=[r["id"] for r in read_json(docs/"atlas.json")["papers"]]
    parquet_ids=pq.read_table(folder/"papers.parquet",columns=["id"])["id"].to_pylist()
    if not ids==web_ids==csv_ids==parquet_ids or len(ids)!=manifest["count"]:
        raise ValueError("Census, browser map, CSV or Parquet IDs disagree")
    return clusters


def reports(folder,manifest,evaluation,clusters,embedding):
    """Generate numbers in prose, tables and every experiment index from archived results."""
    rows=evaluation["seeds"]; r=rows[0]; a=evaluation["pca_ablation"]; pri=evaluation["primary"]
    def mean(k):return sum(row[k] for row in rows)/len(rows)
    def pp(v):return f"{100*v:.2f}"
    n=manifest["count"];first=manifest["passes"][0];last=manifest["passes"][-1]
    change=f"{pp(pri['mean_difference'])} percentage points (95% seed interval {pp(pri['ci95'][0])} to {pp(pri['ci95'][1])})"
    def scoretable():
        header="| Display / assignments | Recall at 10 | Clusters | Unassigned | Shared subject within a cluster |\n|---|---:|---:|---:|---:|"
        entries=[("UMAP / primary",r["umap_recall"],r),("PCA / primary",r["pca_recall"],r),
                 ("Shuffled positions / primary",r["shuffled_recall"],r),("PCA / PCA-clustering ablation",r["pca_recall"],a)]
        return header+"\n"+"\n".join(f"| {name} | {pct(score)} | {c['clusters']} | {pct(c['unassigned_fraction'])} | {pct(c['tag_agreement']['fraction'])} |" for name,score,c in entries)
    desc=(f"The {folder.name} snapshot contains **{n:,} unique papers** and **{r['clusters']} named topics**. "
          f"Both passes found the same papers. Of {sum(p['above_100'] for p in first['pages']):,} entries above the threshold, "
          f"{first['excluded_blogs']} were marked as external posts. The public map shows all {r['unassigned']:,} unassigned papers in gray.\n\n"
          f"Across {len(rows)} seeds, UMAP retained **{pct(mean('umap_recall'))}** of the original ten nearest neighbors, "
          f"compared with **{pct(r['pca_recall'])}** under PCA. The gain was {change}. "
          f"Even with UMAP, {pct(1-mean('umap_recall'))} of those neighbors fell outside a paper’s ten closest screen points. "
          "Select a paper to recover its original-space recommendations.")
    examples=sorted((c for g,c in clusters.items() if int(g)>=0),key=lambda c:-c["count"])[:4]
    ex="\n".join(f"- **{c['name']}** ({c['count']} papers). "+", ".join("["+i+"](https://www.alphaxiv.org/abs/"+i+")" for i in c["evidence"]) for c in examples)
    full=f"""# Snapshot summary · {folder.name}

{desc}

## Display seed and controls

{scoretable()}

The table describes seed {r['seed']}. The PCA and shuffled projections retain the primary assignments in their corresponding rows. Across other seeds, adjusted Rand agreement including unassigned papers ranged from {min(s['ari_all'] for s in rows[1:]):.3f} to {max(s['ari_all'] for s in rows[1:]):.3f}. {evaluation['tagged']:,} papers had recognized arXiv subject tags. Shuffled tag sets yielded {pct(r['shuffled_tag_agreement']['fraction'])} agreement at the display seed.

## Example topics

{ex}

## Coverage and provenance

The collection window was {manifest['started_at']} to {manifest['ended_at']}. The independent page sizes were {first['page_size']} and {last['page_size']}, taking {len(first['pages'])} and {len(last['pages'])} pages. The embedding matrix has {embedding['rows']:,} rows and {embedding['dimensions']:,} columns. The inputs contained {embedding['input_tokens']:,} tokens. {manifest['title_only']} papers used title-only input.

[Coverage audit](../results/{folder.name}/manifest.json) · [Per-seed results](../results/{folder.name}/evaluation.json) · [Research protocol](preregistration.md) · [Published dataset]({HUB})
"""
    report=ROOT/"reports";exp=report/"experiments"/folder.name;exp.mkdir(parents=True,exist_ok=True)
    save_bytes(report/"summary.md",full.encode())
    save_bytes(exp/"experiment.md",(f"# Experiment · {folder.name}\n\n"+desc+"\n\n"+scoretable()+
        "\n\n[Methods and parameter choices](../../preregistration.md) · [Per-seed records](../../../results/"+folder.name+"/evaluation.json)\n").encode())
    learning=(f"# Learnings · {folder.name}\n\nThe strict cutoff by rank included {first['excluded_blogs']} externally marked posts. "
             "Checking each record’s type reconciled the feed rank and the paper count.\n\n"
             f"UMAP’s {change} gain measures local neighborhood fidelity. The lost-neighbor fraction motivates the separate recommendation list. "
             f"At seed 42 the ten-PC ablation assigned {pct(1-a['unassigned_fraction'])} of papers, compared with {pct(1-r['unassigned_fraction'])} for ten-dimensional UMAP. "
             f"Shared subject agreement among assigned and tagged pairs was {pct(a['tag_agreement']['fraction'])} and {pct(r['tag_agreement']['fraction'])}, respectively. "
             "These are conditional comparisons because the assigned sets can differ. The evaluation uses the frozen corpus and held-out tags.\n")
    boundary=folder/"precision-check"/"boundary.json"
    if boundary.exists():
        count=len(read_json(boundary))
        learning+=(f"\nThe precision audit found a change in the tenth neighbor for {count:,} of {n:,} papers. "
                   "The released recommendations rank the archived vectors in float64. "
                   "[Boundary evidence and correction](../../reviews/precision.md)\n")
    save_bytes(exp/"learnings.md",learning.encode())
    paths=sorted((report/"experiments").glob("*/experiment.md"))
    index="\n".join(f"- [{p.parent.name}]({p.parent.name}/experiment.md) · [Learnings]({p.parent.name}/learnings.md)" for p in paths)
    save_bytes(report/"experiments/experiments.md",("# Experiment index\n\n"+index+"\n\nRecall measures how many original neighbors survive projection. Adjusted Rand agreement describes consistency of assignments after correcting for chance.\n").encode())
    save_bytes(report/"experiments/learnings.md",("# Learnings by snapshot\n\n"+index+"\n").encode())
    readme=ROOT/"README.md";start="<!-- results:start -->";end="<!-- results:end -->"
    text=readme.read_text(encoding="utf-8");head,rest=text.split(start,1);_,tail=rest.split(end,1)
    block="\n\n"+desc+"\n\n![Map and largest topics](reports/figures/atlas.png)\n\n"+scoretable()+"\n\n[All seed results and cluster examples](reports/summary.md) · [Comparison figures](reports/figures/comparisons.png) · [Seed sensitivity](reports/figures/metrics.png)\n\n"
    save_bytes(readme,(head+start+block+end+tail).encode())
    return desc


def build(folder,progress):
    """Rebuild from saved observations and numerical artifacts, without a network dependency."""
    docs=ROOT/"docs";docs.mkdir(exist_ok=True)
    report=ROOT/"reports";figdir=report/"figures"
    manifest=read_json(folder/"manifest.json");papers=papers_at(folder)
    if manifest["coverage"]!="verified" or hashlib.sha256((folder/"papers.jsonl").read_bytes()).hexdigest()!=manifest["content_sha256"]:
        raise ValueError("Snapshot membership or checksum failed verification")
    A=load_arrays(folder/"geometry.npz");labels=read_json(folder/"labels.json")
    evaluation=read_json(folder/"evaluation.json");embedding=read_json(folder/"embedding-info.json")
    if hashlib.sha256(A["neighbors"].astype("<i4").tobytes()).hexdigest()!=evaluation["reference_sha256"]:
        raise ValueError("The score references a different nearest-neighbor table")
    if str(A["paper_sha256"])!=manifest["content_sha256"] or str(A["vector_sha256"])!=embedding["vectors_sha256"]:
        raise ValueError("Geometry was fitted to a different paper order or vector matrix")
    if (folder/"embeddings.npy").exists() and hashlib.sha256((folder/"embeddings.npy").read_bytes()).hexdigest()!=embedding["vectors_sha256"]:
        raise ValueError("The frozen embedding matrix failed its SHA-256 integrity check")
    progress("Offline build",0,4)
    clusters=export_data(folder,docs,manifest,papers,A,labels)
    for path in (PACKAGE/"web").iterdir():shutil.copyfile(path,docs/path.name)
    save_bytes(docs/".nojekyll",b"");progress("Offline build",1,4)
    figures(figdir,A,clusters,evaluation);progress("Offline build",2,4)
    reports(folder,manifest,evaluation,clusters,embedding)
    make_paper(report/"paper.pdf",manifest,evaluation,clusters,figdir)
    shutil.copyfile(report/"paper.pdf",docs/"paper.pdf")
    # Publish each fitted layout so readers can recompute seed statistics without rerunning UMAP.
    archive=folder/"seed-layouts.npz"
    seed_files={s:folder/"work"/f"seed-{s}.npz" for s in SEEDS}
    if not archive.exists() and all(p.exists() for p in seed_files.values()):
        layouts={f"seed_{s}_{key}":arr for s,p in seed_files.items() for key,arr in load_arrays(p).items()}
        save_arrays(archive,paper_sha256=A["paper_sha256"],**layouts)
    checksum_files=["manifest.json","papers.jsonl","embedding-info.json","embeddings.npy","geometry.npz","seed-layouts.npz","labels.json","evaluation.json","papers.parquet"]
    checks={}
    previous=(folder/"checksums.json")
    if previous.exists():checks.update(read_json(previous))
    for file in checksum_files:
        if (folder/file).exists():checks[file]=hashlib.sha256((folder/file).read_bytes()).hexdigest()
    save_json(previous,checks)
    progress("Complete",4,4,papers=manifest["count"],clusters=evaluation["seeds"][0]["clusters"],
             recall_at_10=evaluation["seeds"][0]["umap_recall"],coverage=manifest["coverage"])
    # The published run summary has a stable observation timestamp, unlike the live progress clock.
    save_json(docs/"progress.json",dict(snapshot=folder.name,stage="Complete",done=4,total=4,updated_at=manifest["ended_at"],
              papers=manifest["count"],clusters=evaluation["seeds"][0]["clusters"],seed_42_recall_at_10=evaluation["seeds"][0]["umap_recall"],
              collection_window_end=manifest["ended_at"]))
