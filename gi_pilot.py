"""P3-519 to P3-527: the CONTROLLED DEVELOPMENT PILOT of the GI management trace -- its scope, the configuration it needs, the development
boundary before definitive control of the bleeding, the classification of what a participant sees, the de-identified pilot record, the
replay check and the fail-safe rules. Pure: no Streamlit, no page; the page reaches it through ``gi_pilot_ui``.

Faculty decisions FD-PILOT-01 to FD-PILOT-08 (2026-11-22). ``GI_MANAGEMENT_TRACE_V1`` is RATIFIED FOR CONTROLLED DEVELOPMENT PILOT
PREPARATION only: not a clinical validation, not a production approval and not a resident deployment. What this module adds is a
development mode that is OFF unless an operator names it (``FLAG``), refuses any configuration it cannot verify, and changes nothing
for any other encounter:

* one authored case (``PILOT_CASES``) under the live development pressure authority and the manual norepinephrine control exactly as
  published (no physiology, calibration, grant, snapshot, reader or engine change);
* a boundary BEFORE the engine could execute an unreviewed definitive control of the bleeding (FD-PILOT-04, H1): the turn that requests
  it is recorded and NOT carried out, and the encounter ends; a second, structural barrier ends it if the engine state ever shows a
  definitive-control consultation or a haemostasis event anyway;
* mental status is classified as the earlier (legacy) model's on every pilot surface, and withheld once norepinephrine has been given
  (FD-PILOT-05, H2); the other non-pressure signs are classified as the earlier model's;
* the management trace shown after the encounter is the faculty-reviewed construct (``development_management_trace``): no category,
  no score, no internal variable;
* a pilot record that names no person: a pseudonymous participant reference, synthetic encounter ids, append-only hash-chained logs
  kept apart for the participant's session and the supervising faculty, so the two never write the same file;
* the encounter never creates an attempt in the participant's account: it reaches no progress, portfolio, rubric or evaluation surface
  (FD-PILOT-08).
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

try:                                   # POSIX: the pilot logs are locked across processes too (P3-531 F3)
    import fcntl
except ImportError:                    # pragma: no cover - the pilot runs on Linux
    fcntl = None

import development_management_trace as mt

VERSION = "P3-520"
PILOT_ID = "GI_MANAGEMENT_TRACE_CONTROLLED_DEVELOPMENT_PILOT_V1"
RATIFIED_CONSTRUCT = "GI_MANAGEMENT_TRACE_V1"
RATIFIED_STATUS = "RATIFIED_FOR_CONTROLLED_DEVELOPMENT_PILOT_PREPARATION"
DECISIONS = "FD-PILOT-01 to FD-PILOT-08"
ROOT = Path(__file__).resolve().parent

#: The operator's switch. Any other non-empty value is a REQUEST that is refused (a typo never runs a half-configured pilot).
FLAG = "MRS_PHASE3_GI_PILOT"
MODE_ON = "on"
#: The pilot record's directory: required, absolute, outside the repository.
STORE_FLAG = "MRS_PHASE3_GI_PILOT_STORE"
#: The authored challenge and the ONE case of the first pilot (P3-527): the case of the ten faculty-reviewed paths.
CHALLENGE_ID = "R2-05"
PILOT_CASES = ("gi_bleed_57m",)
HORIZON_MIN = mt.HORIZON_MIN

# -- P3-532: what the pilot reads of the Phase-3 layer ------------------------------------------------------------------------------------
#
# The pilot modules import NOTHING of the Phase-3 authority, store or shadow layer: the page's one crossing into it (``app.py``) hands them a ``Layer``, exactly as it hands
# the faculty review pages theirs. The published configuration is named below; ``test_gi_pilot`` pins each name to the layer's own constant.

PRESSURE_SNAPSHOT_ID = "GI_JOINT_PRESSURE_DEVELOPMENT_SNAPSHOT_V1"          # runtime_pressure_snapshot.SNAPSHOT_ID (FD-PROMOTE-01)
TONE_SNAPSHOT_ID = "COMMON_TONE_DEVELOPMENT_SNAPSHOT_V1"                    # runtime_tone_snapshot.SNAPSHOT_ID (FD-TONE-RATIFY)
NOREPINEPHRINE_GRANT_ID = "GI_NOREPINEPHRINE_DEVELOPMENT_AUTHORITY_GRANT_V1"  # runtime_ne_grant.GRANT_ID (FD-AUTHNE-01)
AUTHORITY_STORE_FLAG = "MRS_PHASE3_AUTHORITY_STORE"                         # runtime_authority_store.STORE_FLAG
DEVELOPMENT_ENVIRONMENT = "development"


@dataclass(frozen=True)
class Layer:
    """What the pilot reads of the Phase-3 layer, handed over by the page's one crossing into it. Names, pure checks, the verification and replay of a STORED artifact, and
    this encounter's site through the page's own helper (``app._runtime_authority_site``, the call the page makes on every turn, which orchestrates and decides nothing).
    No member opens, advances, commits or writes an authority of its own: the pilot can only read what the page's crossing already does."""
    pilot_flags: tuple
    deployment_markers: Callable[[], Sequence[str]]
    looks_like_the_pilot: Callable[[Mapping], tuple]
    configuration: tuple                    # ((flag, published value), ...): the published development configuration
    derived_map: Callable[[Any, Any], Any]
    site_key: str
    site: Callable[[], Any]
    verify_artifact: Callable[[Mapping], Mapping]
    replay_site_artifact: Callable[[Mapping], Mapping]


#: The members a ``Layer`` carries; ``test_gi_pilot`` proves none of them is a writer of the authority.
LAYER_MEMBERS = ("pilot_flags", "deployment_markers", "looks_like_the_pilot", "configuration", "derived_map", "site_key", "site", "verify_artifact", "replay_site_artifact")


