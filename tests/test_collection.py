"""Check the scientific unit, public score and independent pagination."""
import pytest
from atlas.collect import scan, verify_passes, paper_record, collect


def raw(group, votes, version="v1", abstract="Some abstract", blog=False):
    return {"paper_group_id": group, "universal_paper_id": group, "canonical_id": group + version,
            "metrics": {"public_total_votes": votes, "total_votes": 999}, "title": group,
            "abstract": abstract, "authors": ["A"], "topics": ["cs.AI", "optics"],
            "external_blog": {} if blog else None, "external_link": None}


def test_cutoff_versions_blog_and_page_ties():
    items = [raw("a", 105), raw("b", 101), raw("b", 101, "v2"), raw("c", 101, abstract=""),
             raw("blog", 101, blog=True), raw("d", 100), raw("e", 100), raw("f", 99)]
    def fetch(page, size):
        return items[page * size:(page + 1) * size]
    papers, audit = scan(fetch, 2)
    assert set(papers) == {"a", "b", "c"}
    assert audit["duplicates"] == 1 and audit["last_page"]["max_likes"] == 100
    assert papers["c"]["title_only"] and papers["b"]["subjects"] == ["cs.AI"]
    assert verify_passes(papers, scan(fetch, 3)[0]) == {"added": [], "removed": []}


def test_drift_is_explicit_and_exclusives_survive():
    assert verify_passes({"a": 1}, {"b": 1}) == {"added": ["b"], "removed": ["a"]}
    assert paper_record(raw("2611.some-exclusive", 101))["paper_id"] == "2611.some-exclusive"


def test_fifty_is_exclusive_with_a_tie_across_pages():
    rows=[raw("a",91),raw("b",51),raw("b",51,"v2"),raw("external",51,blog=True),
          raw("exclusive",51,abstract=""),raw("cutoff",50),raw("also50",50),raw("under",49)]
    def fetch(page,size):return rows[page*size:(page+1)*size]
    papers,audit=scan(fetch,2,threshold=50)
    assert set(papers)=={"a","b","exclusive"} and papers["exclusive"]["title_only"]
    assert audit["boundary"]["last_above"]["rank"]==5
    assert audit["boundary"]["first_at_or_below"]["likes"]==50
    assert audit["excluded_blogs"]==audit["duplicates"]==1
    assert not any(verify_passes(papers,scan(fetch,3,threshold=50)[0]).values())


def test_frozen_census_rejects_another_cutoff(tmp_path):
    (tmp_path/"manifest.json").write_text('{"threshold_exclusive":100}')
    (tmp_path/"papers.jsonl").write_text("")
    with pytest.raises(ValueError,match="different threshold"):collect(tmp_path,lambda *_:None,50)
