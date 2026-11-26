"""Reconcile unstable ordering inside large equal-likes groups using the public feed.

A pass is certified only when the distinct paper and external group IDs at EACH
score exactly fill the corresponding number of global ranks. Independent passes
use different page sizes and separate local caches.
"""
import gzip
import hashlib
import json
from collections import Counter, defaultdict, deque
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from .collect import CATEGORIES, paper_record, scan
from .io import RESULTS, census_path, now, papers_at, save_bytes, save_json
from .editions import PREVIOUS


def assign_observed_scores(canonical,alternates,expected):
    """Match group IDs to rank capacities using only scores observed for that same ID.

    Most groups have one score and need no matching. Augmenting paths move groups with
    documented vote changes to an alternative observation, preserving their identities.
    """
    counts=Counter(canonical.values());assigned={};moves=defaultdict(set)
    for key,options in alternates.items():
        if key in canonical:
            for other in options-{canonical[key]}:moves[canonical[key]].add((key,other))
    for start in list(counts-expected):
        while counts[start]>expected[start]:
            queue=deque([start]);via={start:None};end=None
            while queue and end is None:
                at=queue.popleft()
                for key,dest in sorted(moves[at]):
                    if dest in via or assigned.get(key,canonical[key])!=at:continue
                    via[dest]=(at,key)
                    if counts[dest]<expected[dest]:end=dest;break
                    queue.append(dest)
            if end is None:break
            counts[start]-=1;counts[end]+=1
            while end!=start:
                previous,key=via[end];assigned[key]=end
                for other in (alternates[key]|{canonical[key]})-{end}:moves[end].add((key,other))
                end=previous
    changes=[dict(id=k,displayed=canonical[k],rank_score=s) for k,s in sorted(assigned.items()) if canonical[k]!=s]
    return counts,changes


def census_pass(folder,fetch,size,threshold,progress):
    root=folder/"work"/f"feed-{size}"
    root.mkdir(parents=True,exist_ok=True)
    window=root/"started-at.txt"
    if not window.exists():
        old=min((f.stat().st_mtime for f in root.glob("*/*.json.gz")),default=None)
        first=datetime.fromtimestamp(old,timezone.utc).isoformat(timespec="seconds") if old else now()
        save_bytes(window,first.encode())
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

    last=None
    if threshold==10:
        # Bracket a real stopping page before allowing arbitrarily long runs of tied rows.
        def below(page):
            batch=cached(page,size)
            return not batch or max(r["metrics"]["public_total_votes"] for r in batch)<=threshold
        lo,hi=-1,1
        while not below(hi):
            lo,hi=hi,hi*2
            if hi>2**20:raise RuntimeError("Could not locate a cutoff on the public feed")
        while hi-lo>1:
            mid=(hi+lo)//2
            if below(mid):hi=mid
            else:lo=mid
        last=hi
        with ThreadPoolExecutor(4) as pool:
            for start in range(0,last+1,24):
                pages=range(start,min(start+24,last+1))
                for _ in pool.map(lambda page:len(cached(page,size)),pages):pass
                progress(f"Collect global pages · {size}",pages.stop,last+1)
    papers,audit=scan(cached,size,progress,threshold=threshold,reconcile_ties=True,final_page=last)
    if audit["inversions"]:raise RuntimeError("The reference feed changed order across vote strata")
    expected=Counter(audit["vote_counts"])
    external={e["id"]:e for e in audit["external_entries"]}
    historical=RESULTS/PREVIOUS[threshold][0]
    prior={p["id"]:p["likes"] for p in papers_at(historical)} if census_path(historical).exists() else {}
    alternates=defaultdict(set);sources={}
    def observe_score(key,likes,canonical):
        if likes!=canonical:
            alternates[key].add(likes)
            sources[key,likes]="additional public feed observation"
        if key in prior and prior[key]!=canonical and prior[key]>threshold:
            alternates[key].add(prior[key])
            sources.setdefault((key,prior[key]),f"previous dated over-{PREVIOUS[threshold][1]} census")
    for key,paper in papers.items():observe_score(key,paper["likes"],paper["likes"])
    def proof():
        canonical={k:p["likes"] for k,p in papers.items()}
        if papers.keys() & external.keys():raise RuntimeError("Group changed between external and paper types")
        canonical.update({k:p["likes"] for k,p in external.items()})
        counts,changes=assign_observed_scores(canonical,alternates,expected)
        for move in changes:move["source"]=sources.get((move["id"],move["rank_score"]),"primary feed")
        return Counter(canonical.values()),counts,changes
    def missing():
        _,counts,_=proof()
        return (expected-counts)+(counts-expected)
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
                observe_score(key,likes,external[key]["likes"])
            else:
                if key not in papers:papers[key]=paper_record(r)
                observe_score(key,likes,papers[key]["likes"])
    def topic_pages(topic):
        # A filtered pass only needs to cover score strata with outstanding global ranks.
        page=0;rows=[]
        while True:
            batch=cached(page,size,topic);page+=1
            rows.extend(r for r in batch if r["metrics"]["public_total_votes"]>threshold)
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
                 sum(expected.values()),outstanding=sum(needed.values()),scores_remaining=sorted(needed),sources_checked=len(supplements))
        # Use other independent page widths on the remaining global strata before scanning rare tags.
        if offset in (12,40,96) and wanted:
            widths=({12:(151,127,181),40:(199,191,179,157,139,109),96:(189,177,153,129,111)} if size in (100,125) else
                    {12:(137,113,167),40:(197,193,173,163,131,107),96:(187,169,159,141,103)})
            for width in widths[offset]:
                high=0;page_ids=set()
                for score,n in sorted(expected.items(),reverse=True):
                    if score in wanted:page_ids.update(range(high//width,(high+n-1)//width+1))
                    high+=n
                before=len(external)+len(papers)
                with ThreadPoolExecutor(max_workers=4) as pool:
                    for batch in pool.map(lambda page:cached(page,width),sorted(page_ids)):merge(batch,None)
                track(f"global page size {width}",len(page_ids),len(external)+len(papers)-before)
                wanted=set(missing())
                progress(f"Verify tied ranks · pages of {size}",sum(expected.values())-sum(missing().values()),
                         sum(expected.values()),width=width,scores_remaining=sorted(wanted))
                if not wanted:break
    remaining=missing()
    actual,matched,changes=proof()
    certificate=dict(expected_by_score=dict(expected),observed_by_score=dict(actual),
                     matched_by_score=dict(matched),score_observations_used=changes,
                     initial_missing=dict(initial),remaining=dict(remaining),supplements=supplements)
    save_json(folder/f"rank-certificate-{size}.json",certificate)
    if remaining:raise RuntimeError(f"Unresolved global ranks at page size {size}: {dict(remaining)}")
    audit.update(eligible=len(papers),excluded_blogs=len(external),external_entries=sorted(external.values(),key=lambda x:x["id"]),
                 started_at=window.read_text(),
                 ended_at=now(),rank_certificate=f"rank-certificate-{size}.json")
    return papers,audit
