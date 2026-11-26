# Release review · 2026-11-26-over-10

## Independent scientific checks

Two complete feed passes agreed on all 100,942 research-paper group IDs. Both crossed the strict boundary, with no observed inversion. The JSONL, static map and CSV contain those IDs in the same order. The build independently round-trips the Parquet IDs too. All archived SHA-256 digests verified.

Recomputing all nearest neighbors with scikit-learn in float64 recovered 100.000000% of the published top-ten entries. The complete ordered neighbor lists matched for 100.000000% of papers. The archived vectors are float32 and the ranking uses float64 arithmetic. The maximum absolute vector-norm error was 1.79e-07. A separate kd-tree implementation reproduced the display-seed UMAP, PCA and shuffled recall values (0.089619, 0.002074, 0.000101), plus UMAP and shuffled recall for all 10 archived layouts. An independent Student t calculation reproduced the registered interval. All 725 assigned groups have valid evidence from their own members.

## Interpretation and limitations

The procedure samples highly liked public research papers from a non-atomic feed and measures compression of a hosted representation. It cannot establish research quality, a community-wide topic distribution, or causal differences between fields. Shared tags may reflect broad fields and cross-listing. The 95% interval describes optimizer seed variation on this corpus. Pairs are dependent and larger clusters contribute more pairs to the subject statistic.

There were 0 repeated topic names beyond their first occurrence. The browser distinguishes those clusters by group ID while preserving Luna’s source response. Unassigned papers retain metadata and recommendations. The source-space control and PCA ablation are included even when their behavior is less useful for browsing.

## Engineering checks

API keys are read in the local pipeline. Model instructions and paper text remain outside the static code path. Browser-facing paper text is assigned through textContent. Completed embedding batches and labels survive interruption. Both the raw measurements and the standalone build are versioned. The regression and real-browser checks are documented in the reproduction guide. Pair counts from sparse subject incidence matrices and an independent adjusted Rand calculation reproduced the real and shuffled subject counts and cluster stability for all 10 seeds. Decimal repricing of 1233 usage receipts reproduced USD 2.3227. The independent sum of all 1233 pre-transmission reservations stayed under the registered cap. [OpenAI standard rates](https://developers.openai.com/api/docs/pricing)

[Raw audit](../../../results/2026-11-26-over-10/audit.json) · [Per-seed results](../../../results/2026-11-26-over-10/evaluation.json) · [Preregistration](../preregistration.md)