def layer_from(authority: Any, shadow: Any, site: Callable[[], Any]) -> Layer:
    """The ``Layer`` the page's crossing hands over: ``authority`` and ``shadow`` are the layer modules THE PAGE imported; ``site`` is the page's own helper. Only the
    members named in ``LAYER_MEMBERS`` are kept; the modules themselves are not."""
    return Layer(
        pilot_flags=tuple(authority.PILOT_FLAGS),
        deployment_markers=authority.pilot_deployment_markers,
        looks_like_the_pilot=authority.looks_like_the_pilot,
        configuration=((authority.AUTHORITY_FLAG, authority.MODE_LIMITED_COMMON_AUTHORITY), (authority.SNAPSHOT_FLAG, PRESSURE_SNAPSHOT_ID),
                       (authority.TONE_FLAG, TONE_SNAPSHOT_ID), (authority.ENVIRONMENT_FLAG, DEVELOPMENT_ENVIRONMENT), (shadow.FLAG, shadow.MODE_SHADOW_COMPARE)),
        derived_map=authority.derived_map,
        site_key=str(authority.SITE_KEY),
        site=site,
        verify_artifact=authority.verify_artifact,
        replay_site_artifact=authority.replay_site_artifact,
    )
#: Session keys. The ``phase3_`` prefix keeps them out of the transactional turn's working copy (``runtime_authority_turn``): a discarded
#: turn never takes back what the pilot record already logged.
SESSION_KEY = "phase3_gi_pilot"
DECISION_KEY = "phase3_gi_pilot_decision"
ASSIGNMENT_REASON = "gi_development_pilot"
PARTICIPANT_ROLES = ("resident",)
FACULTY_ROLES = ("faculty", "admin")

# -- P3-520: scope ------------------------------------------------------------------------------------------------------------------------

INCLUDED, EXCLUDED, DEFERRED = "INCLUDED", "EXCLUDED", "DEFERRED"
SCOPE = {
    "cases": {INCLUDED: ["gi_bleed_57m (the case of the ten faculty-reviewed management paths)"],
              DEFERRED: ["gi_bleed_72f (live-authority case, but not part of the human management-trace review)"],
              EXCLUDED: ["every other family and case", "pump-limited vasopressor cases", "pulmonary edema vasopressor use", "ACS vasopressor use", "generated cases"]},
    "interventions": {INCLUDED: ["crystalloid with a stated volume and duration", "packed red cells", "norepinephrine START / INCREASE / DECREASE / STOP / RESTART at explicit absolute rates in mcg/min",
                                 "reassessment with a stated interval", "history, examination and the case's own tests (earlier simulator model)"],
                      EXCLUDED: ["definitive control of the bleeding (endoscopy, interventional radiology, surgery): a request is the development boundary", "other vasopressors",
                                 "target-based norepinephrine titration (MAP or SBP targets)", "weight-based norepinephrine dosing (mcg/kg/min)", "automatic or closed-loop titration"],
                      DEFERRED: ["source control", "any intervention not reviewed with the live development authority"]},
    "visible_outputs": {INCLUDED: ["blood pressure and MAP from the live development pressure authority", "the other signs from the earlier simulator model, labelled as such",
                                   "mental status labelled as the earlier model's, and withheld once norepinephrine has been given", "the development boundary message",
                                   "after the encounter: the faculty-reviewed management trace"],
                        EXCLUDED: ["internal model variables (V, T, tone gain, pressure scale, bleed-rate coordinate, crystalloid kernel, oxygen debt)", "grant, snapshot and lineage identifiers",
                                   "the faculty management categories", "any score, rubric, ranking, radar or count", "patient photographs (the image bank is off)",
                                   "the legacy post-encounter review layer (guided self-review prompts, expert comparison drafts, AI analysis)", "any AI call"],
                        DEFERRED: ["Spanish presentation of the pilot texts (TD-46)", "consciousness derived from the development pressure"]},
    "trace_fields": {INCLUDED: ["state", "the participant's priority, expected effect and reassessment exactly as written (or 'not expressed')", "action as typed, each order with what the simulator did with it",
                                "expected effect (model)", "observed pressure (a committed minute of the live development authority)", "reassessment reading", "new state", "the development boundary"],
                     EXCLUDED: ["scenario priorities of authored paths", "proposed management categories", "provenance identifiers, digests, grant and snapshot ids", "mental status, consciousness, heart rate"]},
    "faculty_controls": {INCLUDED: ["observe an encounter (refreshable)", "stop an encounter", "inspect the trace", "flag an output as unsafe or ambiguous", "mark an encounter unusable", "review the replay"],
                         DEFERRED: ["live co-presence in the participant's screen", "a signed record (needs a key: faculty decision)"]},
}

# -- P3-522: what a participant sees, classified ------------------------------------------------------------------------------------------

AUTHORITATIVE, LEGACY_NONAUTHORITATIVE, DEVELOPMENT_ONLY, HIDDEN = "AUTHORITATIVE", "LEGACY_NONAUTHORITATIVE", "DEVELOPMENT_ONLY", "HIDDEN"
FIELD_CLASSES = (
    ("blood pressure (SBP/DBP) and MAP", AUTHORITATIVE, "committed minutes of the live development pressure authority; MAP derived from them"),
    ("heart rate and rhythm", LEGACY_NONAUTHORITATIVE, "earlier simulator model; covered by the pilot notice"),
    ("SpO2, respiratory support, respiratory rate, work of breathing", LEGACY_NONAUTHORITATIVE, "earlier simulator model; covered by the pilot notice"),
    ("capillary refill, extremities, skin, appearance", LEGACY_NONAUTHORITATIVE, "earlier simulator model; covered by the pilot notice"),
    ("mental status", LEGACY_NONAUTHORITATIVE, "labelled as the earlier model's; WITHHELD once norepinephrine has been given (FD-PILOT-05, H2)"),
    ("laboratory and bedside test results, history, examination", LEGACY_NONAUTHORITATIVE, "earlier simulator model; covered by the pilot notice"),
    ("event narrative (patient response, receipts of orders)", LEGACY_NONAUTHORITATIVE, "earlier simulator model; the pressure in it is the authority's"),
    ("development boundary, pilot notice, faculty-stop notice", DEVELOPMENT_ONLY, "development wording, no clinical outcome"),
    ("management trace after the encounter", DEVELOPMENT_ONLY, "the faculty-reviewed construct; no category and no score"),
    ("V, T, tone gain, pressure scale, bleed-rate coordinate, crystalloid kernel, oxygen debt", HIDDEN, "never on a participant screen"),
    ("grant, snapshot, lineage, artifact and digest identifiers", HIDDEN, "faculty supervision only"),
    ("common-core consciousness (V1 overlay)", HIDDEN, "nonauthoritative comparison only; never shown to the participant"),
    ("faculty management categories", HIDDEN, "faculty interpretations (FD-PILOT-03); never shown to the participant, never a score"),
    ("participant reference, encounter id", HIDDEN, "faculty supervision only"),
)

