"""Check the frozen export contract independently of live network and hosted models."""
import csv
import json
import numpy as np
from atlas.publish import export_data


def test_all_eligible_groups_exported_in_order(tmp_path):
    papers=[dict(id=str(i),paper_id=str(i),title=str(i),likes=101,abstract="x") for i in range(12)]
    knn=np.array([[i]+[j for j in range(12) if j!=i][:10] for i in range(12)])
    geo=dict(neighbors=knn[:,1:11],xy=np.zeros((12,2)),labels=np.full(12,-1),strength=np.zeros(12))
    docs=tmp_path/"docs";docs.mkdir()
    export_data(tmp_path,docs,dict(count=12,ended_at="2026-11-26"),papers,geo,{})
    site=json.loads((docs/"atlas.json").read_text())
    with (docs/"papers.csv").open(encoding="utf-8-sig",newline="") as f: rows=list(csv.DictReader(f))
    assert [r["id"] for r in rows]==[p["id"] for p in site["papers"]]==[p["id"] for p in papers]
    assert site["unassigned"]==12 and all(len(p["neighbors"])==10 for p in site["papers"])
