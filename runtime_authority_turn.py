"""P3-269 to P3-272: the authority-controlled TURN -- capture, clone, execute on the clone, judge, then apply or discard (development only).

WHAT THIS CLOSES (R-FAILOPEN-1). Until this module a turn of the experimental encounter ran on the REAL encounter first and the common authority judged it afterwards: the turn that caused an
authority failure had already moved the real clock, the patient, the order ledger, the events and the Management Trace, and the effective stop (P3-250 to P3-264) began only from the NEXT
operation. An authority-controlled encounter now never mutates the real encounter for a turn that is then rejected.

THE PATTERN (the one the legacy engine already uses for its own atomic bundle: ``execute_family_bundle`` and ``advance_clinical_time`` execute on ``deepcopy(state)`` and apply at the end):

    CAPTURE the objects that make up the encounter  ->  CLONE them into working copies  ->  EXECUTE THE UNCHANGED PAGE TURN on the copies  ->  the common authority JUDGES the copy
      ->  VALID:   the validated copy IS the real encounter (nothing is executed a second time: simulating once and re-running could diverge)
      ->  INVALID: the copy is dropped and the ORIGINAL objects, which nothing ever touched, remain the real encounter.

It is not a rollback: the originals are never mutated, so "discard" restores no value, it only stops using the copy. It is not a second engine: the legacy engine runs exactly as before, on
the copy. It decides nothing clinical: the verdict is read from the authority site's own facts (did it halt during the turn, did it make a durable commit).

WHICH TURNS. Only a turn that begins while a REAL development-authority site (a grant) is open, not halted and has ALREADY made a durable commit (the session is ACTIVE_AUTHORITY): a failure of
that turn is INVALID_FOR_CONTINUATION and must not happen to the real encounter. Before the first commit a failure is a clean abort (PRECOMMIT_ABORT): nothing authoritative was ever shown, the
untouched legacy encounter may continue and the legacy turn that ran stays (FD-STOP-04). With every authority flag off the page asks one dictionary question and nothing else changes.

WHAT IS COPIED AND WHAT IS NOT (the ownership table below is partitioned against ``curriculum_runtime.SESSION_FIELDS`` by a test, so a new session field forces a decision):

* TURN_OWNED fields are copied: the patient state (with its clock), the events, the history, the Management Trace, the order ledger, the pending holds, the parse and counters.
* OPERATIONAL: the submission journal is the write-ahead log of what the resident typed; it is not copied (the guard's own protocol marks the entry blocked) and it is not clinical.
* EXTERNAL_ACCOUNTING: the AI call ledger and spend record paid calls that DID happen; restoring them would hide a real cost. They are never copied and never restored.
* AUTHORITY_RECORD: the authority-session record is written by the authority; the rejection must stay.
* CLOSED_OR_REVIEW: untouched by a turn (a turn cannot run once the encounter ended).

SIDE EFFECTS THAT CANNOT BE COPIED. The authority's own record of a rejected turn (its artifact, which names the failed minute and preserves the legacy counterfactual) is evidence of what was refused;
it is written by the site, not by the turn, and it stays. The shadow session observed the attempted turn in memory (not persisted, never shown); it is kept as that evidence. The turn that is
JUDGED -- every turn that moves the clock or places an order -- writes nothing durable of the encounter before the verdict: its one save is its last statement, which a discarded turn never reaches.
A turn that is not judged (a held-order or reasoning-hold step that saves inside the scope) moves neither the clock nor the authority's domain, so nothing is left to judge; and a turn that moves the
clock and that the site was never shown is NOT applied: it is discarded and the session stops (``TURN_NOT_JUDGED``).

Nothing in this module imports the page, the engine or the common core.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

import runtime_authority as ra

VERSION = "P3-271"
#: Where the open turn is kept in the page's session store (a non-field key: never saved, never compared).
TURN_KEY = "phase3_authority_turn"

COMMIT = "COMMIT"
DISCARD = "DISCARD"

# -- the ownership table (P3-269A) -----------------------------------------------------------------------------------------------------------------------------
TURN_OWNED = ("state", "events", "history", "management_trace", "last_parse", "rng_counter", "pending_action", "pending_bundle", "pending_reasoning", "reasoning_gate_counter",
              "last_executed_action", "order_ledger")
OPERATIONAL = ("submission_log",)
EXTERNAL_ACCOUNTING = ("ai_calls_spent", "ai_call_ledger")
AUTHORITY_RECORD = ("phase3_authority_session",)
CLOSED_OR_REVIEW = ("started", "selected_case", "encounter_ended", "encounter_closed_trace", "encounter_closed_state", "encounter_closed_events", "encounter_closed_time_min", "review_prompts",
                    "decision_review", "adaptation_plan", "adaptation_plan_user_edited", "review_completed", "review_stage", "active_review_index", "active_comparison_index",
                    "review_autosave_revision", "expert_comparison_unlocked", "precomparison_decision_review", "expert_comparison_responses", "attempt_number", "carry_forward_plan",
                    "prior_attempt_summary", "prior_attempt_record", "encounter_assignment", "encounter_close", "encounter_language", "close_pending")
OWNERSHIP = {"TURN_OWNED": TURN_OWNED, "OPERATIONAL": OPERATIONAL, "EXTERNAL_ACCOUNTING": EXTERNAL_ACCOUNTING, "AUTHORITY_RECORD": AUTHORITY_RECORD, "CLOSED_OR_REVIEW": CLOSED_OR_REVIEW}
#: Keys the layer and the page write that are not part of the encounter's record at all (the authority's own objects and the widget plumbing). A turn may change them; none is copied.
NOT_ENCOUNTER_STATE_PREFIXES = ("phase3_", "learner_send_", "learner_text_", "FormSubmitter:", "_submission_nonce", "_processing_submission", "_encounter_fragment_rerun", "_attempt_id")


def _clock(state: Any) -> int | None:
    """The clinical clock of a patient state (None when it cannot be read: the comparison then reads as a move, which fails closed)."""
    try:
        return ra._as_int(dict(state).get("sim_time"))
    except Exception:
        return None


class AuthorityTurnDiscarded(Exception):
    """Raised at the point where the turn is judged invalid: it unwinds the page's own turn so that no later statement (the trace, the final save) runs on a copy that is about to be dropped.
    The context manager of the turn swallows it after dropping the copy; it is never shown to a resident."""


class AuthorityTurn:
    """One transactional turn. Use as a context manager through ``begin``; the page never builds it."""

    def __init__(self, store: Any, site: Any, route: str = "") -> None:
        self.store = store
        self.site = site
        self.route = route
        self.halted_before = bool(site.halted)
        self.committed_before = len(site.minutes_committed)
        self.records_before = len(site.records)
        self.judged_before = len(site.records) + len(getattr(site, "no_advance_turns", ()) or ())
        self.clock_before = _clock(store.get("state"))
        self.originals = {key: store[key] for key in TURN_OWNED if key in store}
        self.absent = tuple(key for key in TURN_OWNED if key not in store)
        self.decided: str | None = None

    # -- the clone ---------------------------------------------------------------------------------------------------------------------------------------------
    def __enter__(self) -> "AuthorityTurn":
        for key, value in self.originals.items():
            self.store[key] = deepcopy(value)
        self.store[TURN_KEY] = self
        return self

    # -- the verdict -------------------------------------------------------------------------------------------------------------------------------------------
    def verdict(self, *, halt: bool = False) -> str:
        """COMMIT when the site held the turn valid (or made a durable commit before anything went wrong), DISCARD otherwise. Read from the site's own facts; fail closed.

        ``halt``: when the verdict is DISCARD because the turn moved the clock and the site never judged it (nothing recorded, nothing committed), also stop the session. The page's own call right
        after the authority judged the turn asks for it; an exit through an exception only discards (the interrupted turn changes nothing and the session is not stopped for it)."""
        try:
            site = self.store.get(ra.SITE_KEY)
            if site is None or site is not self.site:
                return DISCARD                                       # the site that began this turn is gone: a turn nobody judged is never applied
            if len(site.minutes_committed) > self.committed_before:
                return COMMIT                                        # a DURABLE commit: the encounter reached that minute, so the turn is real (a later halt stops the NEXT operation)
            if site.halted and not self.halted_before:
                return DISCARD
            if len(site.minutes_committed) < self.committed_before:
                return DISCARD                                       # a commit was withdrawn: never apply
            if len(site.records) + len(getattr(site, "no_advance_turns", ()) or ()) == self.judged_before and _clock(self.store.get("state")) != self.clock_before:
                # P3-276 (review H1): the working copy's clock moved and the site recorded NOTHING for the turn -- no minute, no quiet turn, no refusal. Whatever moved the patient was never
                # shown to the authority (a route it is not fed by, a hook that was off), so nothing authoritative covers it: it is not applied.
                if halt:
                    site.halt_unjudged_turn(_clock(self.store.get("state")), f"the {self.route or 'turn'} moved the clock from {self.clock_before} to {_clock(self.store.get('state'))} and the authority never judged it")
                return DISCARD
            return COMMIT
        except Exception:
            return DISCARD

    def check(self) -> None:
        """The page calls this right after the authority judged the turn: a DISCARD verdict unwinds the turn here."""
        if self.verdict(halt=True) == DISCARD:
            raise AuthorityTurnDiscarded(self.route or "turn")

    # -- the end -----------------------------------------------------------------------------------------------------------------------------------------------
    def _apply(self, decision: str) -> None:
        self.decided = decision
        if decision == DISCARD:
            for key, value in self.originals.items():
                self.store[key] = value                              # the objects nothing ever touched
            for key in self.absent:
                try:
                    del self.store[key]
                except Exception:
                    pass
        try:
            del self.store[TURN_KEY]
        except Exception:
            pass

    def __exit__(self, exc_type, exc, tb) -> bool:
        # Every exit applies the verdict: a turn that was stopped part way (a rerun, an error) after the authority halted is discarded too, and the original exception keeps going.
        decision = DISCARD if exc_type is AuthorityTurnDiscarded else self.verdict(halt=exc_type is None)
        self._apply(decision)
        return exc_type is AuthorityTurnDiscarded


class _NoTurn:
    """The turn of an encounter that is not under a real, committed authority session: the page runs exactly as before. A single shared object: it costs nothing."""

    decided = None

    def __enter__(self) -> "_NoTurn":
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False

    def verdict(self) -> str:
        return COMMIT

    def check(self) -> None:
        return None


NO_TURN = _NoTurn()


def begin(store: Any, *, route: str = "") -> Any:
    """The turn this page run should execute under: a transactional ``AuthorityTurn`` when a real authority session has already committed and can continue, else ``NO_TURN``.

    One dictionary lookup when no site exists (every flag off, the first pilot and any legacy encounter). Never raises: any doubt is the ordinary (untransacted) turn, because the guard and the
    stop already refuse a stopped session, and an exception here must never break an encounter."""
    try:
        site = store.get(ra.SITE_KEY)
        if site is None or not getattr(site, "grant", None) or getattr(site, "halted", True) or not site.minutes_committed:
            return NO_TURN
        if store.get(TURN_KEY) is not None:
            return NO_TURN                                           # a turn inside a turn is the outer turn's
        return AuthorityTurn(store, site, route)
    except Exception:
        return NO_TURN


def applies(store: Any) -> bool:
    """Whether ``begin`` would return a transactional turn right now (a real authority session has committed and can continue). The page asks it where it must DEFER a mutation into the turn
    instead of making it at render time (the consumption of a held order by the guided form), so that the mutation is covered by the transaction. One dictionary lookup when no site exists."""
    return isinstance(begin(store), AuthorityTurn)


def check(store: Any) -> None:
    """After the authority judged a turn: unwind it when the verdict is DISCARD. One lookup when no turn is open."""
    turn = store.get(TURN_KEY)
    if turn is not None:
        turn.check()


def reset_stale(store: Any) -> str | None:
    """P3-276 (review L2): a turn left open by an earlier page run (killed before its context could close) is closed at the START of the next run, with its own verdict, so a stale turn never
    makes every later turn read as 'a turn inside a turn' and run untransacted. Returns the decision taken, or None when no turn was open. One lookup when none is. Never raises."""
    try:
        turn = store.get(TURN_KEY)
    except Exception:
        return None
    if turn is None:
        return None
    try:
        decision = turn.verdict() if isinstance(turn, AuthorityTurn) else DISCARD
        turn._apply(decision)
        return decision
    except Exception:
        try:
            del store[TURN_KEY]
        except Exception:
            pass
        return DISCARD


def ownership_problems(session_fields: Any) -> list:
    """What is wrong with the ownership table against the session's saved fields: a field nobody classified, or classified twice. Empty means partitioned."""
    problems = []
    seen: dict = {}
    for name, fields in OWNERSHIP.items():
        for field in fields:
            if field in seen:
                problems.append(f"{field} is in both {seen[field]} and {name}")
            seen[field] = name
    for field in session_fields:
        if field not in seen:
            problems.append(f"{field} is a saved session field that no turn ownership class covers")
    for field in seen:
        if field not in set(session_fields):
            problems.append(f"{field} is classified but is not a saved session field")
    return problems