PILOT_NOTICE = ("Development pilot · synthetic patient · supervised by faculty · not an assessment: nothing here counts toward any grade. Blood pressure comes from the development "
                "pressure model the faculty reviewed. The other signs, including mental status, come from the earlier simulator model and are not validated with it. "
                "Do not write personal information.")
MENTAL_STATUS_LABEL = "MENTAL STATUS · EARLIER MODEL"
MENTAL_STATUS_WITHHELD = "Not shown on vasopressor"
MENTAL_STATUS_WITHHELD_NOTE = ("Mental status is not shown once norepinephrine has been given in this development pilot: the development model does not yet represent it under a "
                               "vasopressor, and the earlier model's word could mislead.")
UPDATE_MENTAL_LEGACY = "{word} (mental status from the earlier simulator model)"
UPDATE_MENTAL_WITHHELD = "Mental status not shown (development pilot, on vasopressor)"
APPEARANCE_MENTAL_LEGACY = "Mental status (earlier model): {word}"
APPEARANCE_MENTAL_WITHHELD = "Mental status: not shown (development pilot, on vasopressor)"


def norepinephrine_given(ledger: Sequence[Mapping] | None) -> bool:
    """Whether any norepinephrine order of this encounter was carried out (read from the order ledger the engine settled)."""
    for order in ledger or ():
        try:
            if str(order.get("fate") or "") == "EXECUTED" and "norepinephrine" in f"{order.get('canonical') or ''} {order.get('class') or ''}".lower():
                return True
        except AttributeError:
            continue
    return False


def display_cells(cells: Sequence, ne_given: bool, mental_labels: Sequence[str] = ("MENTAL STATUS",)) -> tuple:
    """The monitor grid as a participant reads it in the pilot: the mental-status cell relabelled as the earlier model's, or withheld after norepinephrine."""
    out = []
    for label, value in cells:
        if str(label) in tuple(mental_labels):
            out.append((MENTAL_STATUS_LABEL, MENTAL_STATUS_WITHHELD if ne_given else value))
        else:
            out.append((label, value))
    return tuple(out)


#: The words the earlier model writes for mental status (``family_engine`` and the authored cases). Used ONLY to fail closed on a sentence the pilot does not know, after
#: norepinephrine; ``test_gi_pilot`` pins that it covers the engine's own ladder.
MENTAL_WORDS = ("Alert", "Drowsy", "Obtunded", "Unresponsive", "Agitated", "Sedated", "Comatose", "Confused", "Lethargic", "Anxious", "Not recorded")
#: The engine's patient-response sentence: ``... RR n/min. <word>; respiratory effort ...`` (``family_engine.clinical_update``).
UPDATE_MENTAL = re.compile(r"(?<=/min\. )(?P<word>[A-Za-z][A-Za-z ,'-]*?)(?=; respiratory effort)")


def display_update_text(text: str, ne_given: bool) -> str:
    """The engine's patient-response sentence with its mental-status word classified as the earlier model's, or withheld after norepinephrine. A pure text transform (P3-532):
    it reads no mental-status field, it classifies or withholds the phrase the inventoried readers already wrote. The stored record is untouched."""
    text = str(text or "")
    if ne_given:
        text = UPDATE_MENTAL.sub(UPDATE_MENTAL_WITHHELD, text, count=1)
        # and anywhere else (a sentence this function does not know, or a second mention): fail closed, never let the earlier model's word stand after norepinephrine
        return re.sub(r"\b(?:" + "|".join(re.escape(word) for word in MENTAL_WORDS) + r")\b", UPDATE_MENTAL_WITHHELD, text, flags=re.IGNORECASE)
    return UPDATE_MENTAL.sub(lambda match: UPDATE_MENTAL_LEGACY.format(word=match.group("word")), text, count=1)


APPEARANCE_MENTAL = re.compile(r"Mental status:\s*(?P<word>[A-Za-z]+)")


def display_appearance(summary: str, ne_given: bool) -> str:
    """The room's appearance line ``Mental status: <Word>`` classified as the earlier model's, or withheld after norepinephrine. A pure text transform (P3-532)."""
    summary = str(summary or "")
    if ne_given:
        return APPEARANCE_MENTAL.sub(APPEARANCE_MENTAL_WITHHELD, summary, count=1)
    return APPEARANCE_MENTAL.sub(lambda match: APPEARANCE_MENTAL_LEGACY.format(word=match.group("word").capitalize()), summary, count=1)


EXAM_ENGAGEMENT = re.compile(r"\s*(?:The patient engages in conversation and follows commands\.|Engagement is reduced; interpret alongside respiratory and circulatory findings\.)")
EXAM_CURRENT = re.compile(r"Current mental status:\s*[A-Za-z ]+\.")
EXAM_MENTAL_WITHHELD = "Mental status: not shown (development pilot, on vasopressor)."


def display_examination(text: str, ne_given: bool) -> str:
    """An examination event as a pilot participant reads it: the earlier model's mental-status words classified as such, or withheld (with the engagement sentence derived from
    them) once norepinephrine has been given. The stored event is untouched."""
    text = str(text or "")
    if ne_given:
        text = EXAM_ENGAGEMENT.sub("", text)
        text = EXAM_CURRENT.sub(EXAM_MENTAL_WITHHELD, text)
        text = re.sub(r"Mental status:\s*(?!not shown)[A-Za-z]+", APPEARANCE_MENTAL_WITHHELD, text)
        return text
    text = EXAM_CURRENT.sub(lambda match: match.group(0).replace("Current mental status:", "Current mental status (earlier model):"), text)
    return re.sub(r"Mental status:\s*(?=[A-Za-z])", "Mental status (earlier model): ", text)


# -- P3-520 / P3-526: configuration, fail closed ------------------------------------------------------------------------------------------

def _inside_repository(path: Path) -> bool:
    try:
        path.resolve().relative_to(ROOT)
        return True
    except ValueError:
        return False


