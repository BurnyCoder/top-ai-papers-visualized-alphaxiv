# Snapshot summary · 2026-11-26-over-10

The 2026-11-26 snapshot contains **100,942 unique papers** above 10 likes and **725 named clusters**. The two accepted passes found the same papers. Of 101,003 entries above the threshold, 61 were marked as external posts. The public map shows all 42,441 unassigned papers in gray.

Across 10 seeds, UMAP retained **8.99%** of the original ten nearest neighbors, compared with **0.21%** under PCA. The gain was 8.78 percentage points (95% seed interval 8.70 to 8.86). Even with UMAP, 91.01% of those neighbors fell outside a paper’s ten closest screen points. Select a paper to recover its original-space recommendations. Shuffling the paper-to-position assignment retained 0.01% across the same seeds.

Of these papers, **64,662** had 11–20 likes. The two dated editions share 36,276 paper groups. 64,666 groups appear only in the expanded edition and 0 appear only in the earlier one.

OpenAI usage receipts priced at standard rates total **USD 2.3227** for this edition. The ledger reserved USD 8.7512 against the USD 50.00 ceiling. Attempts without a usage receipt: 0. [Credit ledger](https://github.com/BurnyCoder/top-ai-papers-visualized-alphaxiv/blob/main/results/2026-11-26-over-10/budget.json)

## Display seed and controls

| Display / assignments | Recall at 10 | Clusters | Unassigned | Shared subject within a cluster |
|---|---:|---:|---:|---:|
| UMAP / primary | 8.96% | 725 | 42.04% | 76.13% |
| PCA / primary | 0.21% | 725 | 42.04% | 76.13% |
| Shuffled positions / primary | 0.01% | 725 | 42.04% | 76.13% |
| PCA / PCA-clustering ablation | 0.21% | 49 | 89.16% | 17.99% |

The table describes seed 42. The PCA and shuffled projections retain the primary assignments in their corresponding rows. Across other seeds, adjusted Rand agreement including unassigned papers ranged from 0.606 to 0.620. 100,784 papers had recognized arXiv subject tags. Shuffled tag sets yielded 27.48% agreement at the display seed.

## Example topics

- **Large language models for recommendation** (1349 papers). [2504.11889](https://www.alphaxiv.org/abs/2504.11889), [2606.16703](https://www.alphaxiv.org/abs/2606.16703), [2311.09049](https://www.alphaxiv.org/abs/2311.09049), [2409.12740](https://www.alphaxiv.org/abs/2409.12740)
- **LLM Agents for Software Engineering** (1010 papers). [2401.07339](https://www.alphaxiv.org/abs/2401.07339), [2505.02133](https://www.alphaxiv.org/abs/2505.02133), [2506.07636](https://www.alphaxiv.org/abs/2506.07636)
- **Vision-language models for autonomous driving** (935 papers). [2510.15446](https://www.alphaxiv.org/abs/2510.15446), [2506.00819](https://www.alphaxiv.org/abs/2506.00819), [2603.18315](https://www.alphaxiv.org/abs/2603.18315)
- **Algebraic geometry and cohomology** (824 papers). [2504.02223](https://www.alphaxiv.org/abs/2504.02223), [1909.01898](https://www.alphaxiv.org/abs/1909.01898), [2304.07181](https://www.alphaxiv.org/abs/2304.07181)

## Coverage and provenance

The collection window was 2026-11-26T14:03:39+00:00 to 2026-11-26T14:27:25+00:00. The independent page sizes were 125 and 175, taking 810 and 579 pages. The embedding matrix has 100,942 rows and 3,072 columns. The inputs contained 26,626,493 tokens. 0 papers used title-only input. The embedding cache supplied 36,275 distinct inputs at the start of the completed embedding invocation. OpenAI embedded 64,666 other inputs. Identical title-and-abstract text occurred in separate paper groups. 100,941 distinct inputs cover 100,942 map points.

Unfiltered pages repeated groups within tied scores. Supplemental queries recovered the skipped IDs. The last qualifying global rank was 101,003 at 11 likes. The next entry had 10 likes. 0 papers had different vote observations in the two accepted passes.

| Page size | Global pages | Initially missing ranks | Supplementary pages | Unresolved ranks |
|---:|---:|---:|---:|---:|
| 125 | 810 | 29,534 | 3,923 | 0 |
| 175 | 579 | 26,735 | 3,612 | 0 |

[First rank certificate](../../results/2026-11-26-over-10/rank-certificate-125.json) · [Second rank certificate](../../results/2026-11-26-over-10/rank-certificate-175.json) · [Collection amendment](collection-amendment.md)

Both editions used 200 UMAP epochs per fit. The larger corpus changes each paper’s potential neighbors, and the two maps have independent coordinate systems.

[Coverage audit](../../results/2026-11-26-over-10/manifest.json) · [Per-seed results](../../results/2026-11-26-over-10/evaluation.json) · [Research protocol](preregistration.md) · [Published dataset](https://huggingface.co/datasets/BurnyCoder/alphaxiv-paper-atlas)
