"""P3-211: the explicit VIEW of the patient's mental status -- legacy, or (later, by decision) the common core's.

Why this module exists. The legacy engine writes ``observable["mental_status"]`` and thirty-odd readers consume it: the engine's own
order eligibility and discharge outcome, the page's available actions and update cards, the persistence of every trace event, and (through
that trace) the AI and faculty analyses and the retention of an AI suggestion on the faculty's evaluation surface. A consciousness
authority that wrote the common core's word into that one field would reach all of them at once. The P3-208 review showed this is not
display only.

The rule this module enforces, with nothing global and nothing mutated:

* the common core's consciousness is carried by an explicit, owned OVERLAY (``OVERLAY_KEY``), never by the live field;
* every reader asks for the word FOR ITSELF (``mental_status_for(state, reader_id)``) and the answer is the legacy word unless the
  reader has been explicitly allowed to see the common one (``COMMON_VIEW_READERS``, EMPTY today);
* an overlay that tries to give a frozen reader the common view is refused, and says so (``view_problems``); its other fields are still
  trusted for the PRESERVED legacy word (``structure_problems``), so a refused assignment can never strand a reader on a common word;
* a transaction may map the common word INTO the live field only while no consequential reader is left unrouted
  (``mapping_problems``, checked by the writer), and then it must preserve the legacy word, which every reader goes on reading.

Nothing here decides anything clinical, touches scoring, or enables an authority: with no overlay (today, always) every function returns
the live field it was given, byte for byte. The layer that would write an overlay lives elsewhere and is dormant.
"""
from __future__ import annotations

from types import MappingProxyType
from typing import Any, Mapping

LEGACY_VIEW = "LEGACY_VIEW"
DEVELOPMENT_COMMON_AUTHORITY_VIEW = "DEVELOPMENT_COMMON_AUTHORITY_VIEW"
VIEWS = (LEGACY_VIEW, DEVELOPMENT_COMMON_AUTHORITY_VIEW)

FIELD = "mental_status"
#: The one key under which a development authority transaction may carry the common core's consciousness. Top level of the state, never
#: inside ``observable``: no reader that iterates the observable can pick it up by accident.
OVERLAY_KEY = "development_authority_view"
OVERLAY_FIELDS = ("owner", "minute", "views", "common", "legacy", "mapped_into_live_field")
COMMON_FIELDS = ("consciousness_category", "mental_status", "pulse_present")
#: The legacy engine's ladder of words, in category order (0 alert .. 3 unresponsive). The common word is accepted only if it is one of them.
WORDS = ("Alert", "Drowsy", "Obtunded", "Unresponsive")

# -- the guard types of P3-210B ---------------------------------------------------------------------------------------------------------
ISOLATE = "ISOLATE_FROM_EXPERIMENTAL_AUTHORITY"
FREEZE = "FREEZE_TO_LEGACY_DURING_DEVELOPMENT_AUTHORITY"
DIAGNOSTIC = "READ_COMMON_ONLY_IN_NONAUTHORITATIVE_DIAGNOSTIC_PATH"
LATER = "EXPLICITLY_AUTHORIZE_LATER"
NONE_NEEDED = "NONE_NEEDED_DISPLAY_OR_DEAD_CODE"
GUARD_TYPES = (ISOLATE, FREEZE, DIAGNOSTIC, LATER, NONE_NEEDED)

#: The readers the page routes through ``mental_status_for``: their id is ``module::function``. Each is FROZEN: it reads the legacy word
#: even if a transaction's overlay asks otherwise. They are the readers whose answer changes something other than a sentence.
ROUTED_READERS = MappingProxyType({
    "app.py::_clinical_encounter_workspace": FREEZE,        # action availability: history is unavailable from a patient who cannot speak
    "app.py::observable_state_changed": FREEZE,             # scenario flow: whether a turn adds an update card
    "app.py::learner_vitals_snapshot": FREEZE,              # persistence: each update event freezes the state, and the trace is built from them
    "app.py::management_state_snapshot": FREEZE,            # persistence: the trace every AI and faculty analysis and retention rule reads
    "trace_phase0.py::observation_snapshot": FREEZE,        # persistence: what the resident saw, stored in every Management-Trace event (P3-219 review, F4)
})
#: Readers that MAY be given the common view by an explicit later decision. EMPTY: no reader sees the common word today.
COMMON_VIEW_READERS: frozenset = frozenset()
#: Developer-facing readers of the common word that are NOT authority: they never feed an encounter, a score or a resident.
DIAGNOSTIC_READERS: frozenset = frozenset()


def _is_mapping(value: Any) -> bool:
    return isinstance(value, Mapping)


def live_word(state: Any, default: Any = None) -> Any:
    """The word in the live field, exactly as the engine wrote it."""
    observable = state.get("observable") if _is_mapping(state) else None
    return observable.get(FIELD, default) if _is_mapping(observable) else default


def view_problems(overlay: Any) -> list:
    """Every view assignment of the overlay that is not allowed (an empty list: all are). A refused assignment gives NO reader the common word."""
    views = overlay.get("views") if _is_mapping(overlay) else None
    if not _is_mapping(views) or any(view not in VIEWS for view in views.values()):
        return ["unknown_view"]
    return [f"common_view_for_a_reader_not_allowed:{reader}" for reader, view in views.items()
            if view == DEVELOPMENT_COMMON_AUTHORITY_VIEW and (reader not in COMMON_VIEW_READERS or reader in ROUTED_READERS)]


