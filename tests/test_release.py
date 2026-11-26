"""Check the frozen export contract independently of live network and hosted models."""
import csv
import json
import numpy as np
import pytest
from atlas.publish import export_data


@pytest.mark.parametrize("threshold",[50,100])
def test_all_eligible_groups_exported_in_order(tmp_path,threshold):
    papers=[dict(id=str(i),paper_id=str(i),title=str(i),likes=threshold+1,abstract="x") for i in range(12)]
    knn=np.array([[i]+[j for j in range(12) if j!=i][:10] for i in range(12)])
    geo=dict(neighbors=knn[:,1:11],xy=np.zeros((12,2)),labels=np.full(12,-1),strength=np.zeros(12))
    docs=tmp_path/"docs";docs.mkdir()
    manifest=dict(count=12,ended_at="2026-11-26",threshold_exclusive=threshold)
    export_data(tmp_path,docs,manifest,papers,geo,{})
    site=json.loads((docs/"atlas.json").read_text())
    with (docs/"papers.csv").open(encoding="utf-8-sig",newline="") as f: rows=list(csv.DictReader(f))
    assert [r["id"] for r in rows]==[p["id"] for p in site["papers"]]==[p["id"] for p in papers]
    assert site["unassigned"]==12 and all(len(p["neighbors"])==10 for p in site["papers"])
    assert site["threshold_exclusive"]==threshold
    papers[0]["likes"]=threshold
    with pytest.raises(ValueError,match="threshold"):export_data(tmp_path,docs,manifest,papers,geo,{})
