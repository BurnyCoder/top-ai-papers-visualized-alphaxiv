# Snapshot summary · 2026-11-26-over-20

The 2026-11-26 snapshot contains **36,276 unique papers** above 20 likes and **313 named clusters**. The two accepted passes found the same papers. Of 36,329 entries above the threshold, 53 were marked as external posts. The public map shows all 13,787 unassigned papers in gray.

Across 10 seeds, UMAP retained **12.81%** of the original ten nearest neighbors, compared with **0.49%** under PCA. The gain was 12.32 percentage points (95% seed interval 12.27 to 12.37). Even with UMAP, 87.19% of those neighbors fell outside a paper’s ten closest screen points. Select a paper to recover its original-space recommendations. Shuffling the paper-to-position assignment retained 0.03% across the same seeds.

Of these papers, **26,136** had 21–50 likes. The two dated editions share 10,140 paper groups. 26,136 groups appear only in the expanded edition and 0 appear only in the earlier one.

OpenAI usage receipts priced at standard rates total **USD 0.9687** for this edition. The ledger reserved USD 14.4372 against the USD 50.00 ceiling. Attempts without a usage receipt: 0. [Credit ledger](https://github.com/BurnyCoder/top-ai-papers-visualized-alphaxiv/blob/main/results/2026-11-26-over-20/budget.json)

## Display seed and controls

| Display / assignments | Recall at 10 | Clusters | Unassigned | Shared subject within a cluster |
|---|---:|---:|---:|---:|
| UMAP / primary | 12.87% | 313 | 38.01% | 79.95% |
| PCA / primary | 0.49% | 313 | 38.01% | 79.95% |
| Shuffled positions / primary | 0.03% | 313 | 38.01% | 79.95% |
| PCA / PCA-clustering ablation | 0.49% | 21 | 86.65% | 37.19% |

The table describes seed 42. The PCA and shuffled projections retain the primary assignments in their corresponding rows. Across other seeds, adjusted Rand agreement including unassigned papers ranged from 0.569 to 0.587. 36,226 papers had recognized arXiv subject tags. Shuffled tag sets yielded 36.83% agreement at the display seed.

## Example topics

- **Large language models for recommendation** (473 papers). [2310.15950](https://www.alphaxiv.org/abs/2310.15950), [2409.12740](https://www.alphaxiv.org/abs/2409.12740), [2504.11889](https://www.alphaxiv.org/abs/2504.11889)
- **Reinforcement learning for LLM reasoning** (460 papers). [2602.05281](https://www.alphaxiv.org/abs/2602.05281), [2503.16219](https://www.alphaxiv.org/abs/2503.16219), [2510.03865](https://www.alphaxiv.org/abs/2510.03865), [2506.14245](https://www.alphaxiv.org/abs/2506.14245)
- **Vision-language-action models for robotic manipulation** (452 papers). [2606.06155](https://www.alphaxiv.org/abs/2606.06155), [2601.02456](https://www.alphaxiv.org/abs/2601.02456), [2505.18719](https://www.alphaxiv.org/abs/2505.18719)
- **Knowledge-Graph Retrieval-Augmented Generation** (396 papers). [2502.11371](https://www.alphaxiv.org/abs/2502.11371), [2503.04338](https://www.alphaxiv.org/abs/2503.04338), [2510.10114](https://www.alphaxiv.org/abs/2510.10114), [2508.10391](https://www.alphaxiv.org/abs/2508.10391)

## Coverage and provenance

The collection window was 2026-11-26T12:51:03+00:00 to 2026-11-26T13:09:14+00:00. The independent page sizes were 100 and 200, taking 365 and 183 pages. The embedding matrix has 36,276 rows and 3,072 columns. The inputs contained 9,787,486 tokens. 0 papers used title-only input. The embedding cache supplied 10,139 distinct inputs at the start of the completed embedding invocation. OpenAI embedded 26,136 other inputs. Identical title-and-abstract text occurred in separate paper groups. 36,275 distinct inputs cover 36,276 map points.

Unfiltered pages repeated groups within tied scores. Supplemental queries recovered the skipped IDs. The last qualifying global rank was 36,329 at 21 likes. The next entry had 20 likes. 3 papers had different vote observations in the two accepted passes.

| Page size | Global pages | Initially missing ranks | Supplementary pages | Unresolved ranks |
|---:|---:|---:|---:|---:|
| 100 | 365 | 7,502 | 1,151 | 0 |
| 200 | 183 | 8,154 | 864 | 0 |

[First rank certificate](../../results/2026-11-26-over-20/rank-certificate-100.json) · [Second rank certificate](../../results/2026-11-26-over-20/rank-certificate-200.json) · [Collection amendment](collection-amendment.md)

Both editions used 200 UMAP epochs per fit. The larger corpus changes each paper’s potential neighbors, and the two maps have independent coordinate systems.

[Coverage audit](../../results/2026-11-26-over-20/manifest.json) · [Per-seed results](../../results/2026-11-26-over-20/evaluation.json) · [Research protocol](preregistration.md) · [Published dataset](https://huggingface.co/datasets/BurnyCoder/alphaxiv-paper-atlas)
