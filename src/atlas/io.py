"""Atomic snapshot files, timestamped console/file logging and the live run ledger."""
from __future__ import annotations

import json
import hashlib
import logging
import os
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path.cwd()
RESULTS = ROOT / "results"
CACHE = ROOT / ".atlas-cache"
PACKAGE = Path(__file__).parent
GITHUB = "https://github.com/BurnyCoder/top-ai-papers-visualized-alphaxiv"
PAGES = "https://burnycoder.github.io/top-ai-papers-visualized-alphaxiv/"
HUB = "https://huggingface.co/datasets/BurnyCoder/alphaxiv-paper-atlas"
COLLECTION = "https://huggingface.co/collections/BurnyCoder/alphaxiv-paper-atlas-6b0813ca579f3a0893eb123a"
LOG = logging.getLogger("paper-atlas")


def now():
    """UTC timestamps describe the observation window across machines."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def save_bytes(path, value):
    """Replace only after the entire new file has reached disk, including on Windows."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_file() and path.stat().st_size==len(value) and path.read_bytes()==value:
        return
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as handle:
        temp = Path(handle.name)
        handle.write(value)
    try:
        for attempt in range(7):
            try:
                os.replace(temp, path)
                break
            except PermissionError:
                if attempt==6:
                    raise
                time.sleep(.1*2**attempt)
    finally:
        temp.unlink(missing_ok=True)


def save_json(path, value, *, compact=False):
    """Reject NaN and infinity so the same files work in browsers and Python."""
    text = json.dumps(value, ensure_ascii=False, allow_nan=False, indent=None if compact else 2,
                      separators=(",", ":") if compact else None)
    save_bytes(path, (text + "\n").encode())


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def papers_at(folder):
    with (folder/"papers.jsonl").open(encoding="utf-8") as source:
        return [json.loads(line) for line in source]


def file_hash(path):
    """Stream large numeric artifacts without duplicating them in memory."""
    with path.open("rb") as source:return hashlib.file_digest(source,"sha256").hexdigest()


def start_log(snapshot):
    """Write all application messages to the terminal and a per-invocation log."""
    logs = ROOT / "logs"
    logs.mkdir(exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    formatter = logging.Formatter("%(asctime)sZ %(levelname)s %(message)s", "%Y-%m-%dT%H:%M:%S")
    formatter.converter = time.gmtime
    LOG.setLevel(logging.INFO)
    for handler in (logging.StreamHandler(), logging.FileHandler(logs / f"{snapshot}-{stamp}.log", encoding="utf-8")):
        handler.setFormatter(formatter)
        LOG.addHandler(handler)


class Progress:
    """Expose only aggregate run state through the monitor endpoint."""
    def __init__(self, snapshot):
        self.snapshot = snapshot
        self.start = time.monotonic()
        self.stage = ""
        self.stage_start = self.start
        self.initial_done = 0
        self.last_note = 0.0

    def __call__(self, stage, done, total, **extra):
        clock=time.monotonic()
        changed=stage!=self.stage
        if changed:
            self.stage,self.stage_start,self.initial_done=stage,clock,done
        state = dict(snapshot=self.snapshot, stage=stage, done=done, total=total,
                     elapsed_seconds=round(clock-self.start, 1), updated_at=now(), **extra)
        if total is not None and done>self.initial_done:
            state["estimated_stage_seconds_left"]=round((total-done)*(clock-self.stage_start)/(done-self.initial_done))
        save_json(RESULTS / "progress.json", state)
        if changed or clock-self.last_note>=60 or done==total:
            self.last_note=clock
            notes=ROOT/"reports"/"progress.md"
            notes.parent.mkdir(parents=True,exist_ok=True)
            with notes.open("a",encoding="utf-8") as file:
                details=", ".join(f"{k}={v}" for k,v in extra.items())
                line=f"- {state['updated_at']} · {self.snapshot} · {stage} · {done}/{total if total is not None else '?'} {details}"
                file.write("\n"+line.rstrip()+"\n")
        LOG.info("%s %s/%s %s", stage, done, total if total is not None else "?", extra or "")