def store_root(environ: Mapping[str, str] | None = None) -> tuple:
    """(path, problem): the pilot record directory, created if missing. Relative paths, the repository and an unwritable place are refused."""
    environ = os.environ if environ is None else environ
    raw = str(environ.get(STORE_FLAG, "") or "").strip()
    if not raw:
        return None, f"{STORE_FLAG} is not set: the pilot cannot run without its record"
    path = Path(raw)
    if not path.is_absolute():
        return None, f"{STORE_FLAG} must be an absolute directory"
    if _inside_repository(path):
        return None, f"{STORE_FLAG} must be outside the repository (the pilot record is never committed)"
    try:
        path.mkdir(parents=True, exist_ok=True)
        probe = path / f".write-check-{os.getpid()}-{threading.get_ident()}-{secrets.token_hex(4)}"     # unique per call: the sessions are threads of one process (P3-531 F3)
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
    except OSError as error:
        return None, f"the pilot record directory cannot be written ({type(error).__name__})"
    return path, ""


def evaluate(environ: Mapping[str, str] | None = None, *, accounts: bool, on_cloud: bool, secret: Any = None, layer: Layer | None = None) -> dict:
    """The pilot mode decision for this process: ``{"requested", "enabled", "problems"}``. Never raises; refuses whatever it cannot verify.

    ``secret(name)`` reads a deployment secret (the page passes its own reader) so that an AI key or the image bank held in secrets is seen
    too. The live development authority still decides on its own, per encounter; this only refuses to START a pilot that could not be the
    one the faculty authorized. ``layer`` is what the page's crossing hands over (P3-532); without it a requested pilot is refused."""
    environ = os.environ if environ is None else environ
    raw = str(environ.get(FLAG, "") or "").strip()
    if not raw:
        return {"requested": False, "enabled": False, "problems": []}
    problems = []
    if raw.lower() != MODE_ON:
        problems.append(f"{FLAG} must be '{MODE_ON}'")
    if not accounts:
        problems.append("individual accounts are required (participant references and faculty supervision depend on them)")
    if on_cloud:
        problems.append("the pilot never runs on a hosted public deployment")

    def _sources(name):
        """Every value ``name`` has where the page could read it: the environment AND the deployment's secrets (the image bank and the AI key read secrets first,
        the pilot flags the environment; a refusal must not depend on which one the operator used -- P3-531 F4, F5)."""
        values = []
        value = str(environ.get(name, "") or "").strip()
        if value:
            values.append(value)
        if secret is not None:
            try:
                value = str(secret(name) or "").strip()
            except Exception:
                value = "unreadable"
            if value:
                values.append(value)
        return values
    if _sources("MRS_FACULTY_DEVELOPMENT_REVIEW"):
        problems.append("the faculty development review environment is a separate mode; it is not combined with the pilot")
    try:
        if layer is None:
            raise LookupError("the page handed over no layer")
        seen = dict(environ)
        for name in tuple(layer.pilot_flags) + tuple(layer.deployment_markers() or ()):
            if not str(seen.get(name, "") or "").strip() and _sources(name):
                seen[name] = _sources(name)[0]                     # a pilot flag held only in secrets counts as set
        is_first_pilot, why = layer.looks_like_the_pilot(seen)
        if is_first_pilot:
            problems.append("this deployment looks like the first resident pilot (" + why + "): the development authority never runs there")
        for name, value in layer.configuration:
            if str(environ.get(name, "") or "").strip() != value:
                problems.append(f"{name} must name the published development configuration ({value})")
        if not str(environ.get(AUTHORITY_STORE_FLAG, "") or "").strip():
            problems.append(f"{AUTHORITY_STORE_FLAG} must name the development authority's record directory (without it no pilot encounter can open its authority)")
    except Exception as error:                                      # an unreadable authority layer is a refusal, never a pilot without its authority
        problems.append(f"the development authority configuration cannot be read ({type(error).__name__})")
    _, store_problem = store_root(environ)
    if store_problem:
        problems.append(store_problem)
    if _sources("OPENAI_API_KEY"):
        problems.append("no AI call is part of the pilot: OPENAI_API_KEY must not be configured")
    bank = _sources("MRS_IMAGE_BANK")
    if not bank or any(value.lower() not in {"off", "0", "false", "no"} for value in bank):
        problems.append("patient photographs are excluded from the pilot: MRS_IMAGE_BANK must be off wherever it is set")
    return {"requested": True, "enabled": not problems, "problems": problems, "pilot_id": PILOT_ID, "version": VERSION}


# -- P3-525: the pilot record (de-identified, append-only, hash-chained) ------------------------------------------------------------------

def participant_ref(user_id: Any) -> str:
    """A pseudonymous participant reference: never the account id, the username or a name. Re-linking it needs the account database."""
    return "P-" + hashlib.sha256(f"{PILOT_ID}:participant:{user_id}".encode()).hexdigest()[:12]


def faculty_ref(user_id: Any) -> str:
    return "F-" + hashlib.sha256(f"{PILOT_ID}:faculty:{user_id}".encode()).hexdigest()[:12]


def plain(value: Any) -> Any:
    """``value`` as plain JSON data: read-only mappings and tuples become dicts and lists, nothing else changes (a stringified mapping would break every digest)."""
    if isinstance(value, Mapping):
        return {str(key): plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [plain(item) for item in value]
    return value


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)


def digest_of(value: Any) -> str:
    return hashlib.sha256(_canonical(value).encode()).hexdigest()


ENCOUNTER_ID = re.compile(r"^PE-[0-9a-f]{16}$")
RESIDENT_LOG, FACULTY_LOG, META, ARTIFACT, TRACE = "participant.jsonl", "faculty.jsonl", "meta.json", "artifact.json", "trace.json"

# What a participant session writes (kinds), and what a faculty member writes (actions). Never the other's.
RESIDENT_KINDS = ("started", "turn", "boundary", "ended", "interrupted", "left")
FACULTY_ACTIONS = ("observe", "stop", "flag", "unusable", "replay_review", "inspect_trace")
FLAG_CATEGORIES = ("UNSAFE", "AMBIGUOUS")

