# Learnings · 2026-11-26-over-50

The strict cutoff by rank included 41 externally marked posts. Checking each record’s type reconciled the feed rank and the paper count.

UMAP’s 17.28 percentage points (95% seed interval 17.23 to 17.33) gain measures local neighborhood fidelity. The lost-neighbor fraction motivates the separate recommendation list. At seed 42 the ten-PC ablation assigned 17.21% of papers, compared with 67.83% for ten-dimensional UMAP. Shared subject agreement among assigned and tagged pairs was 43.02% and 80.13%, respectively. These are conditional comparisons because the assigned sets can differ. The evaluation uses the frozen corpus and held-out tags.

UMAP's default optimization budget was 200 epochs here and 500 in the earlier edition. The rule depends on corpus size. Each edition has an independently fitted coordinate system. Cross-edition differences in recall can reflect the corpus and the optimization budget. [UMAP implementation](https://umap-learn.readthedocs.io/en/latest/_modules/umap/umap_.html#simplicial_set_embedding)
