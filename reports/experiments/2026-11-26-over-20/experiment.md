# Experiment · 2026-11-26-over-20

The 2026-11-26 snapshot contains **36,276 unique papers** above 20 likes and **313 named clusters**. The two accepted passes found the same papers. Of 36,329 entries above the threshold, 53 were marked as external posts. The public map shows all 13,787 unassigned papers in gray.

Across 10 seeds, UMAP retained **12.81%** of the original ten nearest neighbors, compared with **0.49%** under PCA. The gain was 12.32 percentage points (95% seed interval 12.27 to 12.37). Even with UMAP, 87.19% of those neighbors fell outside a paper’s ten closest screen points. Select a paper to recover its original-space recommendations. Shuffling the paper-to-position assignment retained 0.03% across the same seeds.

Of these papers, **26,136** had 21–50 likes. The two dated editions share 10,140 paper groups. 26,136 groups appear only in the expanded edition and 0 appear only in the earlier one.

OpenAI usage receipts priced at standard rates total **USD 0.9687** for this edition. The ledger reserved USD 14.4372 against the USD 50.00 ceiling. Attempts without a usage receipt: 0. [Credit ledger](https://github.com/BurnyCoder/top-ai-papers-visualized-alphaxiv/blob/main/results/2026-11-26-over-20/budget.json)

| Display / assignments | Recall at 10 | Clusters | Unassigned | Shared subject within a cluster |
|---|---:|---:|---:|---:|
| UMAP / primary | 12.87% | 313 | 38.01% | 79.95% |
| PCA / primary | 0.49% | 313 | 38.01% | 79.95% |
| Shuffled positions / primary | 0.03% | 313 | 38.01% | 79.95% |
| PCA / PCA-clustering ablation | 0.49% | 21 | 86.65% | 37.19% |

[Methods and parameter choices](../../over-20/preregistration.md) · [Per-seed records](../../../results/2026-11-26-over-20/evaluation.json)