#: Exits of a pilot encounter. Every one ends it; none is a patient outcome.
EXIT_DEFINITIVE_REQUEST = "DEFINITIVE_CONTROL_REQUESTED"
EXIT_ENGINE_SOURCE_CONTROL = "ENGINE_SOURCE_CONTROL_DETECTED"
EXIT_HORIZON = "DEVELOPMENT_HORIZON"
EXIT_AUTHORITY_STOP = "AUTHORITY_STOP"
EXIT_AUTHORITY_UNAVAILABLE = "AUTHORITY_UNAVAILABLE"
EXIT_FACULTY_STOP = "FACULTY_STOP"
EXIT_RECORD_UNAVAILABLE = "PILOT_RECORD_UNAVAILABLE"
EXIT_PARTICIPANT_FINISHED = "PARTICIPANT_FINISHED"
EXIT_LEGACY_TERMINAL = "LEGACY_ENGINE_CLOSED"
EXIT_CLOSED_IN_RECORD = "ENCOUNTER_CLOSED_IN_RECORD"
EXITS = (EXIT_DEFINITIVE_REQUEST, EXIT_ENGINE_SOURCE_CONTROL, EXIT_HORIZON, EXIT_AUTHORITY_STOP, EXIT_AUTHORITY_UNAVAILABLE, EXIT_FACULTY_STOP, EXIT_RECORD_UNAVAILABLE,
         EXIT_PARTICIPANT_FINISHED, EXIT_LEGACY_TERMINAL, EXIT_CLOSED_IN_RECORD)

FACULTY_STOP_MESSAGE = ("The supervising faculty member ended this development encounter. It is not a judgement of your management and not a statement about the patient. "
                        "What you did up to this point is kept.")
CLOSED_IN_RECORD_MESSAGE = ("This development encounter was already closed in the pilot record (a new pilot encounter was started, or it was left), so it does not "
                            "continue here and nothing more is carried out. It is not a judgement of your management. Tell the supervising faculty member.")
RECORD_UNAVAILABLE_MESSAGE = ("The development pilot record cannot be written, so this development encounter stops here and nothing more is carried out. Tell the supervising faculty member.")
AUTHORITY_UNAVAILABLE_MESSAGE = ("The development pressure model is not available for this encounter, so the development pilot does not run it. Tell the supervising faculty member.")
DEFINITIVE_MESSAGE = mt.BOUNDARY_MESSAGE_REQUEST + " The orders of that turn were recorded and not carried out."
ENGINE_SOURCE_CONTROL_MESSAGE = mt.HAEMOSTASIS_EVENT_MESSAGE
FINISHED_MESSAGE = ("You ended this development encounter. The bleeding has not been controlled in this encounter: definitive control of the bleeding source is outside this "
                    "development model. Ending here does not mean that the patient has recovered, that the bleeding has stopped, that management is complete, or that discharge is safe.")
EXIT_MESSAGES = {EXIT_DEFINITIVE_REQUEST: DEFINITIVE_MESSAGE, EXIT_ENGINE_SOURCE_CONTROL: ENGINE_SOURCE_CONTROL_MESSAGE, EXIT_HORIZON: mt.BOUNDARY_MESSAGE,
                 EXIT_AUTHORITY_STOP: mt.AUTHORITY_STOP_MESSAGE, EXIT_AUTHORITY_UNAVAILABLE: AUTHORITY_UNAVAILABLE_MESSAGE, EXIT_FACULTY_STOP: FACULTY_STOP_MESSAGE,
                 EXIT_RECORD_UNAVAILABLE: RECORD_UNAVAILABLE_MESSAGE, EXIT_PARTICIPANT_FINISHED: FINISHED_MESSAGE, EXIT_LEGACY_TERMINAL: mt.TERMINAL_MESSAGE,
                 EXIT_CLOSED_IN_RECORD: CLOSED_IN_RECORD_MESSAGE}


class PilotRecordError(Exception):
    """The pilot record cannot be read or written as it must be: the caller fails closed."""


def _read_chain(path: Path) -> tuple:
    """(entries, problems) of one append-only log; every line carries the digest of the line before it."""
    entries, problems, previous = [], [], ""
    if not path.exists():
        return entries, problems
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as error:
        return entries, [f"{path.name} cannot be read ({type(error).__name__})"]
    for number, line in enumerate(lines, 1):
        try:
            entry = json.loads(line)
        except ValueError:
            problems.append(f"{path.name} line {number} is not JSON")
            break
        body = {key: value for key, value in entry.items() if key != "digest"}
        if entry.get("prev") != previous or entry.get("digest") != digest_of(body) or entry.get("seq") != number:
            problems.append(f"{path.name} line {number} breaks the chain")
            break
        entries.append(entry)
        previous = entry["digest"]
    return entries, problems


_APPEND_LOCK = threading.Lock()


def _append(path: Path, entry: dict) -> dict:
    """Read the chain and append to it as ONE step: serialized across the session threads of the process and locked across processes, so two writers never take the same
    place in the chain (P3-531 F3)."""
    with _APPEND_LOCK:
        try:
            handle = path.open("a", encoding="utf-8")
        except OSError as error:
            raise PilotRecordError(f"{path.name} cannot be written ({type(error).__name__})") from error
        with handle:
            try:
                if fcntl is not None:
                    fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
                entries, problems = _read_chain(path)
                if problems:
                    raise PilotRecordError("; ".join(problems))
                body = {"seq": len(entries) + 1, "prev": entries[-1]["digest"] if entries else "", "at": _now(), **entry}
                body["digest"] = digest_of(body)
                handle.write(_canonical(body) + "\n")
                handle.flush()
                os.fsync(handle.fileno())
            except OSError as error:
                raise PilotRecordError(f"{path.name} cannot be written ({type(error).__name__})") from error
    return body


def _write_json(path: Path, value: Any) -> None:
    tmp = path.with_suffix(path.suffix + f".tmp-{os.getpid()}-{threading.get_ident()}-{secrets.token_hex(4)}")
    try:
        tmp.write_text(json.dumps(value, indent=1, sort_keys=True, ensure_ascii=False, default=str), encoding="utf-8")
        os.replace(tmp, path)
    except OSError as error:
        raise PilotRecordError(f"{path.name} cannot be written ({type(error).__name__})") from error


