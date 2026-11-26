# Preregistration · 26 November 2026

**Author** Libor “Burny” Burian. This protocol precedes embedding inference, projections, cluster naming and evaluation. Planning probes checked API fields, pagination and the eligibility boundary. The release count comes from the actual crawl.

## Population and unit

Take every research paper returned by the all-time production likes feed with `metrics.public_total_votes > 100`. Set both blog flags to false. Include every subject and alphaXiv-exclusive manuscripts. One unit is a paper group. Traverse zero-based pages of 100 and 50 independently down to a wholly ineligible page or end of feed. Require two consecutive passes with identical eligible group IDs, check page order and retained counts, retry moving pages, and disclose unresolved gaps. Timestamp the interval. Use the latest verified pass for metadata. No like counts, authors, years, subject tags or cluster labels enter the embedding.

## Primary hypothesis

On this frozen corpus the expected mean recall of the original ten nearest paper neighbors is higher under two-dimensional UMAP than under two-dimensional PCA. For each paper exclude itself, rank original vectors by cosine distance and map coordinates by Euclidean distance. Recall is the intersection size divided by ten. Average over all papers. Ties use stable group-ID order.

Compare the difference of the two corpus means at each of seeds 42 through 51. Use the deterministic PCA result in each contrast. Report the seed mean and two-sided 95% Student t interval across ten seeds. A positive lower bound supports the hypothesis. An upper bound at or below zero falsifies the directional prediction for this experiment. Otherwise the result is inconclusive. The interval quantifies algorithmic seed variation conditional on this snapshot. No paper-level independence assumption or field-wide extrapolation is needed.

## Geometry, controls and secondary checks

Use `text-embedding-3-large` at its default 3,072 dimensions on title, a blank line and abstract. Flag title-only fallbacks. Fit cosine UMAP independently in 2D (minimum distance 0.1) and 10D (minimum distance 0), each with 30 neighbors. Use Euclidean HDBSCAN in 10D with minimum cluster size 20, minimum samples 5 (scikit-learn convention including the point), and excess-of-mass selection. Seed 42 is the display realization regardless of evaluation results. Fit PCA by centered full SVD on the same vectors. Independently permute the paper-to-UMAP coordinate mapping once per seed for a control.

Report cluster count, unassigned fraction and adjusted Rand agreement with seed 42, both over all papers and on jointly assigned papers with their coverage. As a secondary check, measure the fraction of tagged, within-cluster paper pairs sharing any official arXiv category, pooled over pairs. Compare with shuffling entire tag sets among eligible tagged papers at each seed, preserving cluster sizes. Report tag coverage. For an ablation, cluster the first ten PCA components with the same HDBSCAN settings. Scores describe this corpus. No labels are treated as an exhaustive scientific taxonomy. No thresholds are changed to obtain a favorable score.

## Naming, release and review

Use GPT-6 Luna only after membership is fixed. Give each cluster characteristic phrases and excerpts from members nearest its centroid in the original normalized embedding space. Validate all cited paper IDs against the examples. Release measured per-seed results, URLs, input hashes, model IDs, frozen vectors, derived coordinates, and both favorable and unfavorable findings. Check site, CSV and snapshot ID equality before deployment. Post-hoc analyses and protocol deviations will be identified separately. [UMAP](https://umap-learn.readthedocs.io/en/latest/clustering.html) · [HDBSCAN conventions](https://scikit-learn.org/stable/modules/generated/sklearn.cluster.HDBSCAN.html) · [Neighborhood fidelity](https://www.nature.com/articles/s42003-022-03628-x)