def structure_problems(overlay: Any) -> list:
    """Every reason an overlay is not a well-formed carrier of the common word and of the PRESERVED legacy word. Never raises. The reading side
    trusts an overlay for the legacy word whenever this list is empty, whatever its view assignments say."""
    if not _is_mapping(overlay):
        return ["not_a_mapping"]
    problems = [f"missing:{name}" for name in OVERLAY_FIELDS if name not in overlay]
    if problems:
        return problems
    if not isinstance(overlay["owner"], str) or not overlay["owner"]:
        problems.append("no_owner")
    if isinstance(overlay["minute"], bool) or not isinstance(overlay["minute"], int):
        problems.append("minute_not_an_integer")
    common = overlay["common"]
    if not _is_mapping(common) or set(common) != set(COMMON_FIELDS):
        problems.append("common_fields")
    elif (common["mental_status"] not in WORDS or type(common["consciousness_category"]) is not int
          or common["consciousness_category"] not in range(len(WORDS))
          or WORDS[common["consciousness_category"]] != common["mental_status"]
          or not isinstance(common["pulse_present"], bool)):
        problems.append("common_word_is_not_the_category")
    if overlay["mapped_into_live_field"] is not False:
        if overlay["mapped_into_live_field"] is not True:
            problems.append("mapped_flag_not_boolean")
        elif not _is_mapping(overlay["legacy"]) or overlay["legacy"].get(FIELD) not in WORDS:
            problems.append("legacy_word_not_preserved")
    return problems


def overlay_problems(overlay: Any) -> list:
    """What the WRITER must find empty before it carries an overlay: the structure and every view assignment."""
    return structure_problems(overlay) + (view_problems(overlay) if _is_mapping(overlay) and not structure_problems(overlay) else [])


def mapping_problems(overlay: Any) -> list:
    """The WRITE-side rule: why a transaction may not map the common word into the live field (an empty list: it may). A reader never calls
    this: it must go on preserving the legacy word whatever the writer did. The layer's commit refuses a mapping while it is not empty."""
    if not _is_mapping(overlay) or overlay.get("mapped_into_live_field") is not True:
        return []
    blockers = live_field_mapping_blockers()
    return [f"live_field_mapping_blocked_by:{sorted(blockers)}"] if blockers else []


def overlay_of(state: Any) -> dict | None:
    """The state's overlay when it is well formed AND belongs to the state's own minute; otherwise None (a stale or malformed overlay is
    not a view: the reader gets the live field)."""
    try:
        overlay = state.get(OVERLAY_KEY) if _is_mapping(state) else None
        if overlay is None or structure_problems(overlay):
            return None
        if overlay["minute"] != state.get("sim_time"):
            return None
        return dict(overlay)
    except Exception:                         # a view that cannot even be read is not a view: the reader gets the live field and never raises into a turn
        return None


def legacy_mental_status(state: Any, default: Any = None) -> Any:
    """The LEGACY word, whatever the overlay says: the live field, or the preserved copy when a transaction mapped the common word into it."""
    overlay = overlay_of(state)
    if overlay is not None and overlay["mapped_into_live_field"] is True:
        return overlay["legacy"][FIELD]
    return live_word(state, default)


def mental_status_for(state: Any, reader: str, default: Any = None) -> Any:
    """The word THIS reader sees. Legacy unless the reader is explicitly allowed the common view AND the transaction assigned it."""
    overlay = overlay_of(state)
    if (overlay is not None and reader in COMMON_VIEW_READERS and reader not in ROUTED_READERS and not view_problems(overlay)
            and overlay["views"].get(reader) == DEVELOPMENT_COMMON_AUTHORITY_VIEW):
        return overlay["common"][FIELD]
    return legacy_mental_status(state, default)


def common_consciousness(state: Any) -> dict | None:
    """The common core's consciousness for a NON-AUTHORITATIVE diagnostic reader (None when there is no valid overlay). Nothing in the
    encounter, the scores or the resident's page reads this."""
    overlay = overlay_of(state)
    return None if overlay is None else dict(overlay["common"])


def live_field_mapping_blockers() -> set:
    """The consequential readers that would see a common word written into the live field because they are not routed. Today the set is
    EMPTY only if every consequential reader named by the audit is in ``ROUTED_READERS``: ``UNROUTED_CONSEQUENTIAL`` lists the others."""
    return set(UNROUTED_CONSEQUENTIAL)


#: Consequential readers of the LIVE state (they change something other than a sentence) that are NOT routed, so a mapping into the live
#: field would reach them: the image contract and the visual profile of the patient (an image edit can be a paid call). The page's adaptive
#: prompts and expert comparison read the frozen TRACE, which the routed snapshots keep legacy, so they are not here. While this tuple is not
#: empty no transaction may map the common word into the live field (``mapping_problems``); it empties only by a later decision that routes them.
UNROUTED_CONSEQUENTIAL = (
    "image_broker.py::edit_prompt", "image_consistency.py::photographic_targets", "patient_appearance.py::contract_brief",
    "visual_observations.py::visual_observations",
    # The three readers of the ENGINE (order eligibility and the outcome of a discharge). They CANNOT be routed in this phase: ``family_engine.py`` is one of the
    # sources of the Phase-2 calibration freeze (``calibration.INPUT_PATH_SOURCES``), so an edit to it moves the closure's freeze digests (found by the full suite
    # of this cycle: an earlier draft routed them and broke ``test_phase2_closure``). They are held today by the only thing that can hold them -- no transaction
    # writes the live field, and the writer refuses to -- and they are blockers for any mapping into it.
    "family_engine.py::_validate", "family_engine.py::_order", "family_engine.py::_discharge_alarm",
)
#: The subset of ``UNROUTED_CONSEQUENTIAL`` that is frozen by the Phase-2 closure (the others merely have not been routed yet).
FROZEN_BY_THE_PHASE2_CLOSURE = frozenset({"family_engine.py::_validate", "family_engine.py::_order", "family_engine.py::_discharge_alarm"})