class PilotStore:
    """The pilot record under one directory: ``encounters/<PE-id>/`` with the participant session's log, the faculty log, the meta, the latest authority artifact and the closing trace.

    It holds NO name, username, e-mail or account id: the participant and the faculty are pseudonymous references. The resident's free text (orders and stated reasoning) is the
    encounter itself and is kept, which is why the pilot notice asks for no personal information."""

    def __init__(self, root: Path | str):
        self.root = Path(root)
        self.encounters = self.root / "encounters"

    def _dir(self, eid: str) -> Path:
        if not ENCOUNTER_ID.match(str(eid or "")):
            raise PilotRecordError("not a pilot encounter id")
        return self.encounters / eid

    def new_encounter(self, *, participant: str, case_id: str, arrival: Mapping, configuration: Mapping) -> str:
        if case_id not in PILOT_CASES:
            raise PilotRecordError("not a pilot case")
        for _ in range(5):
            eid = "PE-" + secrets.token_hex(8)
            folder = self.encounters / eid
            try:
                folder.mkdir(parents=True, exist_ok=False)
                break
            except FileExistsError:
                continue
            except OSError as error:
                raise PilotRecordError(f"the pilot record cannot be created ({type(error).__name__})") from error
        else:
            raise PilotRecordError("no free encounter id")
        meta = {"pilot_id": PILOT_ID, "version": VERSION, "encounter_id": eid, "participant": participant, "case_id": case_id, "challenge_id": CHALLENGE_ID,
                "arrival": {key: arrival.get(key) for key in ("sbp", "dbp", "map")}, "configuration": dict(configuration), "created_at": _now()}
        _write_json(folder / META, meta)
        self.append_participant(eid, "started", {"case_id": case_id, "arrival": meta["arrival"]})
        return eid

    def append_participant(self, eid: str, kind: str, payload: Mapping) -> dict:
        if kind not in RESIDENT_KINDS:
            raise PilotRecordError(f"not a participant record kind: {kind}")
        return _append(self._dir(eid) / RESIDENT_LOG, {"kind": kind, "payload": dict(payload)})

    def append_faculty(self, eid: str, faculty: str, action: str, payload: Mapping) -> dict:
        if action not in FACULTY_ACTIONS:
            raise PilotRecordError(f"not a faculty action: {action}")
        if not str(faculty or "").startswith("F-"):
            raise PilotRecordError("a faculty action needs a faculty reference")
        if action == "flag" and str(dict(payload).get("category")) not in FLAG_CATEGORIES:
            raise PilotRecordError("a flag is UNSAFE or AMBIGUOUS")
        return _append(self._dir(eid) / FACULTY_LOG, {"action": action, "faculty": faculty, "payload": dict(payload)})

    def write_artifact(self, eid: str, artifact: Mapping) -> None:
        _write_json(self._dir(eid) / ARTIFACT, dict(artifact))

    def write_trace(self, eid: str, trace: Mapping) -> None:
        path = self._dir(eid) / TRACE
        if path.exists():
            stored = json.loads(path.read_text(encoding="utf-8"))
            if stored.get("trace_digest") != dict(trace).get("trace_digest"):
                raise PilotRecordError("a different closing trace is already recorded for this encounter")
            return
        _write_json(path, dict(trace))

    def meta(self, eid: str) -> dict:
        try:
            return json.loads((self._dir(eid) / META).read_text(encoding="utf-8"))
        except (OSError, ValueError) as error:
            raise PilotRecordError(f"the encounter meta cannot be read ({type(error).__name__})") from error

    def logs(self, eid: str) -> dict:
        participant, p_problems = _read_chain(self._dir(eid) / RESIDENT_LOG)
        faculty, f_problems = _read_chain(self._dir(eid) / FACULTY_LOG)
        return {"participant": participant, "faculty": faculty, "problems": p_problems + f_problems}

    def artifact(self, eid: str) -> dict | None:
        path = self._dir(eid) / ARTIFACT
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def closing_trace(self, eid: str) -> dict | None:
        path = self._dir(eid) / TRACE
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None

    def controls(self, eid: str) -> dict:
        """What the faculty decided for this encounter. Raises (the caller fails closed) when the faculty log cannot be trusted."""
        faculty, problems = _read_chain(self._dir(eid) / FACULTY_LOG)
        if problems:
            raise PilotRecordError("; ".join(problems))
        return {"stop_requested": any(entry["action"] == "stop" for entry in faculty), "unusable": any(entry["action"] == "unusable" for entry in faculty),
                "flags": [entry["payload"] for entry in faculty if entry["action"] == "flag"]}

    def ids(self) -> list:
        if not self.encounters.exists():
            return []
        return sorted(path.name for path in self.encounters.iterdir() if path.is_dir() and ENCOUNTER_ID.match(path.name))

    def status(self, eid: str) -> dict:
        """The encounter as the faculty list shows it; derived from the logs only."""
        meta = self.meta(eid)
        logs = self.logs(eid)
        participant = logs["participant"]
        ended = next((entry for entry in reversed(participant) if entry["kind"] in ("ended", "interrupted", "left")), None)
        turns = [entry for entry in participant if entry["kind"] == "turn"]
        last = turns[-1]["payload"] if turns else {}
        state = ("RECORD_PROBLEM" if logs["problems"] else "ACTIVE" if ended is None else
                 {"ended": "ENDED", "interrupted": "INTERRUPTED", "left": "LEFT"}[ended["kind"]])
        return {"encounter_id": eid, "participant": meta.get("participant"), "case_id": meta.get("case_id"), "created_at": meta.get("created_at"), "state": state,
                "exit": (ended or {}).get("payload", {}).get("exit"), "turns": len(turns), "minute": last.get("minute"), "pressure": last.get("pressure"),
                "stop_requested": any(entry["action"] == "stop" for entry in logs["faculty"]), "unusable": any(entry["action"] == "unusable" for entry in logs["faculty"]),
                "flags": sum(entry["action"] == "flag" for entry in logs["faculty"]), "problems": logs["problems"]}

    def open_encounters_of(self, participant: str) -> list:
        return [eid for eid in self.ids() if self.meta(eid).get("participant") == participant and self.status(eid)["state"] == "ACTIVE"]


# -- P3-521: the development boundary before definitive control of the bleeding ------------------------------------------------------------

def definitive_orders(orders: Sequence[Mapping] | None) -> list:
    """The orders of a turn that request definitive control of the bleeding -- the same rule as the faculty-reviewed trace (``mt.is_definitive_request``), read from the
    turn's ledger entries BEFORE the engine runs, whatever the engine would have done with them."""
    found = []
    for order in orders or ():
        try:
            if mt.is_definitive_request(order):
                found.append(order)
        except Exception:
            continue
    return found


