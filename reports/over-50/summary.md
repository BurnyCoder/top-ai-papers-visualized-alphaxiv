# Snapshot summary · 2026-11-26-over-50

The 2026-11-26 snapshot contains **10,140 unique papers** above 50 likes and **115 named clusters**. The two accepted passes found the same papers. Of 10,181 entries above the threshold, 41 were marked as external posts. The public map shows all 3,262 unassigned papers in gray.

Across 10 seeds, UMAP retained **18.69%** of the original ten nearest neighbors, compared with **1.42%** under PCA. The gain was 17.28 percentage points (95% seed interval 17.23 to 17.33). Even with UMAP, 81.31% of those neighbors fell outside a paper’s ten closest screen points. Select a paper to recover its original-space recommendations.

Of these papers, **6,437** had 51–100 likes. The two dated editions share 3,703 paper groups. 6,437 groups appear only in the expanded edition and 0 appear only in the earlier one.

## Display seed and controls

| Display / assignments | Recall at 10 | Clusters | Unassigned | Shared subject within a cluster |
|---|---:|---:|---:|---:|
| UMAP / primary | 18.74% | 115 | 32.17% | 80.13% |
| PCA / primary | 1.42% | 115 | 32.17% | 80.13% |
| Shuffled positions / primary | 0.11% | 115 | 32.17% | 80.13% |
| PCA / PCA-clustering ablation | 1.42% | 17 | 82.79% | 43.02% |

The table describes seed 42. The PCA and shuffled projections retain the primary assignments in their corresponding rows. Across other seeds, adjusted Rand agreement including unassigned papers ranged from 0.543 to 0.581. 10,121 papers had recognized arXiv subject tags. Shuffled tag sets yielded 43.83% agreement at the display seed.

## Example topics

- **Reinforcement learning for LLM reasoning** (331 papers). [2503.16219](https://www.alphaxiv.org/abs/2503.16219), [2501.12948](https://www.alphaxiv.org/abs/2501.12948), [2506.14245](https://www.alphaxiv.org/abs/2506.14245)
- **Video-based 3D and 4D scene reconstruction** (233 papers). [2504.07961](https://www.alphaxiv.org/abs/2504.07961), [2504.01016](https://www.alphaxiv.org/abs/2504.01016), [2512.10935](https://www.alphaxiv.org/abs/2512.10935), [2511.19971](https://www.alphaxiv.org/abs/2511.19971)
- **Vision-language-action models for robotic manipulation** (229 papers). [2505.18719](https://www.alphaxiv.org/abs/2505.18719), [2601.02456](https://www.alphaxiv.org/abs/2601.02456), [2406.09246](https://www.alphaxiv.org/abs/2406.09246)
- **Retrieval-augmented generation for large language models** (192 papers). [2005.11401](https://www.alphaxiv.org/abs/2005.11401), [2312.10997](https://www.alphaxiv.org/abs/2312.10997), [2502.01142](https://www.alphaxiv.org/abs/2502.01142)

## Coverage and provenance

The collection window was 2026-11-26T11:52:26+00:00 to 2026-11-26T11:55:41+00:00. The independent page sizes were 100 and 50, taking 103 and 205 pages. The embedding matrix has 10,140 rows and 3,072 columns. The inputs contained 2,777,978 tokens. 0 papers used title-only input. The embedding cache supplied 3,703 distinct inputs at the start of the completed embedding invocation. OpenAI embedded 6,437 other inputs.

UMAP's default optimization budget was 200 epochs here and 500 in the earlier edition. The rule depends on corpus size. Each edition has an independently fitted coordinate system. Cross-edition differences in recall can reflect the corpus and the optimization budget. [UMAP implementation](https://umap-learn.readthedocs.io/en/latest/_modules/umap/umap_.html#simplicial_set_embedding)

[Coverage audit](../../results/2026-11-26-over-50/manifest.json) · [Per-seed results](../../results/2026-11-26-over-50/evaluation.json) · [Research protocol](preregistration.md) · [Published dataset](https://huggingface.co/datasets/BurnyCoder/alphaxiv-paper-atlas)
