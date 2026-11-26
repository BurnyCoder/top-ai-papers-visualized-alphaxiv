# Experiment · 2026-11-26-over-10

The 2026-11-26 snapshot contains **100,942 unique papers** above 10 likes and **725 named clusters**. The two accepted passes found the same papers. Of 101,003 entries above the threshold, 61 were marked as external posts. The public map shows all 42,441 unassigned papers in gray.

Across 10 seeds, UMAP retained **8.99%** of the original ten nearest neighbors, compared with **0.21%** under PCA. The gain was 8.78 percentage points (95% seed interval 8.70 to 8.86). Even with UMAP, 91.01% of those neighbors fell outside a paper’s ten closest screen points. Select a paper to recover its original-space recommendations. Shuffling the paper-to-position assignment retained 0.01% across the same seeds.

Of these papers, **64,662** had 11–20 likes. The two dated editions share 36,276 paper groups. 64,666 groups appear only in the expanded edition and 0 appear only in the earlier one.

OpenAI usage receipts priced at standard rates total **USD 2.3227** for this edition. The ledger reserved USD 8.7512 against the USD 50.00 ceiling. Attempts without a usage receipt: 0. [Credit ledger](https://github.com/BurnyCoder/top-ai-papers-visualized-alphaxiv/blob/main/results/2026-11-26-over-10/budget.json)

| Display / assignments | Recall at 10 | Clusters | Unassigned | Shared subject within a cluster |
|---|---:|---:|---:|---:|
| UMAP / primary | 8.96% | 725 | 42.04% | 76.13% |
| PCA / primary | 0.21% | 725 | 42.04% | 76.13% |
| Shuffled positions / primary | 0.01% | 725 | 42.04% | 76.13% |
| PCA / PCA-clustering ablation | 0.21% | 49 | 89.16% | 17.99% |

[Methods and parameter choices](../../over-10/preregistration.md) · [Per-seed records](../../../results/2026-11-26-over-10/evaluation.json)