def engine_source_control(state: Mapping | None) -> list:
    """The second, structural barrier: why the engine state shows a definitive-control consultation or a haemostasis anyway (empty when it does not)."""
    family = dict((state or {}).get("family_state") or {})
    reasons = []
    for call in family.get("consultations") or ():
        service = str(dict(call).get("service") or "").lower()
        if service in mt.DEFINITIVE_SERVICES or any(word in service for word in ("gastro", "surg", "radiolog", "endoscop")):
            reasons.append(f"consultation recorded: {service}")
    if family.get("endoscopy_at") is not None:
        reasons.append("an endoscopy was recorded")
    for event in family.get("procedure_events") or ():
        if mt.is_haemostasis_event(dict(event)):
            reasons.append("a haemostasis event was recorded")
    return reasons


# -- P3-523: the trace a participant reads after the encounter ----------------------------------------------------------------------------

FATE_WORDS = {"EXECUTED": "carried out", "RECORDED_NOT_MODELLED": "recorded; its effect is not represented in this development model",
              "UNRECOGNIZED": "not understood by the simulator; nothing was done", "HELD_CLARIFICATION": "held for a question; not carried out",
              "HELD_REASONING": "held until your reasoning was complete", "DUPLICATE_IGNORED": "already in place; not repeated", "NOT_EXECUTED_BOUNDARY":
              "recorded and not carried out (development boundary)", "BLOCKED": "not carried out"}
TRACE_INTRO = ("Your management trace (development pilot). Step by step: the state, what you did, what the model expected, what was observed and the new state. Your own "
               "reasoning appears only where you wrote it; nothing is inferred. This is for reflection with your supervising faculty member: it is not a score, not a grade "
               "and not a judgement of right or wrong. Norepinephrine, where given, supports the pressure only while it runs; fluids and blood do not stop the bleeding; "
               "the bleeding is not controlled in this encounter.")
TRACE_WITHHELD = ("Your management trace cannot be verified against the pilot record, so it is not shown. Your supervising faculty member will review it with you. "
                  "Nothing about your management is implied by this.")
#: Words that must never appear on a participant's trace (a category, a score, an internal, an identifier).
FORBIDDEN_ON_PARTICIPANT_TRACE = ("REASONABLE", "TEMPORIZING", "INCOMPLETE", "NONBENEFICIAL", "score", "grade:", "GRANT", "SNAPSHOT", "tone_gain", "lineage", "digest",
                                  "proposed for faculty review", "Scenario priority", "mental status", "Mental status", "heart rate", "consciousness")


def fate_words(fate: Any) -> str:
    return FATE_WORDS.get(str(fate or ""), "recorded")


def order_label(row: Mapping, spans: Mapping) -> str:
    """How an order is named on the participant's trace: the simulator's reading when it is one ("fluid normal saline 1000 mL"), the participant's own words in quotes when
    the ledger only holds an internal token ("unread", "plan:future_timed", "held_with_question") -- P3-531 F8."""
    reading = str(row.get("order") or "")
    if " " in reading.strip():
        return reading
    span = str(spans.get(row.get("order_id")) or "").strip()
    return f'"{span}"' if span else "an order"


CARRIED_READING_PROBLEM = "step {n}: the new state pressure is labelled as the live authority's without its committed minute"


def carried_reading_tolerated(trace: Mapping, problems: Sequence[str]) -> list:
    """P3-523 (declared, TD-165): the ratified construct's verifier rejects a turn that does not move the clock in the middle of an encounter (an order the simulator did not
    understand, a held order) because its NEW STATE keeps the last committed reading without a commit at that minute. That reading is the authority's, carried unchanged; the
    construct's code is NOT edited (its sealed records pin it). Exactly that problem is dropped, and only when the clock did not move and the new state IS the step's state,
    value, provenance and source; every other problem stands."""
    keep = []
    steps = list(trace.get("steps") or ())
    for problem in problems:
        dropped = False
        for index, step in enumerate(steps):
            if problem != CARRIED_READING_PROBLEM.format(n=index + 1):
                continue
            decision, response = step["decision_minute"]["value"], step["response_minute"]["value"]
            state, new = step["state"]["pressure"], step["new_state"]["pressure"]
            if response <= decision and (state.get("value"), state.get("provenance"), state.get("source")) == (new.get("value"), new.get("provenance"), new.get("source")):
                dropped = True
            break
        if not dropped:
            keep.append(problem)
    return keep


def participant_trace(events: Sequence[Mapping], artifact: Mapping | None, arrival: Mapping) -> dict:
    """The faculty-reviewed trace of a participant's encounter, re-extracted from the page's own events and the authority artifact. ``ok`` is False when it does not verify
    (then nothing is shown to the participant)."""
    turns = [mt.turn_from_page_event(dict(event)) for event in events or ()]
    if not artifact:
        return {"ok": False, "problems": ["no authority artifact"], "trace": None, "blocks": [], "turns": turns}
    try:
        trace = mt.extract(turns, dict(artifact), dict(arrival))
        problems = carried_reading_tolerated(trace, mt.trace_problems(trace, turns))
    except Exception as error:
        return {"ok": False, "problems": [f"the trace cannot be extracted ({type(error).__name__}: {error})"], "trace": None, "blocks": [], "turns": turns}
    blocks = mt.render(trace)
    spans = {order.get("order_id"): order.get("span") for turn in turns for order in turn.get("orders") or () if order.get("order_id") is not None}
    steps = list(trace["steps"])
    request_step = len(steps) - 1 if dict(trace.get("boundary") or {}).get("kind") == mt.EXIT_DEFINITIVE_HAEMOSTASIS else None
    for index, (block, step) in enumerate(zip([block for block in blocks if not block.get("boundary")], steps)):
        # P3-523: every order with what the simulator did with it, in plain words (an unsupported or unrecognized order is said as such, never passed off as management);
        # the orders of the turn that requested definitive control were recorded and NOT carried out (P3-521)
        block["order_words"] = [f"{order_label(row, spans)}: {FATE_WORDS['NOT_EXECUTED_BOUNDARY'] if index == request_step else fate_words(row['fate'])}"
                                for row in step["action"]["orders"]["value"] if row["class"] != "reassessment" and row["order"]]
    # The participant's own words are theirs: only what the application wrote is checked
    text = " ".join(line["text"] + " " + line["label"] for block in blocks for line in block["lines"] if line["provenance"] != mt.RESIDENT_EXPRESSED)
    leaked = [word for word in FORBIDDEN_ON_PARTICIPANT_TRACE if word in text]
    if leaked:
        problems.append("the participant trace would show: " + ", ".join(leaked))
    return {"ok": not problems, "problems": problems, "trace": trace, "blocks": blocks, "turns": turns, "trace_digest": digest_of(trace)}


