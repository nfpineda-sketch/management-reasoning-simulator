"""P3-280 to P3-285: the FACULTY DEVELOPMENT REVIEW MODE of the GI pressure development authority experiment. A faculty-only, development-only, single-process review environment.

WHAT IT IS. A named, explicit configuration under which a faculty reviewer can launch one of the two allowlisted GI cases, run the encounter on the real page with the already-certified GI pressure
development authority (grant ``GI_PRESSURE_DEVELOPMENT_AUTHORITY_GRANT_V1``) active, have every authority artifact captured, and inspect the common-versus-legacy evidence afterwards. It is the
step from "technically validated development authority" to "faculty-reviewable controlled development environment".

WHAT IT IS NOT. It is not a resident pilot, a production deployment, a clinical validation or a consciousness authority. It enables NOTHING the existing grant did not already allow: no other family, no
other case, no write into ``mental_status``, no change of scoring, no first-pilot access. It adds no physiology and no authority.

THE CONFIGURATION (every condition is required; a missing or partial configuration makes the authority UNAVAILABLE, never partially enabled -- P3-281A):

* ``MRS_FACULTY_DEVELOPMENT_REVIEW=faculty_development_review``, read from the PROCESS environment (a deployment Secret cannot turn it on, like every other flag of the layer);
* the shadow comparison (live for the GI family: ``MRS_PHASE3_SHADOW_FAMILIES`` may not leave it out), the authority mode, the approved pressure snapshot and the ``development`` environment the
  registered grant names, all present;
* offline authored cases (``MRS_OFFLINE_CASES``): no paid generation, no paid picture, deterministic cases;
* a faculty authority store directory outside the repository, writable, on a filesystem verified as a local type (a network filesystem, or a type that is not on the local list, is refused);
* individual accounts (``MRS_AUTH_MODE=accounts``), because "faculty-only" must be enforceable and a shared password cannot tell a faculty member from anybody else; the account's role must be
  ``faculty`` or ``admin``;
* not the first pilot, and not Streamlit Community Cloud (whose filesystem is ephemeral and whose instances are not under this operator's control);
* the SINGLE-PROCESS lock below.

SINGLE-PROCESS ENFORCEMENT (FD-FAC-06, P3-280A). The review mode takes an exclusive advisory lock (``flock``) on a file inside the store, held for the life of the process. A second process that names
the same store cannot take it and its review mode is UNAVAILABLE. A forked child shares the open lock but not the pid recorded with it, so a child never counts as the holder. WHAT THIS PROVES: at
most one review process per store directory on a local filesystem. WHAT IT DOES NOT PROVE: uniqueness across machines that do not share the store (each has its own store and no shared durable state),
and uniqueness on a filesystem whose type cannot be read (reported as ``UNKNOWN_NOT_VERIFIABLE``, never as verified). Network filesystems, whose advisory locks are not reliable, and any filesystem type
that is not on the local list are refused. The lock is bound to the identity of its file (device and inode): a lock file that was deleted or replaced while the process runs is no longer held, and the
process must take it again (it cannot, when another process took the new file). The check runs at every evaluation, i.e. at every page run: a tampered store is detected, not prevented in between.

Nothing here decides anything clinical or imports the page, the engine or the common core.
"""
from __future__ import annotations

import os
import threading
from pathlib import Path
from typing import Any, Mapping

import runtime_authority as ra
import runtime_authority_store as ras
import runtime_pressure_grant as grants
import runtime_shadow as rs

VERSION = "P3-281"
RECORD_TYPE = "PHASE3_FACULTY_REVIEW_CONFIGURATION"
FLAG = "MRS_FACULTY_DEVELOPMENT_REVIEW"
MODE_ON = "faculty_development_review"
OFFLINE_FLAG = "MRS_OFFLINE_CASES"
#: Where the page keeps this session's decision (a ``phase3_`` key: never saved with the encounter, never in the resident's record).
SESSION_KEY = "phase3_faculty_review"
REVIEW_DIRNAME = "faculty_review"
FACULTY_ROLES = ("faculty", "admin")
AUTHORITY_MODE = grants.AUTHORITY_MODE
ENVIRONMENT = "development"
#: The two cases the grant names and the only ones the review environment launches.
ALLOWLIST = tuple(grants.CASES)

