"""Census of the public, all-time alphaXiv likes feed. API schema: https://api-dev.alphaxiv.org/api.json"""
from __future__ import annotations

import hashlib
import json
import os
import time

import httpx
from .io import LOG, PACKAGE, now, read_json, save_bytes, save_json

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


def scan(fetch, size, report=lambda *_args, **_kw: None):
    """Finish beyond the threshold, checking monotonic ordering over all returned rows."""
    papers, pages = {}, []
    duplicates = excluded_blogs = inversions = 0
    last_votes = None
    seen_pages = set()
    started = now()
    while True:
        page = len(pages)
        rows = fetch(page, size)
        votes = [r["metrics"]["public_total_votes"] for r in rows]
        if any(isinstance(v, bool) or not isinstance(v, int) for v in votes):
            raise ValueError("Feed contains a missing or noninteger public vote count")
        signature = hashlib.sha256("\n".join(r["paper_group_id"] for r in rows).encode()).hexdigest()
        if rows and signature in seen_pages:
            raise RuntimeError(f"API repeated an entire page at offset {page * size}")
        seen_pages.add(signature)
        for row, likes in zip(rows, votes, strict=True):
            inversions += int(last_votes is not None and likes > last_votes)
            last_votes = likes
            if likes <= 100:
                continue
            if row.get("external_blog") is not None or row.get("external_link") is not None:
                excluded_blogs += 1
                continue
            paper = paper_record(row)
            duplicates += int(paper["id"] in papers)
            papers[paper["id"]] = paper
        summary = dict(page=page, size=len(rows), max_likes=max(votes, default=None), min_likes=min(votes, default=None),
                       above_100=sum(v > 100 for v in votes), group_sequence_sha256=signature)
        pages.append(summary)
        report(f"Crawl · pages of {size}", page+1, None, eligible=len(papers), lowest=summary["min_likes"])
        if not rows or max(votes) <= 100:
            break
    return papers, dict(page_size=size, started_at=started, ended_at=now(), pages=pages, last_page=pages[-1],
                        eligible=len(papers), duplicates=duplicates, excluded_blogs=excluded_blogs, inversions=inversions)


def verify_passes(previous, current):
    """Counts alone can match while identities have moved across a page boundary."""
    return dict(added=sorted(current.keys()-previous.keys()), removed=sorted(previous.keys()-current.keys()))


def collect(folder, progress):
    """Require matching consecutive independent passes; retain a discrepancy audit on failure."""
    if (folder / "manifest.json").exists() and (folder / "papers.jsonl").exists():
        manifest=read_json(folder / "manifest.json")
        if hashlib.sha256((folder/"papers.jsonl").read_bytes()).hexdigest()!=manifest["content_sha256"]:
            raise RuntimeError("The stored census differs from the frozen manifest")
        return manifest
    key = os.environ.get("ALPHAXIV_API_KEY")
    if not key:
        raise ValueError("ALPHAXIV_API_KEY is required for a fresh census")
    audits, differences = [], []
    previous = None
    with httpx.Client(timeout=75, headers={"Authorization":"Bearer "+key,
                      "User-Agent":"PaperAtlas/1.0 (alphaXiv public paper census)"}) as client:
        def fetch(page, size):
            for attempt in range(6):
                try:
                    response = client.get(FEED, params={**QUERY, "pageSize":size, "pageNum":page})
                    response.raise_for_status()
                    payload = response.json()
                    if payload["page"] != page or not isinstance(payload["papers"], list):
                        raise RuntimeError(f"Unexpected feed page {page}")
                    return payload["papers"]
                except (httpx.TransportError, httpx.HTTPStatusError) as error:
                    status = getattr(getattr(error, "response", None), "status_code", None)
                    if attempt == 5 or (status is not None and status != 429 and status < 500):
                        raise
                    retry = response.headers.get("Retry-After", "") if status is not None else ""
                    time.sleep(int(retry) if retry.isdigit() else 2**attempt)
        for size in (100, 50, 97, 73):
            current, audit = scan(fetch, size, progress)
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
    data = "".join(json.dumps(r, ensure_ascii=False, separators=(",",":"))+"\n" for r in rows).encode()
    save_bytes(folder / "papers.jsonl", data)
    manifest = dict(snapshot=folder.name, feed=FEED, query=QUERY, threshold_exclusive=100,
                    started_at=audits[0]["started_at"], ended_at=audits[-1]["ended_at"], count=len(rows),
                    content_sha256=hashlib.sha256(data).hexdigest(), passes=audits, differences=differences,
                    coverage="verified", title_only=sum(r["title_only"] for r in rows))
    save_json(folder / "manifest.json", manifest)
    LOG.info("Verified %d unique eligible paper groups", len(rows))
    return manifest
