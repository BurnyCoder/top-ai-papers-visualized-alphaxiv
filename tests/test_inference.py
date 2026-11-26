"""An interrupted hosted run must not reissue completed embedding batches."""
from types import SimpleNamespace
import numpy as np
import pytest
from atlas import inference


def test_resume_cache_and_title_only(tmp_path, monkeypatch):
    folder = tmp_path / "run"
    folder.mkdir()
    monkeypatch.setattr(inference, "CACHE", tmp_path/"cache")
    assert inference.paper_text({"title":"A","abstract":""}) == "A"
    items = [{"title":f"Paper {i}", "abstract":"Methods"} for i in range(65)]
    class Usage:
        total_tokens = 12
        def model_dump(self):
            return {"total_tokens":12}
    class Fake:
        def __init__(self):
            self.embeddings = self
            self.sizes = []
        def create(self, **kw):
            self.sizes.append(len(kw["input"]))
            if len(self.sizes) == 2:
                raise RuntimeError("interrupted")
            vector = np.ones(inference.DIM).tolist()
            return SimpleNamespace(data=[SimpleNamespace(index=i,embedding=vector) for i in range(self.sizes[-1])],
                                   model=inference.EMBEDDER,usage=Usage())
    client = Fake()
    progress = lambda *_a,**_k: None
    with pytest.raises(RuntimeError, match="interrupted"):
        inference.embed(folder,items,progress,client)
    v = inference.embed(folder,items,progress,client)
    assert client.sizes == [64,1,1]
    assert v.shape == (65,inference.DIM)
    assert np.allclose(np.linalg.norm(v,axis=1),1)
