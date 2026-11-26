"""Price only previously uncached input tokens before the first hosted call for a snapshot."""
import sqlite3
import sys
import tiktoken
from atlas.budget import RATES
from atlas.inference import EMBEDDER, digest, paper_text
from atlas.io import CACHE, RESULTS, papers_at, save_json


def estimate(folder):
    target=folder/"budget-preflight.json"
    if target.exists():raise ValueError("This snapshot already has a frozen preflight")
    documents={digest(EMBEDDER+"\0"+paper_text(p)):paper_text(p) for p in papers_at(folder)}
    cache=CACHE/"embeddings.sqlite3"
    known=set()
    if cache.exists():
        with sqlite3.connect(f"{cache.as_uri()}?mode=ro",uri=True) as db:
            known={key for key, in db.execute("SELECT key FROM embeddings")}
    missing=documents.keys()-known
    encoder=tiktoken.get_encoding("cl100k_base")
    tokens=sum(len(encoder.encode_ordinary(documents[key])) for key in missing)
    forecast=dict(distinct_inputs=len(documents),cached_inputs=len(documents)-len(missing),new_inputs=len(missing),
                  new_tokens=tokens,estimated_embedding_usd=tokens*RATES["embedding"]/1e6,
                  basis="No retries, standard endpoint. Cluster label costs are metered separately.")
    save_json(target,forecast)
    print(forecast)


if __name__=="__main__":estimate(RESULTS/sys.argv[1])
