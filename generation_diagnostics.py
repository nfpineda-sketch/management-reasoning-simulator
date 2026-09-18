"""Keep a failed paid generation on disk so it can be replayed without paying again.

A failure carries the draft, the exact validator issues, the reviewer objections
and the per-stage request ledger. Without it the only way to study the failure is
to buy another one. The account path also stores this in the administrator table;
this file is the copy that survives a process with no account store, and the one
an offline replay reads.

Written under ``local-data/``, which is git-ignored. The diagnostic never holds
credentials; it does hold unreviewed fictional case text, so it stays local and
is never rendered to a learner.
"""
from copy import deepcopy
import json
import logging
import os
from pathlib import Path
import time

DIAGNOSTIC_DIR = Path(os.environ.get("MRS_DIAGNOSTIC_DIR")
                      or Path(__file__).resolve().parent / "local-data" / "generation_failures")
_MAX_BYTES = 4_000_000
_KEEP = 50


def _prune(directory):
    reports = sorted(directory.glob("*.json"), key=lambda p: p.stat().st_mtime)
    for stale in reports[:-_KEEP]:
        stale.unlink(missing_ok=True)


def save_failure(error, *, challenge_id=None):
    """Persist ``error.diagnostic`` and return the path, or None if there is none.

    Never raises: a failed write must not replace the generation error the caller
    is about to report.
    """
    diagnostic = getattr(error, "diagnostic", None)
    if not isinstance(diagnostic, dict):
        return None
    reference = str(getattr(error, "reference", "CASE-UNKNOWN"))
    safe_reference = "".join(c for c in reference if c.isalnum() or c in "-_")[:40] or "CASE-UNKNOWN"
    try:
        payload = deepcopy(diagnostic)
        payload.setdefault("challenge_id", challenge_id)
        payload["reference"] = reference
        payload["saved_at"] = int(time.time())
        encoded = json.dumps(payload, indent=1, default=str)
        if len(encoded.encode()) > _MAX_BYTES:
            payload.pop("draft", None)
            payload["draft_omitted"] = "larger than the diagnostic size limit"
            encoded = json.dumps(payload, indent=1, default=str)
        DIAGNOSTIC_DIR.mkdir(parents=True, exist_ok=True)
        path = DIAGNOSTIC_DIR / f"{payload['saved_at']}_{safe_reference}.json"
        path.write_text(encoded)
        _prune(DIAGNOSTIC_DIR)
        # Log the path only. Case content and provider payloads stay in the file.
        logging.getLogger(__name__).warning("Saved generation failure %s", path.name)
        return path
    except (OSError, TypeError, ValueError, RecursionError):
        logging.getLogger(__name__).warning("Could not save the generation failure report")
        return None