CONDITIONS = ("process_flag", "shadow", "shadow_family", "authority_flag", "snapshot", "development_environment", "offline_cases", "store", "accounts", "faculty_role", "no_pilot",
              "not_streamlit_cloud", "registered_grant", "single_process")
#: Conditions about the DEPLOYMENT (the same for every session of the process), as opposed to the account in front of the page (``faculty_role``).
CONFIGURATION_CONDITIONS = tuple(name for name in CONDITIONS if name != "faculty_role")
#: Conditions read from the process environment alone: they are re-read every time the authority asks, so a flag changed after the page decided cannot leave the review half-configured.
ENVIRONMENT_CONDITIONS = ("process_flag", "shadow", "shadow_family", "authority_flag", "snapshot", "development_environment", "offline_cases")
#: The GI family the two allowlisted cases belong to: the pressure authority needs its live shadow comparison, and ``MRS_PHASE3_SHADOW_FAMILIES`` can switch that family off by naming another.
FAMILY = grants.FAMILY
NETWORK_FILESYSTEMS = ("nfs", "nfs4", "cifs", "smb", "smb3", "smbfs", "afs", "ceph", "cephfs", "glusterfs", "9p", "davfs", "fuse.sshfs", "fuse.s3fs", "fuse.gcsfuse", "fuse.glusterfs", "fuse.rclone",
                       "lustre", "gpfs", "virtiofs", "vboxsf")
#: Local filesystem types on which an advisory ``flock`` is reliable (an allowlist: a type nobody vetted is refused, not assumed local).
LOCAL_FILESYSTEMS = ("ext2", "ext3", "ext4", "xfs", "btrfs", "zfs", "tmpfs", "ramfs", "overlay", "overlayfs", "f2fs", "jfs", "reiserfs", "bcachefs", "fuse.overlayfs", "ecryptfs")
FS_LOCAL, FS_NETWORK, FS_UNKNOWN, FS_UNVERIFIED = "LOCAL", "NETWORK_REFUSED", "UNKNOWN_NOT_VERIFIABLE", "NOT_ON_THE_LOCAL_LIST_REFUSED"

#: What is NOT supported once the experiment has halted (FD-FAC-07, P3-287A): named, not implemented. Everything that mutates the encounter or advances its clock is blocked by the
#: continuation guard; these three are listed because they neither move the clock nor the pressure, so the authority does not judge them, and nobody should expect them to work.
EXCLUDED_AFTER_HALT = ("ecg_acquisition", "cancel_pending_orders", "retrospective_explanation")
EXCLUDED_REASON = ("Not judged by the pressure authority: the operation neither moves the clock nor the pressure, so after a halt it is blocked rather than given new semantics. Excluded from the "
                   "first faculty review protocol on purpose (FD-FAC-07).")
#: The only resolution after a halt (FD-FAC-08): leave the experimental encounter. No resume, no rollback, no restart from the pre-authority snapshot.
RESOLUTION_AFTER_HALT = "ABANDON_EXPERIMENT"
UNSUPPORTED_RESOLUTIONS = ("RESUME", "ROLLBACK", "RESTART_FROM_PREAUTHORITY_SNAPSHOT")

# -- the process-wide single-process lock ------------------------------------------------------------------------------------------------------------------------
#: path -> {"fd": int, "pid": int, "ident": (st_dev, st_ino)}. Module state is deliberate and the only mutable state of this module: a lock IS process state.
_HELD: dict = {}
#: Page runs of one process may arrive on several threads: taking, confirming and releasing the lock is one critical section.
_GUARD = threading.RLock()


def asked(environ: Mapping[str, str] | None = None) -> bool:
    """Whether the process names the review mode AT ALL (any non-empty value, including a misspelled one: a misspelling is a refusal, not a silent absence). One dictionary lookup."""
    live = os.environ if environ is None else environ
    return bool(str(live.get(FLAG, "") or "").strip())


