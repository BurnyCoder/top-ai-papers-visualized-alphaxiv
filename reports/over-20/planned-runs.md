# Over-20 run matrix

| Phase | Inputs and fixed settings | Deliverable |
|---|---|---|
| Census | All-time public feed, independent pagination, strict 20/21 boundary | Dated IDs, vote boundary, duplicate and external-entry counts |
| Representation | Cached unchanged inputs, new text-embedding-3-large vectors | Complete frozen embedding matrix, usage and durable credit reservations |
| Map and topics | Cosine UMAP in two and ten dimensions, seed 42, HDBSCAN in ten dimensions | All-paper coordinates, assignments, exact full-space neighbors |
| Naming | GPT-6 Luna, centroid-near examples and corpus-derived terms | Validated paper evidence for each name |
| Evaluation | Seeds 42–51, 2D PCA and shuffled-position controls, 10D PCA ablation, held-out arXiv tags | Paired interval, stability, assignment coverage and topic agreement |
| Release | Match raw, map, CSV and Parquet identities, independently check neighbors and browser interactions | New Pages edition, numerical dataset, paper, cost report and reproducible offline build |

This study extends the [literature review](../literature-review.md) and [implementation review](../state-of-the-art-review.md). Established algorithms and model settings carry forward. The additional engineering addresses the larger corpus and the hard spending limit. [Preregistration](preregistration.md) · [OpenAI rates](https://developers.openai.com/api/docs/pricing) · [SciPy exact search](https://docs.scipy.org/doc/scipy/reference/generated/scipy.spatial.cKDTree.query.html)