def bounded_trace(result: Mapping, exit_kind: str | None, exit_minute: int | None) -> dict:
    """The participant's trace with the pilot's own exit as its boundary when the trace itself did not reach one (a faculty stop, the participant's end, a record problem)."""
    if not result.get("ok") or not exit_kind:
        return dict(result)
    trace = result["trace"]
    if dict(trace.get("boundary") or {}).get("reached"):
        return dict(result)
    out = dict(result)
    blocks = list(result["blocks"]) + [{"n": None, "minutes": f"Minute {exit_minute}", "orders": [], "boundary": True,
                                        "lines": [{"label": "Development boundary", "text": EXIT_MESSAGES.get(exit_kind, mt.AUTHORITY_STOP_MESSAGE), "provenance": mt.FACULTY_DEFINED}]}]
    out["blocks"] = blocks
    return out


# -- P3-524 / P3-525: replay review --------------------------------------------------------------------------------------------------------

def replay_review(store: PilotStore, eid: str, layer: Layer) -> dict:
    """What a faculty member checks before trusting an encounter: both logs chain, the artifact verifies and reproduces from itself, and the trace re-extracts from the
    logged turns to the closing trace. Each check says MATCH, MISMATCH or MISSING; anything but MATCH makes the encounter unusable for analysis."""
    out = {"encounter_id": eid, "checks": {}}
    logs = store.logs(eid)
    out["checks"]["logs_chain"] = "MATCH" if not logs["problems"] else "MISMATCH"
    artifact = store.artifact(eid)
    if artifact is None:
        out["checks"]["artifact_verifies"] = out["checks"]["artifact_reproduces"] = "MISSING"
    else:
        try:
            verified = layer.verify_artifact(artifact)
            out["checks"]["artifact_verifies"] = "MATCH" if verified.get("digest_matches") and verified.get("grant_is_the_registered_one") else "MISMATCH"
        except Exception:
            out["checks"]["artifact_verifies"] = "MISMATCH"
        try:
            replay = layer.replay_site_artifact(artifact)
            out["checks"]["artifact_reproduces"] = "MATCH" if replay.get("reproduces") else "MISMATCH"
        except Exception:
            out["checks"]["artifact_reproduces"] = "MISMATCH"
    closing = store.closing_trace(eid)
    events = [entry["payload"]["event"] for entry in logs["participant"] if entry["kind"] == "turn" and "event" in entry["payload"]]
    try:
        meta = store.meta(eid)
    except PilotRecordError:
        meta = {}
    if closing is None:
        out["checks"]["trace_reextracts"] = "MISSING"
    elif artifact is None:
        out["checks"]["trace_reextracts"] = "MISMATCH"
    else:
        again = participant_trace(events, artifact, meta.get("arrival") or {})
        out["checks"]["trace_reextracts"] = "MATCH" if again.get("ok") and again.get("trace_digest") == closing.get("trace_digest") else "MISMATCH"
    out["usable"] = all(value == "MATCH" for value in out["checks"].values())
    return out


# -- P3-526: fail safe ----------------------------------------------------------------------------------------------------------------------

FAIL_SAFE = (
    ("authority mismatch or halt", "the encounter stops (AUTHORITY_STOP); no fallback to the earlier model; the record keeps everything up to the stop", EXIT_AUTHORITY_STOP),
    ("no authority site for a pilot encounter", "the encounter does not run (AUTHORITY_UNAVAILABLE)", EXIT_AUTHORITY_UNAVAILABLE),
    ("unrecognized or incomplete order BEFORE the first committed minute", "recorded as not understood, or held for the reader's question; nothing is done; the encounter goes on", None),
    ("a turn that does not move the clock AFTER the first committed minute and is not purely structural (an incomplete order the reader must ask about, an order it does not "
     "understand, a target instead of a rate, a question typed as an order)",
     "the development experiment stops permanently (the certified authority rule MINUTE_ALREADY_COMMITTED, P3-28; found again by the pilot dry run, unchanged here); the "
     "encounter ends with the operational message. This is fail closed, and it is the pilot's main open readiness problem (TD-165)", EXIT_AUTHORITY_STOP),
    ("an order the engine carries out but the development authority does not represent (e.g. tranexamic acid, analgesia, other medications)",
     "the development experiment stops (AUTHORITY_STOP, the certified fail-closed behaviour, unchanged); the encounter ends with the operational message; nothing is invented", EXIT_AUTHORITY_STOP),
    ("malformed vasopressor order", "the reader asks for an explicit rate with its unit (the approved text); nothing is carried out", None),
    ("request for definitive control of the bleeding", "that turn is recorded and NOT carried out; the encounter ends at the development boundary", EXIT_DEFINITIVE_REQUEST),
    ("engine state shows source control anyway", "the encounter ends at once at the development boundary; what followed is not shown", EXIT_ENGINE_SOURCE_CONTROL),
    ("two-hour development horizon reached", "the encounter ends at the development boundary", EXIT_HORIZON),
    ("pilot record unavailable or its faculty log broken", "the encounter stops; nothing more is carried out (fails closed)", EXIT_RECORD_UNAVAILABLE),
    ("replay mismatch", "the participant's trace is withheld; the faculty sees MISMATCH and the encounter is not usable for analysis", None),
    ("faculty abort", "the encounter ends at the faculty stop on the participant's next action or refresh", EXIT_FACULTY_STOP),
    ("UI refresh, new tab or process restart", "the encounter is never resumed (no account attempt exists); the record shows it INTERRUPTED when the participant starts again", None),
    ("a second encounter started while one is open (another tab of the same participant)", "the open one is recorded INTERRUPTED before the new one starts, and on its own "
     "next run it ends (ENCOUNTER_CLOSED_IN_RECORD): it never continues, so no participant runs two encounters", EXIT_CLOSED_IN_RECORD),
    ("two sessions writing the pilot record at the same moment", "appends are serialized and locked, so the chain never forks; the write check is unique per call", None),
)
