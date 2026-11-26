# Expanded census run matrix

| Phase | Inputs and fixed choices | Output |
|---|---|---|
| Verify membership | All-time feed, public votes above 50, independent page sizes 100 and 50 | Dated group IDs, cutoff and pass reconciliation |
| Represent text | Cached or new OpenAI text-embedding-3-large vectors for title and abstract | Frozen matrix and exact cosine top ten |
| Fit geometry | Separate UMAP 2D and 10D, cosine, 30 neighbors, min_dist 0.1 and 0, seed 42 | Map and HDBSCAN groups with minimum size 20 and min_samples 5 |
| Name topics | GPT-6 Luna, central examples and distinctive terms from these new groups | Topic names and evidence IDs |
| Evaluate | Seeds 42–51, 2D PCA, seed-wise shuffled positions, 10D PCA clustering and shuffled subject tags | Recall, paired interval, assignment coverage and stability |
| Publish | Independent geometry and coverage audit plus desktop and mobile tests | Searchable Pages atlas, versioned dataset, figures and paper |

This extension uses the earlier [literature review](../literature-review.md) and [implementation comparison](../state-of-the-art-review.md). The corpus selection changes; the model, geometry and evaluation definitions follow the [registered extension](preregistration.md). [UMAP's clustering guide](https://umap-learn.readthedocs.io/en/latest/clustering.html) · [Scientific document label evaluation](https://arxiv.org/html/2511.02601v1)
