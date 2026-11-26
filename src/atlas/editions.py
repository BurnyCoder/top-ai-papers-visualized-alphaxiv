"""Use the manifest cutoff to route each edition and read both page-audit formats."""
from pathlib import Path

CURRENT_THRESHOLD = 10
PREVIOUS = {10: ("2026-11-26-over-20",20), 20: ("2026-11-26-over-50",50), 50: ("2026-11-26",100)}
CAPPED = {10,20}


def edition_path(threshold):
    """The original atlas owns the root URL; additional cutoffs each have their own route."""
    return Path() if threshold == 100 else Path(f"over-{threshold}")


def above_threshold(page):
    """Earlier versioned manifests used a field named after the old cutoff."""
    return page["above_threshold"] if "above_threshold" in page else page["above_100"]
