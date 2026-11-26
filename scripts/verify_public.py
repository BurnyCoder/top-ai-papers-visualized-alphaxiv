"""Verify the deployed map and the pinned Hub artifacts with streamed public HTTP requests."""
import argparse
import hashlib
import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import quote
from urllib.request import Request, urlopen

from atlas.editions import edition_path
from atlas.io import HUB, PAGES, ROOT, read_json


def fetch(url):
    """Request the public file anonymously, following the Hub's signed download redirect."""
    return urlopen(Request(url,headers={"User-Agent":"alphaXiv-atlas-release-verification/1.0"}),timeout=120)


def verify(url,expected,restore=None):
    """Optionally restore a verified numerical array while checking the public bytes."""
    tmp=None
    try:
        with fetch(url) as stream:
            if restore is None:digest=hashlib.file_digest(stream,"sha256").hexdigest()
            else:
                restore.parent.mkdir(parents=True,exist_ok=True)
                hasher=hashlib.sha256()
                with NamedTemporaryFile(dir=restore.parent,delete=False) as out:
                    tmp=Path(out.name)
                    for block in iter(lambda:stream.read(1024*1024),b""):
                        hasher.update(block);out.write(block)
                digest=hasher.hexdigest()
        if digest!=expected:raise ValueError(f"Public SHA-256 mismatch for {url.split('?')[0]}")
        if restore is not None:os.replace(tmp,restore)
    finally:
        if tmp is not None:tmp.unlink(missing_ok=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshot")
    parser.add_argument("--hub-revision",help="Defaults to the immutable atlas tag for this snapshot")
    parser.add_argument("--restore-arrays",type=Path,help="Also write verified numerical files to this checkout's dated results folder")
    args=parser.parse_args()
    folder=ROOT/"results"/args.snapshot
    manifest=read_json(folder/"manifest.json")
    edition=edition_path(manifest["threshold_exclusive"])
    url=PAGES if not edition.parts else PAGES+edition.as_posix()+"/"
    public=read_json(ROOT/"docs"/edition/"atlas.json")
    assets=["atlas.json",public.get("csv","papers.csv"),"paper.pdf","progress.json",*public.get("paper_parts",[])]
    if "controls" in public:assets.append(public["controls"]["file"])
    if (ROOT/"docs"/edition/"walkthrough.mp4").exists():assets.append("walkthrough.mp4")
    if "abstract_chunk_size" in public:
        size=public["abstract_chunk_size"]
        count=public.get("paper_count") or len(public["papers"])
        assets.extend(f"abstracts/{i//size}.json" for i in range(0,count,size))
    def pages_asset(name):
        with (ROOT/"docs"/edition/name).open("rb") as stream:
            local=hashlib.file_digest(stream,"sha256").hexdigest()
        verify(url+name,local)
    with ThreadPoolExecutor(max_workers=4) as pool:list(pool.map(pages_asset,assets))
    print("Pages files verified:",len(assets),flush=True)
    tag=args.hub_revision or "atlas-"+args.snapshot
    base=f"{HUB}/resolve/{quote(tag,safe='')}/results/{quote(args.snapshot,safe='')}/"
    with fetch(base+"checksums.json") as stream: remote=json.load(stream)
    if remote!=read_json(folder/"checksums.json"):
        raise ValueError("The published artifact manifest differs from the local release")
    for name,digest in remote.items():
        destination=None
        if args.restore_arrays and name in ("embeddings.npy","geometry.npz","seed-layouts.npz"):
            destination=args.restore_arrays/"results"/args.snapshot/name
        verify(base+quote(name,safe="")+"?download=true",digest,destination)
        print("Hub verified",name,flush=True)


if __name__=="__main__":
    main()