def filesystem_kind(path: Path, mounts: str | None = None) -> tuple:
    """(kind, type name) of the filesystem holding ``path``: LOCAL (a type on the local list), NETWORK_REFUSED, NOT_ON_THE_LOCAL_LIST_REFUSED (a type nobody vetted), or UNKNOWN_NOT_VERIFIABLE when the
    platform does not say. Never raises."""
    try:
        target = str(Path(path).resolve())
        best, kind_name = "", ""
        if mounts is None:
            with open("/proc/self/mounts", encoding="utf-8") as handle:
                mounts = handle.read()
        for line in mounts.splitlines():                       # ``mounts`` is a parameter so the classification can be tested against a mount table the test controls
            parts = line.split()
            if len(parts) >= 3:
                mount = parts[1].replace("\\040", " ")
                if (target == mount or target.startswith(mount.rstrip("/") + "/")) and len(mount) >= len(best):
                    best, kind_name = mount, parts[2]
        if not kind_name:
            return FS_UNKNOWN, ""
        lowered = kind_name.lower()
        if lowered in NETWORK_FILESYSTEMS:
            return FS_NETWORK, kind_name
        return (FS_LOCAL if lowered in LOCAL_FILESYSTEMS else FS_UNVERIFIED), kind_name
    except Exception:
        return FS_UNKNOWN, ""


def review_root(environ: Mapping[str, str] | None = None) -> Path | None:
    """The review directory inside the faculty authority store (bundles, feedback, the lock), or None when the store is not configured. Never inside the repository."""
    base = ras.root(environ)
    return None if base is None else base / REVIEW_DIRNAME


def _probe_writable(directory: Path) -> tuple:
    try:
        directory.mkdir(parents=True, exist_ok=True)
        probe = directory / f".probe-{os.getpid()}-{threading.get_ident()}"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
        return True, ""
    except Exception as error:
        return False, f"the review directory cannot be written ({type(error).__name__})"


def _identity(stat: os.stat_result) -> tuple:
    return (stat.st_dev, stat.st_ino)


def _drop(path: str, held: Mapping) -> None:
    _HELD.pop(path, None)
    try:
        os.close(held["fd"])
    except OSError:
        pass


def acquire_single_process_lock(directory: Path) -> dict:
    """Take (or confirm) this process's exclusive lock on the review directory. Returns ``{"held", "why", "filesystem", "pid"}``. Never raises; any doubt is NOT held.

    One critical section (page runs may arrive on several threads). A lock this process already holds is CONFIRMED against the file now at the path (device and inode): a lock file that was deleted or
    replaced, or a directory that was moved, makes the old descriptor a lock on nothing, so it is dropped and the lock is taken again (which fails when another process took the new file)."""
    with _GUARD:
        kind, kind_name = filesystem_kind(directory)
        base = {"held": False, "why": "", "filesystem": kind, "filesystem_type": kind_name, "pid": os.getpid(), "lock_file": ""}
        try:
            path = Path(directory) / "single_process.lock"
            base["lock_file"] = str(path)
            if kind == FS_NETWORK:
                return {**base, "why": f"the review directory is on a network filesystem ({kind_name}): an advisory lock is not reliable there"}
            if kind == FS_UNVERIFIED:
                return {**base, "why": f"the review directory is on a filesystem type that is not on the local list ({kind_name}): the single-process lock cannot be verified as reliable there"}
            held = _HELD.get(str(path))
            if held is not None:
                if held["pid"] == os.getpid():
                    try:
                        same = _identity(os.stat(str(path))) == held["ident"]
                    except OSError:
                        same = False
                    if same:
                        return {**base, "held": True, "why": "held by this process"}
                    _drop(str(path), held)           # the lock file is gone or is another file: this process no longer holds the lock of this path
                else:
                    _drop(str(path), held)           # inherited through fork: the child is not the holder, and its copy of the descriptor must not be mistaken for the lock
            import fcntl
            Path(directory).mkdir(parents=True, exist_ok=True)
            fd = os.open(str(path), os.O_RDWR | os.O_CREAT, 0o600)
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError:
                os.close(fd)
                return {**base, "why": "another process holds the faculty review lock for this store: the review mode requires a single process"}
            try:
                ident = _identity(os.fstat(fd))
                if ident != _identity(os.stat(str(path))):
                    os.close(fd)
                    return {**base, "why": "the lock file was replaced while it was being taken: the review mode fails closed"}
            except OSError:
                os.close(fd)
                return {**base, "why": "the lock file cannot be confirmed: the review mode fails closed"}
            try:
                os.ftruncate(fd, 0)
                os.write(fd, f"{os.getpid()}\n".encode("ascii"))
            except OSError:
                pass
            _HELD[str(path)] = {"fd": fd, "pid": os.getpid(), "ident": ident}
            return {**base, "held": True, "why": "acquired by this process"}
        except Exception as error:
            return {**base, "why": f"the single-process lock cannot be taken ({type(error).__name__}): the review mode fails closed"}


