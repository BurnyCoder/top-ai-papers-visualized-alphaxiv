# Experiment · 2026-11-26-over-50

The 2026-11-26 snapshot contains **10,140 unique papers** above 50 likes and **115 named clusters**. The two accepted passes found the same papers. Of 10,181 entries above the threshold, 41 were marked as external posts. The public map shows all 3,262 unassigned papers in gray.

Across 10 seeds, UMAP retained **18.69%** of the original ten nearest neighbors, compared with **1.42%** under PCA. The gain was 17.28 percentage points (95% seed interval 17.23 to 17.33). Even with UMAP, 81.31% of those neighbors fell outside a paper’s ten closest screen points. Select a paper to recover its original-space recommendations.

Of these papers, **6,437** had 51–100 likes. The two dated editions share 3,703 paper groups. 6,437 groups appear only in the expanded edition and 0 appear only in the earlier one.

| Display / assignments | Recall at 10 | Clusters | Unassigned | Shared subject within a cluster |
|---|---:|---:|---:|---:|
| UMAP / primary | 18.74% | 115 | 32.17% | 80.13% |
| PCA / primary | 1.42% | 115 | 32.17% | 80.13% |
| Shuffled positions / primary | 0.11% | 115 | 32.17% | 80.13% |
| PCA / PCA-clustering ablation | 1.42% | 17 | 82.79% | 43.02% |

[Methods and parameter choices](../../over-50/preregistration.md) · [Per-seed records](../../../results/2026-11-26-over-50/evaluation.json)
