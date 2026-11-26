# Existing implementations and design choices

| Component | Existing work | Choice for this atlas |
|---|---|---|
| Scientific document embeddings | [SPECTER2](https://github.com/allenai/SPECTER2) learns representations from titles, abstracts and citation supervision. | Use the requested hosted [OpenAI text embedding](https://developers.openai.com/api/docs/guides/embeddings). We make no benchmark claim about the two encoders. |
| Topic discovery | [BERTopic](https://arxiv.org/pdf/2203.05794) uses modular embeddings, dimensionality reduction, density clustering and class-based term weighting. | Use the UMAP and HDBSCAN libraries directly. Select distinctive phrases with a transparent cluster-level TF–IDF calculation. |
| Naming | [Murray et al.](https://arxiv.org/html/2511.02601v1) investigate generative labels grounded in cluster characteristics. | Give [GPT-6 Luna](https://developers.openai.com/api/docs/models/gpt-6-luna) characteristic phrases and representative papers. Store the prompt and the IDs supporting the returned name. |
| Interactive maps | [DataMapPlot's scientific paper example](https://datamapplot.readthedocs.io/en/latest/selection_and_filtering.html) combines point selection with filtering. | Build a static, searchable map with coordinated filters, a keyboard-operable paper list and exact original-space neighbors. |
| Projection fidelity | [A comparative evaluation](https://www.nature.com/articles/s42003-022-03628-x) measures local neighbor preservation. | Compare UMAP with PCA and shuffled coordinates, using exactly the same collection and reference neighbors. |

The contribution is a dated, auditable atlas of alphaXiv's highly liked papers with inspectable supporting examples, downloadable vectors and a quantified fidelity comparison. We use established algorithms and make no claim of algorithmic novelty.

The expanded census uses exact Euclidean tree queries for two-dimensional recall, with exhaustive stable ordering when distances tie at the inclusion boundary. The original-space calculation still evaluates every cosine similarity. These changes accelerate evaluation while preserving the original metric. [SciPy cKDTree query](https://docs.scipy.org/doc/scipy/reference/generated/scipy.spatial.cKDTree.query.html) · [CuPy matrix multiplication](https://docs.cupy.dev/en/stable/reference/generated/cupy.matmul.html)