def release_for_tests() -> None:
    """Release every lock this process holds (tests only: a real review process holds its lock until it ends)."""
    with _GUARD:
        for path, held in list(_HELD.items()):
            if held["pid"] == os.getpid():
                try:
                    os.close(held["fd"])
                except OSError:
                    pass
            _HELD.pop(path, None)


def _truthy(value: Any) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def environment_conditions(live: Mapping[str, str]) -> dict:
    """The conditions that the PROCESS ENVIRONMENT alone decides (``ENVIRONMENT_CONDITIONS``), each from the live environment and never from a Secret. Used by ``evaluate`` and re-read by
    ``authority_available``, so a flag changed after the page decided cannot leave the review half-configured."""
    raw = str(live.get(FLAG, "") or "").strip()
    secrets_named = [name for name in (FLAG, ra.AUTHORITY_FLAG, ra.SNAPSHOT_FLAG, ra.ENVIRONMENT_FLAG, OFFLINE_FLAG) if rs._named_in_secrets(name)]
    return {
        "process_flag": raw.lower() == MODE_ON and FLAG not in secrets_named,
        "shadow": rs.mode(live) == rs.MODE_SHADOW_COMPARE,
        "shadow_family": rs.enabled_for(FAMILY, live),
        "authority_flag": str(live.get(ra.AUTHORITY_FLAG, "") or "").strip().lower() == ra.MODE_LIMITED_COMMON_AUTHORITY and ra.AUTHORITY_FLAG not in secrets_named,
        "snapshot": str(live.get(ra.SNAPSHOT_FLAG, "") or "").strip() == grants.PRESSURE_SNAPSHOT_ID and ra.SNAPSHOT_FLAG not in secrets_named,
        "development_environment": str(live.get(ra.ENVIRONMENT_FLAG, "") or "").strip().lower() == ENVIRONMENT and ra.ENVIRONMENT_FLAG not in secrets_named,
        "offline_cases": _truthy(live.get(OFFLINE_FLAG)) and OFFLINE_FLAG not in secrets_named,
    }


