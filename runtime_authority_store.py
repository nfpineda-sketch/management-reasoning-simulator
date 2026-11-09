"""P3-26: the Phase-3 authority-experiment artifact store. Faculty and research only.

Faculty decision of 2026-11-07: an authority-experiment artifact is kept in a SEPARATE Phase-3
faculty/research surface, never inside the frozen Phase-2 trace schema, the resident trace, the
resident-visible output, the scoring data or the critical-event data.

So this module is the smallest thing that satisfies that decision: a directory of immutable JSON records,
one per outcome of one minute, named by a deterministic identity, with the artifact's own digest as its
integrity check. It is **off unless a faculty environment names a directory** (``MRS_PHASE3_AUTHORITY_STORE``),
so in production nothing is written, nothing is read and nothing is created -- the same shape as the rest of
this layer.

What it deliberately is NOT: a database migration. The repository's account database is the authorization
boundary for resident and faculty data, and an experiment artifact is neither; adding a table for a dormant
experiment would be a bigger change than the decision asks for, and a harder one to remove.

Integrity: the record carries the artifact's digest and this module recomputes it on every read. That
detects an accidental or content-level modification. It does NOT detect a malicious actor who can also
recompute the digest -- a signature would need a key, and no signature is required by this package.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Mapping

import runtime_authority as ra

STORE_VERSION = "P3-26"
#: The faculty environment names the directory. Absent means the store is off, which is production.
STORE_FLAG = "MRS_PHASE3_AUTHORITY_STORE"

NOT_CONFIGURED = "NO_AUTHORITY_ARTIFACT_STORE_CONFIGURED"
NOT_AN_ARTIFACT = "NOT_AN_AUTHORITY_EXPERIMENT_ARTIFACT"
COLLISION = "ARTIFACT_IDENTITY_COLLISION_WITH_DIFFERENT_CONTENT"
DIGEST_MISMATCH = "ARTIFACT_DIGEST_DOES_NOT_RECOMPUTE"
#: Nothing resident-facing may ever read this store; the test that proves it names this constant.
RESIDENT_READERS_FORBIDDEN = ("app.py", "pilot_acceptance.py", "management_trace_store.py",
                              "rubric_store.py", "progress_store.py")


#: Why a named directory is refused. The P3-28 review pointed out that ``MRS_PHASE3_AUTHORITY_STORE=.``
#: would have written artifacts -- with the whole replay input and the snapshot -- inside the repository.
OUTSIDE_THE_REPOSITORY = ("an artifact store must be an absolute path outside the repository: experiment "
                          "records are run data, and the repository holds no run data")


def repository_root() -> Path:
    return Path(__file__).resolve().parent


def root(environ: Mapping[str, str] | None = None) -> Path | None:
    """The directory this process stores artifacts in, or None when no faculty environment named one.

    A relative path, or any path inside the repository, is refused rather than created: nothing of a run
    belongs in the tree, and ``validation/`` least of all.
    """
    live = os.environ if environ is None else environ
    named = str(live.get(STORE_FLAG, "") or "").strip()
    if not named:
        return None
    directory = Path(named)
    if not directory.is_absolute():
        return None
    try:
        resolved = directory.resolve()
        inside = resolved == repository_root() or repository_root() in resolved.parents
    except Exception:
        return None
    return None if inside else directory


def refused_root(environ: Mapping[str, str] | None = None) -> str:
    """Why the named directory was refused, for a faculty reader. Empty when there is nothing to refuse."""
    live = os.environ if environ is None else environ
    named = str(live.get(STORE_FLAG, "") or "").strip()
    if not named or root(environ) is not None:
        return ""
    return OUTSIDE_THE_REPOSITORY


def configured(environ: Mapping[str, str] | None = None) -> bool:
    return root(environ) is not None


def artifact_id(artifact: Mapping) -> str:
    """The deterministic identity of one experiment record.

    It distinguishes the encounter, the attempt, the experiment, the minute and the layer version, and it
    does not depend on a clock: two runs of the same encounter with the same actions produce the same id,
    and that is wanted -- a repeated write of the same content is idempotent instead of a new record.
    """
    body = dict(artifact)
    minutes = [dict(record) for record in (body.get("minutes") or [])]
    # The identity does NOT include the artifact's digest. The P3-28 review was right that including it
    # made every content change a new identity, so the create-only rule could never refuse anything: with
    # the digest out, the same encounter, attempt and minute is the same record, and content that differs
    # under that identity is a collision the store refuses instead of overwriting.
    return ra.digest_of({
        "encounter_id": body.get("encounter_id"),
        "experiment_id": body.get("experiment_id"),
        "attempt": body.get("attempt"),
        "case_id": body.get("case_id"),
        "last_minute": (minutes[-1].get("minute") if minutes else None),
        "last_outcome": (minutes[-1].get("outcome") if minutes else None),
        "minutes": len(minutes),
        # P3-49 found the store keeping the record written at the commit and REFUSING the one written
        # after the order pipeline settled each fate: same identity, different content, so the
        # create-only rule called it a collision and the durable record never carried the provenance.
        # The two are different immutable facts about the same minute -- what was known when the
        # pressure was written, and what was known once the fates existed -- so the stage is part of the
        # identity and both are kept.
        "provenance_settled": bool(minutes[-1].get("provenance_settled")) if minutes else None,
        "site": body.get("site"),
        "store": STORE_VERSION,
    })[:32]


def _name(artifact: Mapping, identifier: str) -> str:
    body = dict(artifact)
    minutes = [dict(record) for record in (body.get("minutes") or [])]
    last = minutes[-1].get("minute") if minutes else "x"
    state = str(body.get("experiment_state") or ("halted" if body.get("halted") else "active"))
    return f"{body.get('case_id') or 'case'}__m{last}__{state}__{identifier}.json"


def persist(artifact: Mapping, *, environ: Mapping[str, str] | None = None) -> dict:
    """Write one immutable record, or say why nothing was written. Never raises into a caller.

    Create-only: an identity that already holds the same content is idempotent, and one that holds
    different content is a refusal -- a record is never overwritten.
    """
    try:
        body = dict(artifact)
        if str(body.get("artifact") or "") != "phase3_authority_experiment":
            return {"stored": False, "why": NOT_AN_ARTIFACT}
        directory = root(environ)
        if directory is None:
            return {"stored": False, "why": NOT_CONFIGURED}
        identifier = artifact_id(body)
        record = {"store": STORE_VERSION, "artifact_id": identifier,
                  "artifact_digest": body.get("artifact_digest"), "artifact": body}
        payload = ra.canonical(record)
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / _name(body, identifier)
        if path.exists():
            existing = path.read_text(encoding="utf-8")
            if existing == payload:
                return {"stored": True, "idempotent": True, "artifact_id": identifier,
                        "path": str(path), "why": ""}
            return {"stored": False, "why": COLLISION, "artifact_id": identifier, "path": str(path)}
        path.write_text(payload, encoding="utf-8")
        return {"stored": True, "idempotent": False, "artifact_id": identifier, "path": str(path),
                "bytes": len(payload.encode("utf-8")), "why": ""}
    except Exception as error:  # a store failure may never break an encounter
        return {"stored": False, "why": f"STORE_ERROR {type(error).__name__}: {error}"}


def paths(*, environ: Mapping[str, str] | None = None) -> list:
    directory = root(environ)
    if directory is None or not directory.exists():
        return []
    return sorted(directory.glob("*.json"))


def records(*, encounter_id: str | None = None, case_id: str | None = None,
            environ: Mapping[str, str] | None = None) -> list:
    """The stored records, newest content last, as a faculty retrieval path would list them."""
    out = []
    for path in paths(environ=environ):
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        body = dict(record.get("artifact") or {})
        if encounter_id is not None and body.get("encounter_id") != encounter_id:
            continue
        if case_id is not None and body.get("case_id") != case_id:
            continue
        out.append({"artifact_id": record.get("artifact_id"), "path": str(path),
                    "encounter_id": body.get("encounter_id"), "case_id": body.get("case_id"),
                    "experiment_id": body.get("experiment_id"), "attempt": body.get("attempt"),
                    "experiment_state": body.get("experiment_state"),
                    "minutes": len(body.get("minutes") or []),
                    "halted": bool(body.get("halted")),
                    "mixed_trajectory": bool(body.get("mixed_trajectory")),
                    # P3-49: with the settlement stage in the identity there are two records per minute,
                    # and a reader has to be able to ask for the settled one without loading both.
                    "provenance_settled": bool((list(body.get("minutes") or []) or [{}])[-1]
                                               .get("provenance_settled")),
                    "artifact_digest": body.get("artifact_digest")})
    return sorted(out, key=lambda item: (str(item["encounter_id"]), item["minutes"],
                                         bool(item["provenance_settled"])))


def load(identifier: str, *, environ: Mapping[str, str] | None = None) -> dict | None:
    """One stored artifact by its identity, or None. The faculty retrieval path, and the only one."""
    for path in paths(environ=environ):
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if str(record.get("artifact_id")) == str(identifier):
            return dict(record.get("artifact") or {})
    return None


def verify(identifier: str, *, environ: Mapping[str, str] | None = None) -> dict:
    """Retrieve, recompute the digest and check the record's identity. No signature, by design."""
    artifact = load(identifier, environ=environ)
    if artifact is None:
        return {"found": False, "verified": False, "why": "no stored artifact with that identity"}
    checked = ra.verify_artifact(artifact)
    return {"found": True, "verified": bool(checked["digest_matches"] and checked["complete"]),
            "digest_matches": checked["digest_matches"], "complete": checked["complete"],
            "identity_matches": artifact_id(artifact) == str(identifier),
            "missing_fields": checked["missing_fields"],
            "incomplete_minutes": checked["incomplete_minutes"],
            "integrity": "the digest detects an accidental or content modification; it does not detect a "
                         "modification by someone who can recompute it, because the record carries no "
                         "signature and this package requires none",
            "why": "" if checked["digest_matches"] else DIGEST_MISMATCH}


def replay(identifier: str, *, environ: Mapping[str, str] | None = None) -> dict:
    """Retrieve, verify and replay a stored experiment, from the record alone."""
    artifact = load(identifier, environ=environ)
    if artifact is None:
        return {"found": False, "reproduces": False, "why": "no stored artifact with that identity"}
    checked = verify(identifier, environ=environ)
    replayed = ra.replay_site_artifact(artifact)
    return {"found": True, "verified": checked["verified"], "reproduces": bool(replayed["reproduces"]),
            "compared": replayed["compared"], "minutes": replayed["minutes"],
            "experiment_state": artifact.get("experiment_state"),
            "mixed_trajectory": bool(artifact.get("mixed_trajectory")),
            "why": checked["why"] or ""}
