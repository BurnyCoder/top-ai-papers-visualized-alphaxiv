"""Census of the public, all-time alphaXiv likes feed. API schema: https://api-dev.alphaxiv.org/api.json"""
from __future__ import annotations

import hashlib
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor
from .editions import CAPPED, CURRENT_THRESHOLD

import httpx
from .io import LOG, PACKAGE, now, read_json, save_json, census_digest, census_path, write_census

FEED = "https://api.alphaxiv.org/papers/v3/feed"
CATEGORIES = set((PACKAGE / "categories.txt").read_text(encoding="utf-8").splitlines())
QUERY = dict(sort="Likes", interval="All time", includeExternalBlogs="false", linkBlogs="false")


def paper_record(item):
    """Keep author-supplied bibliographic fields and group identity, including non-arXiv IDs."""
    title = item["title"].strip()
    if not title:
        raise ValueError(f"Missing title for {item['paper_group_id']}")
    abstract = (item.get("abstract") or "").strip()
    topics = sorted(set(item.get("topics") or []))
    authors = item.get("authors") or [a["full_name"] for a in item.get("full_authors_v2", []) if a.get("full_name")]
    return dict(id=item["paper_group_id"], paper_id=item["universal_paper_id"], version=item.get("canonical_id"),
                title=title, abstract=abstract, title_only=not abstract, authors=authors, topics=topics,
                subjects=sorted(CATEGORIES.intersection(topics)), date=(item.get("first_publication_date") or "")[:10],
                likes=item["metrics"]["public_total_votes"])


def scan(fetch, size, report=lambda *_args, **_kw: None, *, threshold=100, reconcile_ties=False, final_page=None):
    """Finish beyond the threshold, checking monotonic ordering over all returned rows."""
    papers, pages = {}, []
    duplicates = excluded_blogs = inversions = 0
    last_votes = None
    boundary = {"last_above": None, "first_at_or_below": None}
    external_entries = []
    seen_pages = set()
    vote_counts = {}
    repeated_pages = []
    started = now()
    while True:
        page = len(pages)
        rows = fetch(page, size)
        votes = [r["metrics"]["public_total_votes"] for r in rows]
        if any(isinstance(v, bool) or not isinstance(v, int) for v in votes):
            raise ValueError("Feed contains a missing or noninteger public vote count")
        signature = hashlib.sha256("\n".join(r["paper_group_id"] for r in rows).encode()).hexdigest()
        if rows and signature in seen_pages:
            if not reconcile_ties or final_page is None and page>=4 and all(p["group_sequence_sha256"]==signature for p in pages[-4:]):
                raise RuntimeError(f"API repeated an entire page at offset {page * size}")
            repeated_pages.append(page)
        seen_pages.add(signature)
        for offset,(row, likes) in enumerate(zip(rows, votes, strict=True)):
            inversions += int(last_votes is not None and likes > last_votes)
            last_votes = likes
            position = dict(rank=page*size+offset+1, likes=likes, id=row["paper_group_id"])
            if likes <= threshold:
                if boundary["first_at_or_below"] is None:
                    boundary["first_at_or_below"] = position
                continue
            boundary["last_above"] = position
            vote_counts[likes] = vote_counts.get(likes,0)+1
            if row.get("external_blog") is not None or row.get("external_link") is not None:
                excluded_blogs += 1
                external_entries.append(position)
                continue
            paper = paper_record(row)
            duplicates += int(paper["id"] in papers)
            papers[paper["id"]] = paper
        summary = dict(page=page, size=len(rows), max_likes=max(votes, default=None), min_likes=min(votes, default=None),
                       above_threshold=sum(v > threshold for v in votes), group_sequence_sha256=signature)
        pages.append(summary)
        report(f"Crawl · pages of {size}", page+1, None, eligible=len(papers), lowest=summary["min_likes"])
        if not rows or max(votes) <= threshold:
            break
        if final_page is not None and page>=final_page:raise RuntimeError("Preobserved cutoff moved during the crawl")
    return papers, dict(page_size=size, started_at=started, ended_at=now(), pages=pages, last_page=pages[-1],
                        eligible=len(papers), duplicates=duplicates, excluded_blogs=excluded_blogs, inversions=inversions,
                        boundary=boundary, external_entries=external_entries, vote_counts=vote_counts,
                        repeated_pages=repeated_pages)


def verify_passes(previous, current):
    """Counts alone can match while identities have moved across a page boundary."""
    return dict(added=sorted(current.keys()-previous.keys()), removed=sorted(previous.keys()-current.keys()))