def evaluate(environ: Mapping[str, str] | None = None, *, accounts: bool = False, role: str | None = None, on_cloud: bool = False) -> dict:
    """The review-mode decision for ONE session of this process. Never raises. Not asked -> a minimal record and nothing else (one lookup); asked -> every condition, each with its own reason.

    ``enabled`` is True only when EVERY condition holds. Anything less is "the authority is unavailable": the page draws no review launcher and ``authority_available`` says no."""
    live = os.environ if environ is None else environ
    record = {"record_type": RECORD_TYPE, "version": VERSION, "requested": False, "enabled": False, "configuration_complete": False, "conditions": {}, "problems": [],
              "authority_mode": AUTHORITY_MODE, "grant_id": grants.GRANT_ID, "grant_version": grants.GRANT_VERSION, "environment": ENVIRONMENT, "allowlist": list(ALLOWLIST),
              "role": role, "access": "NOT_REQUESTED", "single_process": {"held": False}}
    try:
        raw = str(live.get(FLAG, "") or "").strip()
        if not raw:
            return record
        record["requested"] = True
        store_in_secrets = rs._named_in_secrets(ras.STORE_FLAG)
        directory = review_root(live)
        is_pilot, pilot_why = ra.looks_like_the_pilot(live)
        problems: dict = {}
        conditions = {
            **environment_conditions(live),
            "store": False,
            "accounts": bool(accounts),
            "faculty_role": str(role or "") in FACULTY_ROLES,
            "no_pilot": not is_pilot,
            "not_streamlit_cloud": not on_cloud,
            "registered_grant": dict(grants.GRANT).get("fingerprint") == grants.GRANT_FINGERPRINT,
            "single_process": False,
        }
        # The disk is touched only by a configuration that holds in everything else: a refused configuration (a pilot, the cloud, a shared password, a missing flag) writes nothing.
        writable, writable_why = False, ""
        if directory is not None and not store_in_secrets and all(conditions[name] for name in CONFIGURATION_CONDITIONS if name not in ("store", "single_process")):
            writable, writable_why = _probe_writable(directory)
        conditions["store"] = directory is not None and writable and not store_in_secrets
        problems["process_flag"] = f"{FLAG} must be exactly {MODE_ON!r} in the process environment (and not a Secret); it is {raw!r}"
        problems["shadow"] = f"the shadow comparison ({rs.FLAG}) is not on"
        problems["shadow_family"] = f"the live shadow comparison is not on for the {FAMILY!r} family ({rs.FAMILIES_FLAG} leaves it out): the pressure authority has nothing to compare against"
        problems["authority_flag"] = f"{ra.AUTHORITY_FLAG} is not the authority mode (or it is a Secret)"
        problems["snapshot"] = f"{ra.SNAPSHOT_FLAG} is not {grants.PRESSURE_SNAPSHOT_ID!r} (or it is a Secret)"
        problems["development_environment"] = f"{ra.ENVIRONMENT_FLAG} is not {ENVIRONMENT!r}, the only environment the registered grant names (or it is a Secret)"
        problems["offline_cases"] = f"{OFFLINE_FLAG} is not on: the review environment uses authored cases only and never pays a provider"
        probed = directory is not None and not store_in_secrets and all(conditions[name] for name in CONFIGURATION_CONDITIONS if name not in ("store", "single_process"))
        problems["store"] = (writable_why or (f"{ras.STORE_FLAG} does not name an absolute, writable directory outside the repository (or it is a Secret)" if (directory is None or store_in_secrets or probed)
                                              else "not probed: the rest of the configuration is incomplete, so nothing was written"))
        problems["accounts"] = "individual accounts are not enabled: faculty-only access cannot be enforced behind a shared password"
        problems["faculty_role"] = "the signed-in account is not a faculty or administrator account"
        problems["no_pilot"] = f"the first pilot's configuration is present: {pilot_why}"
        problems["not_streamlit_cloud"] = "Streamlit Community Cloud is refused: its filesystem is ephemeral and its instances are not under this operator's control"
        problems["registered_grant"] = "the registered grant is not the pinned one"
        # The lock is only taken when everything else holds: a misconfigured process must not hold a store.
        if all(conditions[name] for name in CONFIGURATION_CONDITIONS if name != "single_process"):
            lock = acquire_single_process_lock(directory)
            record["single_process"] = lock
            conditions["single_process"] = bool(lock.get("held"))
            problems["single_process"] = str(lock.get("why") or "the single-process lock is not held")
        else:
            problems["single_process"] = "not attempted: the configuration is incomplete"
        record["conditions"] = conditions
        record["problems"] = [f"{name}: {problems[name]}" for name in CONDITIONS if not conditions[name]]
        record["configuration_complete"] = all(conditions[name] for name in CONFIGURATION_CONDITIONS)
        record["enabled"] = all(conditions.values())
        record["access"] = ("FACULTY_REVIEWER" if record["enabled"] else
                            ("NOT_A_FACULTY_ACCOUNT" if record["configuration_complete"] and not conditions["faculty_role"] else "CONFIGURATION_INCOMPLETE"))
        return record
    except Exception as error:
        record.update({"enabled": False, "configuration_complete": False, "access": "CONFIGURATION_INCOMPLETE",
                       "problems": [f"the faculty review configuration cannot be evaluated ({type(error).__name__}): the review mode fails closed"]})
        return record


