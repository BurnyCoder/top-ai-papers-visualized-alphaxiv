# Reproduce the atlas

Install [uv](https://docs.astral.sh/uv/getting-started/installation/), clone the repository and run `uv sync --frozen` at its root. The lockfile targets a local Python 3.12 environment. The authoring platform was Windows. Compatible CPU wheels suffice for the published analysis.

## Rebuild a published snapshot

### Over 20 likes

The three numerical arrays are on the tagged Hugging Face dataset. Git contains the matching census, rank certificates, labels, usage receipts and budget ledger. Rebuilding the site reads only local files.

```sh
hf download BurnyCoder/alphaxiv-paper-atlas results/2026-11-26-over-20/geometry.npz results/2026-11-26-over-20/embeddings.npy results/2026-11-26-over-20/seed-layouts.npz --type dataset --revision atlas-2026-11-26-over-20 --local-dir .
uv run atlas build --snapshot 2026-11-26-over-20
uv run python scripts/audit_release.py 2026-11-26-over-20
uv run python -m http.server 8000 --bind 127.0.0.1 --directory docs
```

Open `http://127.0.0.1:8000/over-20/`. The explorer fetches abstract text when requested. Its gzip-compressed CSV expands into a UTF-8 table. The tagged Parquet table contains the same papers in the same order. [Dataset](https://huggingface.co/datasets/BurnyCoder/alphaxiv-paper-atlas/tree/atlas-2026-11-26-over-20) · [Coverage amendment](../reports/over-20/collection-amendment.md)

Alternatively, run `uv run python scripts/verify_public.py 2026-11-26-over-20 --restore-arrays .` from the tagged checkout. It streams the live map assets and pinned Hub files, checks each digest, and restores the three numerical arrays after verification.

For a fresh over-20 census, use `uv run atlas refresh --threshold 20 --max-api-usd 50 --snapshot NEW_ID`. Reusing that ID resumes the same immutable ledger. The public metadata feed has no API credit charge. Every OpenAI attempt reserves an upper bound before transmission, and the final budget report prices returned usage at the cited standard rates. `uv run atlas monitor --port 18765` serves live progress. The optional `uv run --extra cuda atlas refresh ...` uses local GPU FP64 matrix multiplication when supported. All hosted models run through OpenAI. [Pricing](https://developers.openai.com/api/docs/pricing) · [CuPy installation](https://docs.cupy.dev/en/stable/install.html)

Set `ATLAS_SEED_WORKERS=2` on a machine with sufficient memory to fit independent sensitivity seeds concurrently. Each process opens the same read-only vectors and writes a distinct checkpoint. The default runs one seed at a time.

For the edition with more than 50 likes, restore the three numerical arrays, rebuild and open the `/over-50/` route of the local server. The published editions have distinct result directories and fit their own projections and clusters.

```sh
hf download BurnyCoder/alphaxiv-paper-atlas results/2026-11-26-over-50/geometry.npz results/2026-11-26-over-50/embeddings.npy results/2026-11-26-over-50/seed-layouts.npz --type dataset --revision atlas-2026-11-26-over-50 --local-dir .
uv run atlas build --snapshot 2026-11-26-over-50
uv run python -m http.server 8000 --bind 127.0.0.1 --directory docs
```

For a new census use `uv run atlas refresh --threshold 50`. Reusing a snapshot name resumes its frozen cutoff. Passing a different cutoff with that name reports the mismatch. The same three assets are available as direct downloads from the dated release. Save them under `results/2026-11-26-over-50/` before running the build. [Dated files](https://huggingface.co/datasets/BurnyCoder/alphaxiv-paper-atlas/tree/atlas-2026-11-26-over-50/results/2026-11-26-over-50) · [Expanded protocol](../reports/over-50/preregistration.md)

After building, `uv run python scripts/verify_public.py 2026-11-26-over-50` compares the live Pages assets and every checksummed file in the pinned Hub release against the local build. It streams the full public files over HTTPS.

### Original 100-like edition

Install the [Hugging Face CLI](https://huggingface.co/docs/huggingface_hub/guides/cli) and download the numerical assets into the checkout. Git includes the dated census, labels, manifest and metrics. Each new date has an independent folder.

```sh
hf download BurnyCoder/alphaxiv-paper-atlas results/2026-11-26/geometry.npz results/2026-11-26/embeddings.npy results/2026-11-26/seed-layouts.npz --type dataset --revision atlas-2026-11-26 --local-dir .
uv run atlas build --snapshot 2026-11-26
uv run python -m http.server 8000 --bind 127.0.0.1 --directory docs
```

Open [the local map](http://127.0.0.1:8000). The offline build validates the snapshot, generates the table, figures, PDF and static map, and checks their paper IDs. Exact cached vectors enable independent neighbor and projection analyses. UMAP's optimizer and library versions can affect numerical reproductions.

The same files are available by direct HTTPS. Save them under `results/2026-11-26/` in a checkout of the tagged source and run the build command above. [Source tag](https://github.com/BurnyCoder/top-ai-papers-visualized-alphaxiv/tree/atlas-2026-11-26) · [embeddings.npy](https://huggingface.co/datasets/BurnyCoder/alphaxiv-paper-atlas/resolve/atlas-2026-11-26/results/2026-11-26/embeddings.npy?download=true) · [geometry.npz](https://huggingface.co/datasets/BurnyCoder/alphaxiv-paper-atlas/resolve/atlas-2026-11-26/results/2026-11-26/geometry.npz?download=true) · [seed-layouts.npz](https://huggingface.co/datasets/BurnyCoder/alphaxiv-paper-atlas/resolve/atlas-2026-11-26/results/2026-11-26/seed-layouts.npz?download=true)

## Fetch a fresh collection

Copy `.env.example` to an ignored `.env` and set your own alphaXiv and OpenAI keys. Run `uv run atlas refresh`. The console prints the snapshot name. For an explicit repeatable run use a new name, such as `uv run atlas refresh --snapshot my-census`. Resume with the identical name. Each verified census is frozen, and completed embedding batches, individual cluster names and seed results are checkpointed. A new named snapshot rechecks live membership. Input hashes allow unchanged papers to reuse the local embedding cache.

In a second terminal run `uv run atlas monitor --port 0` and open the loopback URL it prints. Port zero selects an available port. Use `--port 8765` for a fixed address. The dashboard displays stage, counts, elapsed time, API usage during embedding, and measured recall as seeds finish. The site’s Run details link displays the final release status. Full timestamped Luna prompts and responses go to the terminal and local `logs/`. Numeric embedding outputs are preserved losslessly in the published array. The static site never needs keys.

## Frozen files

The JSONL row order, sorted by group UUID, is the index of both numerical archives. `embeddings.npy` contains normalized float32 vectors. `geometry.npz` contains display coordinates, the ten-dimensional clustering space, labels, membership strength and PCA outputs. Its `neighbors` array contains ten original-space recommendations per paper, ranked in float64 with self excluded. The separate `knn` and `knn_dist` arrays are the float32 graph used by UMAP, with self in column zero. `papers.parquet` includes stable public IDs for all recommendations. `labels.json` links generated names to representative paper IDs. `evaluation.json` contains every seed and the primary interval. `checksums.json` records SHA-256 digests.

The archive `seed-layouts.npz` contains the separate two- and ten-dimensional coordinates, assignments and membership strengths for every registered seed. Array keys follow `seed_42_xy`, `seed_42_z10`, `seed_42_labels` and `seed_42_strength`. Each uses the frozen JSONL row order.

The official subject-code list is frozen from the [arXiv taxonomy](https://arxiv.org/category_taxonomy). Category metadata is used for filters and external descriptive checks. All embedding inputs are title and abstract text. Cluster names are generated after membership is fixed. [Protocol](../reports/preregistration.md) · [Run matrix](../reports/planned-runs.md)

## Verification

Run `uv run pytest -q`. After restoring the numeric artifacts, `uv run python scripts/audit_release.py 2026-11-26` independently recomputes original-space neighbors, projection scores and the interval, checks all release checksums and validates every piece of label evidence. With the local site running, use `uv run python tests/browser_smoke.py http://127.0.0.1:8000` for desktop and mobile interaction checks. By default this uses installed Chrome. With Playwright Chromium installed, pass `--channel chromium`. The checks exercise search by ID, title and author, combined filters, empty results, topic evidence, nearest neighbors, link sharing, zoom, CSV download and responsive layout.
