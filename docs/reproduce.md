# Reproduce the atlas

Install [uv](https://docs.astral.sh/uv/getting-started/installation/), clone the repository and run `uv sync --frozen` at its root. The lockfile targets a local Python 3.12 environment. The authoring platform was Windows. Compatible CPU wheels suffice for the published analysis.

## Rebuild a published snapshot

Install the [Hugging Face CLI](https://huggingface.co/docs/huggingface_hub/guides/cli) and download the numerical assets into the checkout. The command below retrieves the first dated release and its manifest. Each new date has an independent folder.

```sh
hf download BurnyCoder/alphaxiv-paper-atlas --type dataset --include "results/2026-11-26/*" --local-dir .
uv run atlas build --snapshot 2026-11-26
uv run python -m http.server 8000 --bind 127.0.0.1 --directory docs
```

Open [the local map](http://127.0.0.1:8000). The offline build validates the snapshot, generates the table, figures, PDF and static map, and checks their paper IDs. Exact cached vectors enable independent neighbor and projection analyses. UMAP's optimizer and library versions can affect numerical reproductions.

## Fetch a fresh collection

Copy `.env.example` to an ignored `.env` and set your own alphaXiv and OpenAI keys. Run `uv run atlas refresh`. The console prints the snapshot name. For an explicit repeatable run use a new name, such as `uv run atlas refresh --snapshot my-census`. Resume with the identical name. Each verified census is frozen, and completed embedding batches, individual cluster names and seed results are checkpointed. A new named snapshot rechecks live membership. Input hashes allow unchanged papers to reuse the local embedding cache.

In a second terminal run `uv run atlas monitor` and open [live run progress](http://127.0.0.1:8765/). The dashboard displays stage, counts, elapsed time, API usage during embedding, and measured recall as seeds finish. The site’s Run details link displays the final release status. Full timestamped Luna prompts and responses go to the terminal and local `logs/`. Numeric embedding outputs are preserved losslessly in the published array. The static site never needs keys.

## Frozen files

The JSONL row order, sorted by group UUID, is the index of both numerical archives. `embeddings.npy` contains normalized float32 vectors. `geometry.npz` contains display coordinates, the ten-dimensional clustering space, assigned labels, membership strength, PCA coordinates and labels, and original cosine neighbors and distances. The first neighbor column is self. The next ten feed the explorer. `papers.parquet` includes stable paper IDs for all recommendations. `labels.json` links generated names to representative paper IDs. `evaluation.json` contains every seed and the primary interval. `checksums.json` records SHA-256 digests.

The official subject-code list is frozen from the [arXiv taxonomy](https://arxiv.org/category_taxonomy). Category metadata is used for filters and external descriptive checks. All hosted inputs are title and abstract text. Cluster names are generated after membership is fixed. [Protocol](../reports/preregistration.md) · [Run matrix](../reports/planned-runs.md)

## Verification

Run `uv run pytest -q`. After restoring the numeric artifacts, `uv run python scripts/audit_release.py 2026-11-26` independently recomputes original-space neighbors, projection scores and the interval, checks all release checksums and validates every piece of label evidence. With the local site running, use `uv run python tests/browser_smoke.py http://127.0.0.1:8000` for desktop and mobile interaction checks. By default this uses installed Chrome. With Playwright Chromium installed, pass `--channel chromium`. The checks exercise search by ID, title and author, combined filters, empty results, topic evidence, nearest neighbors, link sharing, zoom, CSV download and responsive layout.