def publish(store: Any, decision: Mapping) -> None:
    """Keep this session's decision where the authority gate can read it. Never raises."""
    try:
        store[SESSION_KEY] = dict(decision)
    except Exception:
        pass


def authority_available(store: Any, environ: Mapping[str, str] | None = None) -> tuple:
    """(available, why): the one question the authority site asks before it opens. When the review mode is NOT named the answer is always yes and nothing else is read (the ordinary development
    path is untouched). When it is named, the authority is available only for a session whose published decision is ENABLED; a decision that was never published, a partial one and any error read as no."""
    live = os.environ if environ is None else environ
    try:
        decision = store.get(SESSION_KEY)
        if not asked(live):
            # The flag was removed after this session was a review session: the authority does not continue as an ordinary development encounter (P3-288 review).
            if isinstance(decision, Mapping) and decision.get("requested") is True:
                return False, "FACULTY_REVIEW_CONFIGURATION_INCOMPLETE: the review flag is no longer set in the process environment"
            return True, ""
        if isinstance(decision, Mapping) and decision.get("enabled") is True and decision.get("requested") is True:
            changed = [name for name, held in environment_conditions(live).items() if not held]
            if not changed:
                return True, ""
            return False, "FACULTY_REVIEW_CONFIGURATION_INCOMPLETE: the process environment no longer holds: " + ", ".join(changed)
        reasons = list(dict(decision or {}).get("problems") or ()) or ["the faculty review configuration was not evaluated for this session"]
        return False, "FACULTY_REVIEW_CONFIGURATION_INCOMPLETE: " + "; ".join(str(item) for item in reasons[:4])
    except Exception as error:
        return False, f"FACULTY_REVIEW_CONFIGURATION_INCOMPLETE: unreadable ({type(error).__name__})"


def case_allowed(case_id: str | None) -> bool:
    return str(case_id or "") in ALLOWLIST


def case_of_state(state: Mapping | None) -> str:
    """The authored case id of an encounter state (``encounter_spec.clinical_case.id``), or an empty string. Plain data: it imports nothing."""
    try:
        return str(dict(dict(dict(state or {}).get("encounter_spec") or {}).get("clinical_case") or {}).get("id") or "")
    except Exception:
        return ""


def surface_after_halt() -> dict:
    """What a faculty reviewer can and cannot do once the experiment has halted, read from the continuation guard's own classification (so this list cannot drift from what the page blocks)."""
    import runtime_authority_session as se
    allowed = sorted(name for name, kind in se.OPERATIONS.items() if kind in (se.READ_ONLY, se.LEAVES_THE_SESSION))
    blocked = sorted(name for name in se.OPERATIONS if name not in allowed)
    return {"allowed": allowed, "blocked": blocked, "excluded_unjudged": list(EXCLUDED_AFTER_HALT), "excluded_reason": EXCLUDED_REASON, "resolution": RESOLUTION_AFTER_HALT,
            "unsupported_resolutions": list(UNSUPPORTED_RESOLUTIONS), "notice": se.NOTICE_HEADLINE}


# -- P3-285: the scripted review set -----------------------------------------------------------------------------------------------------------------------------------
IV, Q, E = ("order", "Place an IV line."), ("question", None), ("examination", None)
WAIT60, WAIT20 = ("order", "Reassess in 60 minutes."), ("order", "Reassess in 20 minutes.")
LITRE15, BLOOD2 = ("order", "Give 1 litre of normal saline over 15 minutes."), ("order", "Transfuse 2 units of packed red cells.")
UNSUPPORTED = ("order", "Start norepinephrine at 10 mcg/min.")

