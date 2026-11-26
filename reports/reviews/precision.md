# Numerical precision follow-up

An independent float64 calculation detected a close boundary in the original float32 cosine ranking. The archived comparison identifies the query, both candidate IDs and their double-precision similarities. The release ranks the stored vectors in float64 for recommendations and primary evaluation. The numerical fix was applied uniformly to every paper before release. It required no new hosted inference.

The UMAP input graph, fitted layouts, assignments, cluster names and seeds retain their original definitions. The affected primary and control metrics were recalculated from cached coordinates. The initial evaluation and audit are archived for comparison. [Observed boundary](../../results/2026-11-26/precision-check/boundary.json) · [Initial audit](../../results/2026-11-26/precision-check/audit.json) · [Final audit](../../results/2026-11-26/audit.json)
