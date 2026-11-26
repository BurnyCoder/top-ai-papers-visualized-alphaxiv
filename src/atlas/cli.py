"""The atlas entry point composes census, remote inference, analysis and offline publication."""
import argparse
import re
from datetime import datetime, timezone

from dotenv import load_dotenv
from filelock import FileLock
from .io import LOG, RESULTS, ROOT, Progress, papers_at, start_log

STAGES = ("collect", "embed", "main", "label", "evaluate", "build")


def refresh(folder, through, progress, threshold=None):
    """Stop only at complete, reusable stage boundaries."""
    from .collect import collect
    collect(folder, progress, threshold)
    if through == "collect":
        return
    from .inference import embed, name_clusters
    papers = papers_at(folder)
    vectors = embed(folder, papers, progress)
    if through == "embed":
        return
    from .geometry import geometry, evaluate
    main = geometry(folder, vectors, progress)
    if through == "main":
        return
    name_clusters(folder, papers, vectors, main["labels"], progress)
    if through == "label":
        return
    evaluate(folder, papers, vectors, progress)
    if through != "evaluate":
        from .publish import build
        build(folder, progress)


def main():
    parser = argparse.ArgumentParser(description="alphaXiv Paper Atlas")
    commands = parser.add_subparsers(dest="action", required=True)
    update = commands.add_parser("refresh", help="Collect a new snapshot or resume a named one")
    update.add_argument("--snapshot", default=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ"))
    update.add_argument("--through", choices=STAGES, default="build")
    update.add_argument("--threshold", type=int, help="Exclusive public-like cutoff (new snapshots default to 50)")
    rebuild = commands.add_parser("build", help="Rebuild static outputs from the frozen files without API calls")
    rebuild.add_argument("--snapshot", required=True)
    monitor = commands.add_parser("monitor", help="Serve the local run dashboard on loopback")
    monitor.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    if args.action=="refresh" and args.threshold is not None and args.threshold < 0:
        parser.error("The exclusive vote threshold must be nonnegative")
    if args.action == "monitor":
        from .monitor import serve
        return serve(args.port)
    if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_-]{0,80}", args.snapshot):
        parser.error("Use a snapshot name made from letters, numbers, underscores and hyphens")
    folder = RESULTS / args.snapshot
    folder.mkdir(parents=True, exist_ok=True)
    start_log(args.snapshot)
    progress = Progress(args.snapshot)
    # A single output directory is shared by offline reports and the browser build.
    from .io import CACHE
    CACHE.mkdir(exist_ok=True)
    with FileLock(str(CACHE / "pipeline.lock"), timeout=0):
        try:
            if args.action == "refresh":
                load_dotenv(ROOT / ".env", override=True)
                refresh(folder, args.through, progress, args.threshold)
            else:
                from .publish import build
                build(folder, progress)
        except Exception as error:
            progress("Stopped", 0, None, error=str(error))
            LOG.exception("Pipeline stopped")
            raise


if __name__ == "__main__":
    main()
