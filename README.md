# Paper Atlas

An interactive map of papers with more than 100 public likes on alphaXiv. Every point is a paper. Similar titles and abstracts place papers close together, and selecting a paper reveals its nearest neighbors in the full embedding space. The project includes every subject exposed by the all-time paper feed.

The collection uses the public vote count and verifies the boundary in two independent passes. OpenAI embeds the texts, UMAP constructs the display, HDBSCAN groups papers in a separate ten-dimensional representation, and GPT-6 Luna names each group from representative papers. The research question is how often a paper's ten closest semantic neighbors remain close in two dimensions. [alphaXiv API](https://api-dev.alphaxiv.org/api.json) · [OpenAI embeddings](https://developers.openai.com/api/docs/guides/embeddings) · [UMAP clustering](https://umap-learn.readthedocs.io/en/latest/clustering.html)

## Study

[Research plan](reports/plan.md) · [Literature review](reports/literature-review.md) · [State of the art](reports/state-of-the-art-review.md) · [Preregistration](reports/preregistration.md) · [Planned runs and controls](reports/planned-runs.md) · [Progress](reports/progress.md)

The inference run and evaluation follow the public preregistration. The release will carry the source snapshot, numerical artifacts and instructions for rebuilding the map without an API key.
