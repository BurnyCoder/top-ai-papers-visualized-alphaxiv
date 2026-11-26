# Snapshot summary · 2026-11-26

The 2026-11-26 snapshot contains **3,703 unique papers** and **56 named topics**. Both passes found the same papers. Of 3,723 entries above the threshold, 20 were marked as external posts. The public map shows all 1,242 unassigned papers in gray.

Across 10 seeds, UMAP retained **26.34%** of the original ten nearest neighbors, compared with **2.86%** under PCA. The gain was 23.49 percentage points (95% seed interval 23.36 to 23.61). Even with UMAP, 73.66% of those neighbors fell outside a paper’s ten closest screen points. Select a paper to recover its original-space recommendations.

## Display seed and controls

| Display / assignments | Recall at 10 | Clusters | Unassigned | Shared subject within a cluster |
|---|---:|---:|---:|---:|
| UMAP / primary | 26.29% | 56 | 33.54% | 70.36% |
| PCA / primary | 2.86% | 56 | 33.54% | 70.36% |
| Shuffled positions / primary | 0.24% | 56 | 33.54% | 70.36% |
| PCA / PCA-clustering ablation | 2.86% | 10 | 75.21% | 68.66% |

The table describes seed 42. The PCA and shuffled projections retain the primary assignments in their corresponding rows. Across other seeds, adjusted Rand agreement including unassigned papers ranged from 0.498 to 0.642. 3,690 papers had recognized arXiv subject tags. Shuffled tag sets yielded 48.22% agreement at the display seed.

## Example topics

- **Quantum many-body dynamics** (139 papers). [2403.00091](https://www.alphaxiv.org/abs/2403.00091), [2505.09707](https://www.alphaxiv.org/abs/2505.09707), [2503.23475](https://www.alphaxiv.org/abs/2503.23475), [2506.06994](https://www.alphaxiv.org/abs/2506.06994)
- **Efficient attention for LLM inference** (132 papers). [2505.21487](https://www.alphaxiv.org/abs/2505.21487), [2504.06319](https://www.alphaxiv.org/abs/2504.06319), [2410.10819](https://www.alphaxiv.org/abs/2410.10819)
- **Adversarial attacks on LLM safety** (87 papers). [2503.21598](https://www.alphaxiv.org/abs/2503.21598), [2504.00218](https://www.alphaxiv.org/abs/2504.00218), [2307.15043](https://www.alphaxiv.org/abs/2307.15043)
- **Reinforcement learning for LLM reasoning** (85 papers). [2506.14245](https://www.alphaxiv.org/abs/2506.14245), [2503.16219](https://www.alphaxiv.org/abs/2503.16219), [2501.12948](https://www.alphaxiv.org/abs/2501.12948)

## Coverage and provenance

The collection window was 2026-11-26T11:13:01+00:00 to 2026-11-26T11:14:03+00:00. The independent page sizes were 100 and 50, taking 39 and 76 pages. The embedding matrix has 3,703 rows and 3,072 columns. The inputs contained 1,018,152 tokens. 0 papers used title-only input.

[Coverage audit](../results/2026-11-26/manifest.json) · [Per-seed results](../results/2026-11-26/evaluation.json) · [Research protocol](preregistration.md) · [Published dataset](https://huggingface.co/datasets/BurnyCoder/alphaxiv-paper-atlas)
