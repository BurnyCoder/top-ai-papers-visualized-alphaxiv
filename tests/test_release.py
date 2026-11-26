"""Check the frozen export contract independently of live network and hosted models."""
import csv
import gzip
import json
import numpy as np
import pytest
from atlas.publish import export_data
from atlas.catalog import local_catalog


@pytest.mark.parametrize("threshold",[10,20,50,100])
def test_all_eligible_groups_exported_in_order(tmp_path,threshold):
    papers=[dict(id=str(i),paper_id=str(i),title=str(i),likes=threshold+1,abstract="x") for i in range(12)]
    knn=np.array([[i]+[j for j in range(12) if j!=i][:10] for i in range(12)])
    geo=dict(neighbors=knn[:,1:11],xy=np.zeros((12,2)),labels=np.full(12,-1),strength=np.zeros(12),
             pca=np.arange(36).reshape(12,3))
    docs=tmp_path/"docs";docs.mkdir()
    manifest=dict(count=12,ended_at="2026-11-26",threshold_exclusive=threshold)
    evaluation={"seeds":[dict(seed=42,umap_recall=.2,pca_recall=.1,shuffled_recall=.01)]}
    export_data(tmp_path,docs,manifest,papers,geo,{},evaluation)
    site=local_catalog(docs)
    if threshold==10:
        assert site["paper_parts"]==["points/0.json"] and site["paper_count"]==12
        controls=json.loads((docs/site["controls"]["file"]).read_bytes())
        np.testing.assert_array_equal(controls["pca"],geo["pca"][:,:2])
        assert controls["shuffled"]==np.random.default_rng(42).permutation(12).tolist()
    name=site.get("csv","papers.csv")
    with (gzip.open if name.endswith(".gz") else open)(docs/name,"rt",encoding="utf-8-sig",newline="") as f:rows=list(csv.DictReader(f))
    if threshold<=20:
        assert json.loads((docs/"abstracts"/"0.json").read_text())==[p["abstract"] for p in papers]
        assert all("abstract" not in p for p in site["papers"])
    assert [r["id"] for r in rows]==[p["id"] for p in site["papers"]]==[p["id"] for p in papers]
    assert site["unassigned"]==12 and all(len(p["neighbors"])==10 for p in site["papers"])
    assert site["threshold_exclusive"]==threshold
    papers[0]["likes"]=threshold
    with pytest.raises(ValueError,match="threshold"):export_data(tmp_path,docs,manifest,papers,geo,{})
