"""Stage only named public artifacts for a single Hugging Face dataset commit."""
import argparse
import json
import shutil
import subprocess
from pathlib import Path
from atlas.editions import edition_path


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("snapshot")
    args=parser.parse_args()
    root=Path.cwd()
    source=root/"results"/args.snapshot
    manifest=json.loads((source/"manifest.json").read_text(encoding="utf-8"))
    target=root/".atlas-cache"/"hub-release"/args.snapshot
    out=target/"results"/args.snapshot
    out.mkdir(parents=True,exist_ok=True)
    for name in ("manifest.json","papers.jsonl","papers.jsonl.gz","boundary-probes.json","embeddings.npy","embedding-info.json","geometry.npz","seed-layouts.npz",
                 "labels.json","label-traces.jsonl","api-usage.jsonl","evaluation.json","papers.parquet","checksums.json","audit.json","comparison.json",
                 "budget.json","budget-preflight.json","budget-reservations.jsonl",*(f.name for f in source.glob("rank-certificate-*.json"))):
        if (source/name).is_file():shutil.copyfile(source/name,out/name)
    if (source/"precision-check").exists():
        shutil.copytree(source/"precision-check",out/"precision-check",dirs_exist_ok=True)
    if (source/"evaluation.json").exists() and (source/"papers.parquet").exists():
        ev=json.loads((source/"evaluation.json").read_text(encoding="utf-8"))
        r=ev["seeds"][0]
        threshold=manifest["threshold_exclusive"]
        route=edition_path(threshold)
        base="https://burnycoder.github.io/top-ai-papers-visualized-alphaxiv/"
        site=base if threshold==100 else base+route.as_posix()+"/"
        paper=(Path("reports")/route/"paper.pdf").as_posix()
        # Both published tables remain selectable in the Hub dataset viewer.
        configs=[]
        for path in sorted((root/"results").glob("*/papers.parquet")):
            dated=path.parent.name
            config="default" if dated==args.snapshot else dated
            configs.append(f"- config_name: '{config}'\n  data_files:\n  - split: train\n    path: results/{dated}/papers.parquet")
        catalog="\n".join(configs)
        cost_note=""
        if (source/"budget.json").exists():
            budget=json.loads((source/"budget.json").read_bytes())
            cost_note=(f"Usage receipts for this edition total **USD {budget['estimated_usd']:.4f}** at standard rates. "
                       f"All attempts reserved USD {budget['reserved_usd']:.4f} against the USD {budget['cap_usd']:.2f} ceiling. "
                       f"[Cost breakdown](results/{args.snapshot}/budget.json) · [Per-attempt ledger](results/{args.snapshot}/budget-reservations.jsonl)")
        card=f"""---
pretty_name: alphaXiv Paper Atlas
language:
- en
tags:
- scientific-papers
- embeddings
- dimensionality-reduction
- clustering
configs:
{catalog}
---

# alphaXiv Paper Atlas

**[Open the interactive map]({site}) · [Code and preregistration](https://github.com/BurnyCoder/top-ai-papers-visualized-alphaxiv) · [Research paper]({paper})**

The {args.snapshot} snapshot contains {manifest['count']:,} distinct research papers with strictly more than {threshold} public alphaXiv likes. Two accepted passes used different page sizes. The collection covers all subjects and includes alphaXiv-exclusive manuscripts. Titles, abstracts and authors are credited to the individual papers. Consult the linked original publications for their licenses. [Original 100-like atlas]({base}) · [Original dataset tag](https://huggingface.co/datasets/BurnyCoder/alphaxiv-paper-atlas/tree/atlas-2026-11-26)

Two-dimensional UMAP displays OpenAI text-embedding-3-large vectors. A separate ten-dimensional UMAP and HDBSCAN generated {r['clusters']} clusters. GPT-6 Luna named each cluster from representative evidence. {r['unassigned']:,} unassigned papers remain visible. Exact original-space neighbors are listed by public paper ID. See [the evaluation](results/{args.snapshot}/evaluation.json) for all seeds and uncertainty. This descriptive snapshot conditions on platform attention. The train split is a Hub viewer convention covering the entire census.

{cost_note}

## Download and rebuild

Install uv and clone the GitHub project. Download this dated results folder into the checkout with the Hugging Face CLI, then run `uv run atlas build --snapshot {args.snapshot}`. The snapshot JSONL row order indexes both the vector matrix and geometry archive. The Parquet table contains paper text, IDs, authors, dates, subject tags, public votes, coordinates and recommendations. The folder also includes the retrieval audit, label evidence, timestamped labeling traces, per-seed metrics and checksums. The pre-inference implementation archive and protocol are preserved in this repository. [Reproduction guide](https://github.com/BurnyCoder/top-ai-papers-visualized-alphaxiv/blob/main/docs/reproduce.md)
"""
        (target/"README.md").write_text(card,encoding="utf-8")
        shutil.copytree(root/"reports",target/"reports",dirs_exist_ok=True)
        project=target/"project";project.mkdir(exist_ok=True)
        paths=["--","src","scripts","tests","reports","docs/reproduce.md","README.md","AGENTS.md","uv.lock","pyproject.toml",".python-version",".gitignore",".gitattributes",".env.example"] if threshold==10 else []
        subprocess.run(["git","archive","--format=zip","-o",str(project/"release-source.zip"),"HEAD",*paths],check=True)
    print(target)


if __name__=="__main__":
    main()
