# Planned runs

| Order | Run | Input and method | Outcome |
|---|---|---|---|
| 1 | Census | Authenticated alphaXiv all-time likes, page sizes 100 and 50, group deduplication | Frozen membership, cutoff pages and audit |
| 2 | Hosted embeddings | OpenAI text-embedding-3-large, title and abstract, full default vector | Cached vectors and ten original-space neighbors |
| 3 | Display | UMAP 2D and independent UMAP 10D → HDBSCAN, seed 42 | Coordinates, memberships, unassigned papers |
| 4 | Labels | GPT-6 Luna, representative texts and phrases from each assigned cluster | Short names and validated evidence IDs |
| 5 | Comparisons | PCA 2D, shuffled coordinates, PCA 10D → HDBSCAN ablation | Baselines, control and category agreement |
| 6 | Sensitivity | Identical embedding matrix, seeds 43–51, the same parameters | Variation in fidelity, assignment and agreement |
| 7 | Release | Offline rebuild, browser tests and count reconciliation | Public explorer, dataset, paper and reproducible figures |

The run fits numerical projections and clusters. Embedding and language-model inference are hosted. Timing and actual API usage are logged during the run. [Full hypothesis and analysis plan](preregistration.md)