def feed_rows(client,page,size,topic=None):
    """Fetch one public feed page and honor a transient service retry instruction."""
    for attempt in range(6):
        try:
            params={**QUERY,"pageSize":size,"pageNum":page}
            if topic:params["topics"]=json.dumps([topic],separators=(",",":"))
            response=client.get(FEED,params=params)
            response.raise_for_status()
            payload=response.json()
            if payload["page"]!=page or not isinstance(payload["papers"],list):
                raise RuntimeError(f"Unexpected feed page {page}")
            return payload["papers"]
        except (httpx.TransportError,httpx.HTTPStatusError) as error:
            status=getattr(getattr(error,"response",None),"status_code",None)
            if attempt==5 or status is not None and status!=429 and status<500:raise
            retry=response.headers.get("Retry-After","") if status is not None else ""
            time.sleep(int(retry) if retry.isdigit() else 2**attempt)


def collect(folder, progress, threshold=None, *, anonymous=False):
    """Require matching consecutive independent passes; retain a discrepancy audit on failure."""
    if (folder / "manifest.json").exists() and census_path(folder).exists():
        manifest=read_json(folder / "manifest.json")
        if threshold is not None and threshold != manifest["threshold_exclusive"]:
            raise ValueError(f"Snapshot {folder.name} already uses a different threshold. Choose a new snapshot ID.")
        if census_digest(folder)!=manifest["content_sha256"]:
            raise RuntimeError("The stored census differs from the frozen manifest")
        return manifest
    threshold = CURRENT_THRESHOLD if threshold is None else threshold
    key = os.environ.get("ALPHAXIV_API_KEY")
    if not anonymous and not key:
        raise ValueError("ALPHAXIV_API_KEY is required for a fresh census")
    audits, differences = [], []
    previous = None
    headers={"User-Agent":"PaperAtlas/1.0 (alphaXiv public paper census)"}
    if not anonymous:
        headers["Authorization"]="Bearer "+key
    with httpx.Client(timeout=75, headers=headers) as client, ThreadPoolExecutor(1) as secondary:
        def fetch(page, size, topic=None):
            return feed_rows(client,page,size,topic)
        second=None
        if threshold==10:
            from .reconcile import census_pass
            def secondary_progress(stage,done,total,**extra):
                save_json(folder/"work"/"second-pass.json",dict(stage=stage,done=done,total=total,updated=now(),**extra))
            second=secondary.submit(census_pass,folder,fetch,175,threshold,secondary_progress)
        sizes=(125,175,97,173) if threshold==10 else (100,200,97,173) if threshold==20 else (100,50,97,73)
        for size in sizes:
            if size==175 and second is not None:
                current,audit=second.result()
            elif threshold in CAPPED:
                from .reconcile import census_pass
                current,audit=census_pass(folder,fetch,size,threshold,progress)
            else:
                current, audit = scan(fetch, size, progress, threshold=threshold)
            audits.append(audit)
            if previous is not None:
                diff = verify_passes(previous, current)
                differences.append(diff)
                if not any(diff.values()) and not audit["inversions"] and not audits[-2]["inversions"]:
                    break
            previous = current
        else:
            save_json(folder / "coverage-unresolved.json", {"passes":audits,"differences":differences})
            raise RuntimeError("Independent crawls disagree. See coverage-unresolved.json and rerun collection.")
    rows = [current[k] for k in sorted(current)]
    if not rows:
        raise RuntimeError("Empty qualifying feed; refusing to publish an empty census")
    digest=write_census(folder,rows,compressed=threshold==10)
    manifest = dict(snapshot=folder.name, feed=FEED, query=QUERY, threshold_exclusive=threshold,
                    feed_access="anonymous public metadata" if anonymous else "authenticated public metadata",
                    started_at=min(a["started_at"] for a in audits), ended_at=max(a["ended_at"] for a in audits), count=len(rows),
                    content_sha256=digest, passes=audits, differences=differences,
                    coverage="verified", title_only=sum(r["title_only"] for r in rows))
    if threshold in CAPPED:
        manifest["accepted_vote_changes"]=[dict(id=k,first=previous[k]["likes"],second=current[k]["likes"])
                    for k in sorted(current) if previous[k]["likes"]!=current[k]["likes"]]
    save_json(folder / "manifest.json", manifest)
    LOG.info("Verified %d unique eligible paper groups", len(rows))
    return manifest