#: Seven representative encounters, not dozens. ``series`` names the management script already run and certified in ``PHASE3_PRESSURE_AUTHORITY_SERIES.json``; ``expected`` is what that certified
#: run did (a faculty reviewer sees it BEFORE the encounter only as the educational purpose, never as a target to match).
SCENARIOS = (
    {"id": "FR-A", "case_id": "gi_bleed_57m", "series": "untreated", "steps": (WAIT60,) * 5, "expected": "HALTED_AT_COLLAPSE_BOUNDARY",
     "title": "57-year-old man, untreated deterioration",
     "reason": "Does an untreated bleed deteriorate in a clinically coherent direction and at an acceptable pace, and does the experiment stop at an understandable point before the patient state the pressure authority "
               "cannot represent? Also the main halt-experience review."},
    {"id": "FR-B", "case_id": "gi_bleed_57m", "series": "early_treatment", "steps": (IV, LITRE15, BLOOD2, WAIT20), "expected": "ACTIVE_TO_THE_END",
     "title": "57-year-old man, early treatment",
     "reason": "Does early volume and blood replacement produce a pressure response that begins at an appropriate time and has a plausible size?"},
    {"id": "FR-C", "case_id": "gi_bleed_57m", "series": "delayed_treatment", "steps": (WAIT60, WAIT60, IV, LITRE15, BLOOD2, WAIT20), "expected": "ACTIVE_TO_THE_END",
     "title": "57-year-old man, delayed treatment",
     "reason": "After two hours without treatment, is the deterioration and then the response to the same treatment plausible, and does a resident risk being misled by the trajectory?"},
    {"id": "FR-D", "case_id": "gi_bleed_72f", "series": "untreated", "steps": (WAIT60,) * 5, "expected": "HALTED_AT_COLLAPSE_BOUNDARY",
     "title": "72-year-old woman, untreated deterioration",
     "reason": "The same question as FR-A for the second authored case, so a reviewer can tell a case-specific problem from a general one."},
    {"id": "FR-E", "case_id": "gi_bleed_72f", "series": "recovery", "steps": (WAIT60, WAIT60, IV, LITRE15, BLOOD2, ("order", "Reassess in 30 minutes.")), "expected": "ACTIVE_TO_THE_END",
     "title": "72-year-old woman, delayed treatment and recovery",
     "reason": "Is the recovery after delayed treatment coherent in direction, timing and magnitude, and is the common consciousness comparison plausible beside it?"},
    {"id": "FR-F", "case_id": "gi_bleed_57m", "series": "unsupported_action", "steps": (Q, UNSUPPORTED, Q), "expected": "HALTED_BY_UNSUPPORTED_ACTION",
     "title": "57-year-old man, an action the experiment cannot judge",
     "reason": "An effective stop by an operational cause (a vasopressor the pressure authority does not represent), not by the patient's state: is the halt understandable and free of clinical or terminal wording?"},
    {"id": "FR-G", "case_id": "gi_bleed_72f", "series": "long_infusion", "steps": (IV, ("order", "Give 1 litre of normal saline over 60 minutes. Reassess in 60 minutes."), ("order", "Reassess in 10 minutes.")),
     "expected": "ACTIVE_TO_THE_END",
     "title": "72-year-old woman, long infusion",
     "reason": "A single order that spans a long interval: is the pressure trajectory across the whole infusion plausible, and is the response timed with the volume given?"},
)


def scenario(identifier: str) -> dict | None:
    return next((dict(item) for item in SCENARIOS if item["id"] == str(identifier)), None)


def scenario_problems() -> list:
    """What is wrong with the scripted set: a case outside the allowlist, a duplicate id, a missing reason, more than seven encounters or fewer than five. Empty means the set is as decided."""
    problems, seen = [], set()
    if not 5 <= len(SCENARIOS) <= 7:
        problems.append(f"the review set must have 5 to 7 encounters, it has {len(SCENARIOS)}")
    for item in SCENARIOS:
        if item["id"] in seen:
            problems.append(f"{item['id']} is duplicated")
        seen.add(item["id"])
        if not case_allowed(item["case_id"]):
            problems.append(f"{item['id']} names a case outside the allowlist: {item['case_id']}")
        if len(str(item.get("reason") or "")) < 40:
            problems.append(f"{item['id']} does not explain its educational reason")
    return problems
