"""Where a report finds the factual corrections recorded for an encounter.

The app and the three PDFs must show the same text, so both read the
corrections from here rather than from whatever the caller happens to pass.

A correction is an exact substring written for one passage of one stored
analysis, with the reason it was made. The stored analysis is never modified:
corrections are applied when a document is rendered, and every document says
how many it applied. Files are versioned by keeping the original entries and
adding new ones rather than editing history in place.

Layout, one file per encounter::

    <directory>/<encounter id>.json
    {"corrections": [{"original": ..., "replacement": ..., "reason": ...}, ...]}

``MRS_ANALYSIS_CORRECTIONS`` names the directory. It is absent in ordinary
deployments, and then nothing is corrected and every report shows the stored
analysis unchanged.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

ENV = "MRS_ANALYSIS_CORRECTIONS"
_SAFE = re.compile(r"^[A-Za-z0-9._-]{1,120}$")


def directory():
    """The configured corrections directory, or None."""
    value = str(os.environ.get(ENV, "")).strip()
    if not value:
        return None
    path = Path(value).expanduser()
    return path if path.is_dir() else None


def load(encounter_id):
    """Corrections recorded for this encounter, or an empty list.

    Never raises: a missing, unreadable or malformed file means no correction,
    because a report that cannot be corrected is still a report, while a report
    that fails to open is not.
    """
    root = directory()
    name = str(encounter_id or "").strip()
    if root is None or not _SAFE.match(name):
        return []
    path = root / (name + ".json")
    try:
        content = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    entries = content.get("corrections") if isinstance(content, dict) else content
    if not isinstance(entries, list):
        return []
    return [entry for entry in entries
            if isinstance(entry, dict) and isinstance(entry.get("original"), str)
            and isinstance(entry.get("replacement"), str) and entry["original"]]


def for_payload(payload):
    """Corrections for the encounter a frozen learner payload belongs to."""
    trace = (payload or {}).get("trace") if isinstance(payload, dict) else None
    first = (trace or [{}])[0] if isinstance(trace, list) and trace else {}
    before = first.get("state_before") if isinstance(first, dict) else {}
    return load((before or {}).get("case_id"))


def for_record(record):
    """Corrections for the encounter a saved faculty record belongs to."""
    session = ((record or {}).get("payload") or {}).get("session") or {}
    return load((session.get("state") or {}).get("case_id"))
