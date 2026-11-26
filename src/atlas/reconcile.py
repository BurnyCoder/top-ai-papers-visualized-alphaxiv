"""Reconcile unstable ordering inside large equal-likes groups using the public feed.

A pass is certified only when the distinct paper and external group IDs at EACH
score exactly fill the corresponding number of global ranks. Independent passes
use different page sizes and separate local caches.
"""
import gzip
import hashlib
import json
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from .collect import CATEGORIES, paper_record, scan
from .io import now, save_bytes, save_json


def census_pass(folder,fetch,size,threshold,progress):
    root=folder/"work"/f"feed-{size}"
    def cached(page,limit,topic=None):
        key=hashlib.sha256((topic or "").encode()).hexdigest()[:16]
        path=root/key/f"{limit}-{page}.json.gz"
        if path.exists():return json.loads(gzip.decompress(path.read_bytes()))
        rows=fetch(page,limit,topic)
        # Keep only public fields used by paper_record; raw response headers are never persisted.
        fields=("paper_group_id","universal_paper_id","canonical_id","title","abstract","authors",
                "topics","first_publication_date")
        compact=[]
        for r in rows:
            v={k:r.get(k) for k in fields}
            if not v["authors"]:v["authors"]=[a["full_name"] for a in r.get("full_authors_v2",[]) if a.get("full_name")]
            v["metrics"]={"public_total_votes":r["metrics"]["public_total_votes"]}
            v["external_blog"]=True if r.get("external_blog") is not None or r.get("external_link") is not None else None
            compact.append(v)
        save_bytes(path,gzip.compress(json.dumps(compact,ensure_ascii=False,separators=(",",":")).encode(),compresslevel=1,mtime=0))
        return compact

    papers,audit=scan(cached,size,progress,threshold=threshold,reconcile_ties=True)
    if audit["inversions"]:raise RuntimeError("The reference feed changed order across vote strata")
    expected=Counter(audit["vote_counts"])
    external={e["id"]:e for e in audit["external_entries"]}
    def observed():
        return Counter(p["likes"] for p in papers.values())+Counter(e["likes"] for e in external.values())
    def missing():
        counts=observed()
        if counts-expected:raise RuntimeError(f"Observed more group IDs than ranks at scores {dict(counts-expected)}")
        return expected-counts
    supplements=[]
    audit["global_unique_papers"]=len(papers)
    audit["global_external_occurrences"]=audit["excluded_blogs"]
    def merge(rows,topic):
        for r in rows:
            likes=r["metrics"]["public_total_votes"]
            if likes<=threshold:continue
            key=r["paper_group_id"]
            if r.get("external_blog") is not None:
                external.setdefault(key,dict(id=key,likes=likes,topic=topic))
            else:papers.setdefault(key,paper_record(r))
    def topic_pages(topic):
        # A filtered pass only needs to cover score strata with outstanding global ranks.
        page=0;rows=[]
        while True:
            batch=cached(page,size,topic);page+=1
            rows.extend(r for r in batch if r["metrics"]["public_total_votes"] in wanted)
            if len(batch)<size or batch[-1]["metrics"]["public_total_votes"]<min(wanted):break
        return topic,page,rows
    # Narrow subject feeds have fewer pagination ties. Attend first to the tags most
    # common among the missing score strata, including alphaXiv's own topic labels.
    initial=missing()
    wanted=set(initial)
    frequencies=Counter(t for p in papers.values() if p["likes"] in wanted for t in p["topics"])
    ordered=sorted(frequencies,key=lambda t:(t not in CATEGORIES,-frequencies[t],t))
    def track(source,pages,gain):
        supplements.append(dict(source=source,pages=pages,added_groups=gain))
    for offset in range(0,len(ordered),4):
        if not wanted:break
        with ThreadPoolExecutor(max_workers=4) as pool:
            for topic,pages,rows in pool.map(topic_pages,ordered[offset:offset+4]):
                before=len(external)+len(papers);merge(rows,topic)
                track(topic,pages,len(external)+len(papers)-before)
        needed=missing();wanted=set(needed)
        progress(f"Verify tied ranks · pages of {size}",sum(expected.values())-sum(needed.values()),
                 sum(expected.values()),outstanding=sum(needed.values()),subjects_checked=len(supplements))
        # Use other independent page widths on the remaining global strata before scanning rare tags.
        if offset==12 and wanted:
            for width in ((151,127,181) if size==100 else (137,113,167)):
                high=0;page_ids=set()
                for score,n in sorted(expected.items(),reverse=True):
                    if score in wanted:page_ids.update(range(high//width,(high+n-1)//width+1))
                    high+=n
                before=len(external)+len(papers)
                with ThreadPoolExecutor(max_workers=4) as pool:
                    for batch in pool.map(lambda page:cached(page,width),sorted(page_ids)):merge(batch,None)
                track(f"global page size {width}",len(page_ids),len(external)+len(papers)-before)
                wanted=set(missing())
                if not wanted:break
    remaining=missing()
    certificate=dict(expected_by_score=dict(expected),observed_by_score=dict(observed()),
                     initial_missing=dict(initial),remaining=dict(remaining),supplements=supplements)
    save_json(folder/f"rank-certificate-{size}.json",certificate)
    if remaining:raise RuntimeError(f"Unresolved global ranks at page size {size}: {dict(remaining)}")
    audit.update(eligible=len(papers),excluded_blogs=len(external),external_entries=sorted(external.values(),key=lambda x:x["id"]),
                 ended_at=now(),rank_certificate=f"rank-certificate-{size}.json")
    return papers,audit
