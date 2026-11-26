"""Verify the deployed map and the pinned Hub artifacts with streamed public HTTP requests."""
import argparse
import hashlib
import json
from urllib.parse import quote
from urllib.request import Request, urlopen

from atlas.editions import edition_path
from atlas.io import HUB, PAGES, ROOT, read_json


def fetch(url):
    """Request the public file anonymously, following the Hub's signed download redirect."""
    return urlopen(Request(url,headers={"User-Agent":"alphaXiv-atlas-release-verification/1.0"}),timeout=120)


def verify(url,expected):
    with fetch(url) as stream:
        digest=hashlib.file_digest(stream,"sha256").hexdigest()
    if digest!=expected:
        raise ValueError(f"Public SHA-256 mismatch for {url.split('?')[0]}")


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshot")
    parser.add_argument("--hub-revision",help="Defaults to the immutable atlas tag for this snapshot")
    args=parser.parse_args()
    folder=ROOT/"results"/args.snapshot
    manifest=read_json(folder/"manifest.json")
    edition=edition_path(manifest["threshold_exclusive"])
    url=PAGES if not edition.parts else PAGES+edition.as_posix()+"/"
    for name in ("atlas.json","papers.csv","paper.pdf","progress.json"):
        with (ROOT/"docs"/edition/name).open("rb") as stream:
            local=hashlib.file_digest(stream,"sha256").hexdigest()
        verify(url+name,local)
        print("Pages verified",name,flush=True)
    tag=args.hub_revision or "atlas-"+args.snapshot
    base=f"{HUB}/resolve/{quote(tag,safe='')}/results/{quote(args.snapshot,safe='')}/"
    with fetch(base+"checksums.json") as stream: remote=json.load(stream)
    if remote!=read_json(folder/"checksums.json"):
        raise ValueError("The published artifact manifest differs from the local release")
    for name,digest in remote.items():
        verify(base+quote(name,safe="")+"?download=true",digest)
        print("Hub verified",name,flush=True)


if __name__=="__main__":
    main()
