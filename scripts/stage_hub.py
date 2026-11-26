"""Stage only named public artifacts for a single Hugging Face dataset commit."""
import argparse
import json
import shutil
import subprocess
from pathlib import Path


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
    for name in ("manifest.json","papers.jsonl","embeddings.npy","embedding-info.json","geometry.npz","seed-layouts.npz",
                 "labels.json","label-traces.jsonl","api-usage.jsonl","evaluation.json","papers.parquet","checksums.json","audit.json"):
        if (source/name).is_file():shutil.copyfile(source/name,out/name)
    if (source/"precision-check").exists():
        shutil.copytree(source/"precision-check",out/"precision-check",dirs_exist_ok=True)
    if (source/"evaluation.json").exists() and (source/"papers.parquet").exists():
        ev=json.loads((source/"evaluation.json").read_text(encoding="utf-8"))
        r=ev["seeds"][0]
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
- config_name: default
  data_files:
  - split: train
    path: results/{args.snapshot}/papers.parquet
---

# alphaXiv Paper Atlas

**[Open the interactive map](https://burnycoder.github.io/top-ai-papers-visualized-alphaxiv/) · [Code and preregistration](https://github.com/BurnyCoder/top-ai-papers-visualized-alphaxiv) · [Research paper](reports/paper.pdf)**

The {args.snapshot} snapshot contains {manifest['count']:,} distinct research papers with strictly more than 100 public alphaXiv likes. The feed was read twice with different page sizes. The collection covers all subjects and includes alphaXiv-exclusive manuscripts. Titles, abstracts and authors are credited to the individual papers. Consult the linked original publications for their licenses.

Two-dimensional UMAP displays OpenAI text-embedding-3-large vectors. A separate ten-dimensional UMAP and HDBSCAN generated {r['clusters']} clusters. GPT-6 Luna named each cluster from representative evidence. {r['unassigned']:,} unassigned papers remain visible. Exact original-space neighbors are listed by public paper ID. See [the evaluation](results/{args.snapshot}/evaluation.json) for all seeds and uncertainty. This descriptive snapshot conditions on platform attention. The train split is a Hub viewer convention covering the entire census.

## Download and rebuild

Install uv and clone the GitHub project. Download this dated results folder into the checkout with the Hugging Face CLI, then run `uv run atlas build --snapshot {args.snapshot}`. The snapshot JSONL row order indexes both the vector matrix and geometry archive. The Parquet table contains paper text, IDs, authors, dates, subject tags, public votes, coordinates and recommendations. The folder also includes the retrieval audit, label evidence, timestamped labeling traces, per-seed metrics and checksums. The pre-inference implementation archive and protocol are preserved in this repository. [Reproduction guide](https://github.com/BurnyCoder/top-ai-papers-visualized-alphaxiv/blob/main/docs/reproduce.md)
"""
        (target/"README.md").write_text(card,encoding="utf-8")
        shutil.copytree(root/"reports",target/"reports",dirs_exist_ok=True)
        project=target/"project";project.mkdir(exist_ok=True)
        subprocess.run(["git","archive","--format=zip","-o",str(project/"release-source.zip"),"HEAD"],check=True)
    print(target)


if __name__=="__main__":
    main()
