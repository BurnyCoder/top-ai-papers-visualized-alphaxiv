# Experiment · 2026-11-26

The 2026-11-26 snapshot contains **3,703 unique papers** and **56 named topics**. Both passes found the same papers. Of 3,723 entries above the threshold, 20 were marked as external posts. The public map shows all 1,242 unassigned papers in gray.

Across 10 seeds, UMAP retained **26.34%** of the original ten nearest neighbors, compared with **2.86%** under PCA. The gain was 23.49 percentage points (95% seed interval 23.36 to 23.61). Even with UMAP, 73.66% of those neighbors fell outside a paper’s ten closest screen points. Select a paper to recover its original-space recommendations.

| Display / assignments | Recall at 10 | Clusters | Unassigned | Shared subject within a cluster |
|---|---:|---:|---:|---:|
| UMAP / primary | 26.29% | 56 | 33.54% | 70.36% |
| PCA / primary | 2.86% | 56 | 33.54% | 70.36% |
| Shuffled positions / primary | 0.24% | 56 | 33.54% | 70.36% |
| PCA / PCA-clustering ablation | 2.86% | 10 | 75.21% | 68.66% |

[Methods and parameter choices](../../preregistration.md) · [Per-seed records](../../../results/2026-11-26/evaluation.json)
