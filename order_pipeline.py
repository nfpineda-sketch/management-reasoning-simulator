"""One path from what the resident wrote to a fate for every order (Phase 0, workstreams 0A-0B).

Pre-pilot measurement safety, 2026-10-06. Every entry point -- the free-text form, the
answer that completes the reasoning a held order asked for, the answer to a clarification
question, the guided reasoning form -- ends in ``execute_bundle``. Before it, this module
opens the turn (each order gets an id and the text is mapped for coverage); for a bank
case it splits the bundle so that independent orders run and only dependency groups wait;
after it, every order gets its fate. ``app.py`` calls it at those three points and shows
the receipt; nothing here touches the reader or the physiology.

The bundle rule (proposal §9.4, Phase 0 default): independent recognised orders run.
Only these wait together with the order that cannot run yet:

* a procedure and its premedication (induction agent, paralytic, intubation);
* an explicit sequence ("X then Y"): what is written after the sequence word waits for
  what was written before it, never the other way round;
* another order for the same agent (a start and its titration).

A reassessment waits with a treatment that is held for an answer: the resident chose
when to look again in order to see that treatment's effect. It does not wait for an order
that will never run in this simulator (an unrecognised or unmodelled one).

The reasoning gate keeps holding the whole order it holds (methodology, unchanged): each
order in it is ``HELD_REASONING`` until the reasoning is completed.
"""
from __future__ import annotations

import re
from copy import deepcopy

import order_ledger as L

ENTRY_POINTS = ("free_text", "reasoning_followup", "clarification_answer", "guided_form", "pending_completion",
                "recovered_submission")

_AIRWAY_GROUP = frozenset({"procedural_sedation", "neuromuscular_blockade", "intubation", "airway_preparation",
                           "invasive_ventilation"})
_SEQUENCE = re.compile(r"(?<![a-z])(?:then|luego|despues|after\s+that|afterwards|posteriormente|followed\s+by|"
                       r"seguido\s+de|y\s+despues)(?![a-z])")
_NOT_MODELLED_REFUSAL = "requires a generated encounter"
_STUDY_QUESTION = re.compile(r"(?<![a-z])(?:study|studies|estudio|estudios|investigation|examination|examen)(?![a-z])",
                             re.I)
_NRB_FLOW_LPM = 15


# --------------------------------------------------------------------------------------
# Opening a turn
# --------------------------------------------------------------------------------------
def apply_safe_defaults(parsed):
    """Defaults that are standard practice and said in the receipt, never silent.

    A non-rebreather mask is run at 15 L/min: it is the flow its reservoir needs, and the
    reader's own question names it ("non-rebreather mask 15 L/min"). Nothing else is
    defaulted here.
    """
    for index, action in enumerate(parsed.get("actions") or []):
        pending = action.get("pending_action") if isinstance(action, dict) else None
        if (isinstance(pending, dict) and action.get("type") == "clarification"
                and pending.get("type") == "oxygen" and pending.get("flow_lpm") is None
                and "rebreather" in str(pending.get("device") or "").lower()):
            completed = {**deepcopy(pending), "flow_lpm": float(_NRB_FLOW_LPM)}
            completed["_default_applied"] = (f"no flow was written; the standard non-rebreather flow, "
                                             f"{_NRB_FLOW_LPM} L/min, was used")
            for key in ("_order_id", "_submission_id", "_span", "_written_at_min"):
                if action.get(key) is not None:
                    completed[key] = action[key]
            parsed["actions"][index] = completed
    remaining = [a for a in parsed.get("actions") or [] if isinstance(a, dict) and a.get("type") == "clarification"]
    if parsed.get("clarification") and not remaining:
        parsed.pop("clarification", None)
    elif remaining and parsed.get("clarification"):
        parsed["clarification"] = remaining[0].get("message") or parsed["clarification"]
    return parsed


def open_turn(text, parsed, *, submission_id, entry_point, minute, ledger=None, coverage_parse=None):
    """Tag the turn's orders, map the text and account for everything the reader did not return.

    ``ledger`` is the encounter's order ledger (a list); orders already in it -- the ones
    a held bundle carries -- are reused, never duplicated. ``coverage_parse`` is what the
    reader returned for this turn's own text when ``parsed`` also carries a held order
    (the answer to the reasoning gate): the text is checked against what it produced.
    """
    parsed = parsed if isinstance(parsed, dict) else {}
    apply_safe_defaults(parsed)
    L.tag(parsed, submission_id, text, minute)
    if coverage_parse is not None:
        apply_safe_defaults(coverage_parse)
    cov = L.coverage(text, coverage_parse if coverage_parse is not None else parsed)
    known = {order["order_id"]: order for order in (ledger or [])}
    orders = []
    for index, action in enumerate(parsed.get("actions") or []):
        if not isinstance(action, dict):
            continue
        existing = known.get(action.get("_order_id"))
        if existing is not None:
            orders.append(existing)
            continue
        order = L.order_from_action(action, submission_id=submission_id, index=index, text=text, minute=minute)
        if action.get("_default_applied"):
            order["default_applied"] = action["_default_applied"]
        orders.append(order)
    seen_plans = {order.get("span") for order in orders}
    for order in L.plan_orders(parsed, submission_id=submission_id, minute=minute):
        if order["order_id"] in known:
            continue
        if order.get("span") in seen_plans and any(o["order_id"] == order["order_id"] for o in orders):
            continue
        orders.append(order)
    orders.extend(L.unaccounted_orders(cov, submission_id=submission_id, minute=minute))
    for offset, item in enumerate(cov.get("held") or []):
        order = {
            "order_id": f"{submission_id}:h{3000 + offset}", "submission_id": submission_id,
            "span": item["text"], "canonical": "held_with_question", "class": "held_with_question",
            "detected_as": item["cls"], "dose": None, "route": None, "rate": None, "timing": None,
            "written_at_min": minute, "fate": None, "reason": None, "executed_at_min": None, "receipt": None,
            "modelled_effect": None, "history": [],
        }
        L.set_fate(order, "HELD_CLARIFICATION", "held with the reader's question about this order",
                   minute=minute)
        orders.append(order)
    return {
        "submission": {"id": submission_id, "raw_text": str(text or ""), "entry_point": entry_point,
                       "written_at_min": minute},
        "orders": orders,
        "coverage": cov,
    }


def _same_order(a, b):
    """A held order restated in the answer: the same kind and the same agent."""
    if a.get("type") != b.get("type") or a.get("type") in ("reassessment", "clarification"):
        return False
    return (a.get("agent") or a.get("diagnostic") or a.get("service") or a.get("fluid_type")
            or a.get("destination")) == (b.get("agent") or b.get("diagnostic") or b.get("service")
                                         or b.get("fluid_type") or b.get("destination"))


def join_followup(held_actions, supplemental_actions):
    """The orders an answer to the reasoning gate adds to the held order, and the restated ones.

    A reassessment is handled by the caller (it replaces the held one). An order that
    restates a held one ("give the pantoprazole because...") is not given twice: it is
    recorded as a restatement. Everything else -- new orders, and what the reader could
    not read in the answer -- joins the held order, so that it gets a fate.
    """
    joining, restated = [], []
    for action in supplemental_actions or []:
        if not isinstance(action, dict) or action.get("type") == "reassessment":
            continue
        if any(_same_order(action, held) for held in held_actions if isinstance(held, dict)):
            restated.append(action)
            continue
        joining.append(action)
    return joining, restated


# --------------------------------------------------------------------------------------
# The bundle rule (bank cases)
# --------------------------------------------------------------------------------------
def _position(text, action):
    span = L.fold(action.get("_span") or "")
    folded = L.fold(text)
    if span:
        found = folded.find(span)
        if found >= 0:
            return found
    return None


def split_bundle(state, parsed, *, text="", weight_waiting=()):
    """Which actions run now and which wait, with each one's reason.

    Returns ``{"run": [...], "held": [(action, reason, kind)], "refused": [(action, reason)],
    "unreadable": [(action, reason)], "question": str|None}`` where ``kind`` is
    ``"question"`` (the reader or engine asks something) or ``"dependency"``.
    """
    from family_engine import _validate
    actions = [a for a in parsed.get("actions") or [] if isinstance(a, dict)]
    base = {key: value for key, value in parsed.items() if key not in ("clarification", "actions")}
    accepted, held, refused, unreadable = [], [], [], []
    question = None
    waiting = set(weight_waiting or ())
    for index, action in enumerate(actions):
        if index in waiting:
            held.append((action, "waiting for the patient's weight", "question"))
            continue
        if action.get("type") == "clarification":
            if action.get("unrecognized_text"):
                unreadable.append((action, str(action.get("message") or "not recognized")))
            else:
                held.append((action, str(action.get("message") or "the order needs a clarification"), "question"))
                question = question or action.get("message")
            continue
        trial = accepted + [action]
        _, error = _validate(state, {**base, "actions": [L.strip_tags(a) for a in trial]})
        if not error:
            accepted.append(action)
            continue
        if _NOT_MODELLED_REFUSAL in str(error):
            refused.append((action, str(error)))
            continue
        held.append((action, str(error), "question"))
        question = question or str(error)
    # Dependency groups.
    failed = [a for a, *_ in held] + [a for a, _ in unreadable] + [a for a, _ in refused]
    # A reassessment waits for a held treatment, not for a held study or a question about one.
    pending_question = [a for a, reason, kind in held if kind == "question"
                        and a.get("type") not in ("reassessment", "diagnostic", "examination")
                        and not _STUDY_QUESTION.search(str(a.get("message") or reason or ""))]
    dependent = []
    folded = L.fold(text)
    sequence_marks = [m.start() for m in _SEQUENCE.finditer(folded)]
    for action in list(accepted):
        reason = None
        kind = action.get("type")
        if kind in _AIRWAY_GROUP and any(f.get("type") in _AIRWAY_GROUP for f in failed):
            reason = "waits with the airway procedure it belongs to"
        elif any(f.get("type") == kind and kind != "clarification"
                 and (f.get("agent") or None) == (action.get("agent") or None) for f in failed):
            reason = "waits with the other order for the same agent"
        elif sequence_marks and failed:
            mine = _position(text, action)
            for other in failed:
                theirs = _position(text, other)
                if mine is None or theirs is None:
                    continue
                if theirs < mine and any(theirs < mark < mine for mark in sequence_marks) \
                        and folded.rfind(".", theirs, mine) < 0:
                    reason = "written after an order that has not run (\"then\")"
                    break
        if reason is None and kind == "reassessment" and pending_question:
            reason = "the reassessment waits for the held treatment it is meant to judge"
        if reason:
            dependent.append((action, reason))
    for action, reason in dependent:
        accepted.remove(action)
        held.append((action, reason, "dependency"))
    return {"run": accepted, "held": held, "refused": refused, "unreadable": unreadable, "question": question}


def held_message(split, labels_of):
    """The resident-facing words for a partly held order: what ran, what waits, and why."""
    ran = labels_of({"actions": split["run"]})
    waiting = labels_of({"actions": [a for a, *_ in split["held"] if a.get("type") != "clarification"]})
    lines = []
    if ran:
        lines.append("**PART OF THIS ORDER IS HELD — CLARIFICATION REQUIRED**")
        lines.append("")
        lines.append("Executed now: **" + " + ".join(ran) + "**.")
        if waiting:
            lines.append("Held until you answer: **" + " + ".join(waiting) + "**. Nothing of it has been given.")
        else:
            lines.append("The item below is held until you answer. Nothing of it has been given.")
    else:
        lines.append("**ORDER HELD — CLARIFICATION REQUIRED**")
        lines.append("")
        if waiting:
            lines.append("I understood: **" + " + ".join(waiting) + "**.")
        lines.append("Nothing in this order was executed and the patient state has not changed.")
    if split.get("question"):
        lines.append("")
        lines.append(str(split["question"]))
    return "\n".join(lines)


# --------------------------------------------------------------------------------------
# Settling fates after the engine ran
# --------------------------------------------------------------------------------------
def _order_by_action(turn, action):
    wanted = action.get("_order_id")
    return next((order for order in turn["orders"] if order["order_id"] == wanted), None)


def _summary_for(action, summaries, used):
    kind = action.get("type")
    for position, summary in enumerate(summaries):
        if position in used or not isinstance(summary, dict):
            continue
        if summary.get("type") == kind or (kind == "diagnostic" and (
                summary.get("diagnostic_type") == action.get("diagnostic")
                or summary.get("type") == "study_not_performed")):
            used.add(position)
            return summary
    return None


def settle(turn, *, result, run_actions, split=None, minute_before, minute_after, terminal=False,
           held_for_reasoning=False):
    """Give every order of the turn its fate, from what the engine actually did."""
    split = split or {"held": [], "refused": [], "unreadable": []}
    summaries = list((result or {}).get("action_summaries") or [])
    used = set()
    executed = bool((result or {}).get("executed"))
    for action in run_actions:
        order = _order_by_action(turn, action)
        if order is None:
            continue
        if held_for_reasoning:
            L.set_fate(order, "HELD_REASONING", "held until the reasoning the gate asks for is given",
                       minute=minute_before)
            continue
        if terminal:
            L.set_fate(order, "TERMINAL_NOT_EXECUTABLE",
                       "written after a cardiac arrest; resuscitation is not modelled in this pilot",
                       minute=minute_before,
                       receipt=f'Not executed: "{order.get("span") or order.get("canonical")}". The patient is in '
                               "cardiac arrest; resuscitation management is not modelled in this pilot.")
            continue
        if not executed:
            continue
        summary = _summary_for(action, summaries, used) if action.get("type") != "reassessment" else None
        if action.get("after_result"):
            L.set_fate(order, "SCHEDULED", f"waits for the result: {action['after_result']}", minute=minute_before)
            continue
        if summary is not None and summary.get("type") == "study_not_performed":
            L.set_fate(order, "RECORDED_NOT_MODELLED", str(summary.get("label") or "study not modelled here"),
                       minute=minute_before, modelled_effect=False)
            order["receipt_shown_elsewhere"] = True
            continue
        label = str((summary or {}).get("label") or "")
        if summary is not None and (summary.get("repeated") or label.endswith("not repeated")) \
                and action.get("operation") != "continue":
            L.set_fate(order, "DUPLICATE_IGNORED", label or "already done; not repeated", minute=minute_before,
                       modelled_effect=False)
            order["receipt_shown_elsewhere"] = True
            continue
        L.set_fate(order, "EXECUTED", label or "executed", minute=minute_before)
        if order.get("default_applied"):
            order["receipt"] = f"{order.get('canonical')}: {order['default_applied']}."
        if action.get("type") == "reassessment":
            order["executed_at_min"] = minute_before
            order["timing"] = {**(order.get("timing") or {}), "observed_at_min": minute_after}
    for action, reason, kind in split.get("held", []):
        order = _order_by_action(turn, action)
        if order is None:
            continue
        if held_for_reasoning:
            L.set_fate(order, "HELD_REASONING", "held until the reasoning the gate asks for is given",
                       minute=minute_before)
        elif split.get("no_pending"):
            # No answer can complete it (a lone question about a study the reader does not know,
            # an examination this case does not have): nothing waits, so the fate is final, and
            # the reader's or engine's own words, already shown, are its reason.
            if action.get("type") == "clarification":
                L.set_fate(order, "UNRECOGNIZED", reason, minute=minute_before, modelled_effect=False)
            else:
                L.set_fate(order, "RECORDED_NOT_MODELLED", reason, minute=minute_before, modelled_effect=False)
            order["receipt_shown_elsewhere"] = True
        else:
            L.set_fate(order, "HELD_CLARIFICATION", reason, minute=minute_before)
            order["receipt_shown_elsewhere"] = True
    for action, reason in split.get("unreadable", []):
        order = _order_by_action(turn, action)
        if order is None:
            continue
        L.set_fate(order, "UNRECOGNIZED", "not read by the simulator's reader; nothing was given",
                   minute=minute_before, modelled_effect=False,
                   receipt=L.unrecognized_receipt(order.get("span") or action.get("unrecognized_text") or ""))
    for action, reason in split.get("refused", []):
        order = _order_by_action(turn, action)
        if order is None:
            continue
        L.set_fate(order, "RECORDED_NOT_MODELLED",
                   "recognised; no response to it is modelled for this case in this simulator", minute=minute_before,
                   modelled_effect=False,
                   receipt=f'Recorded as your decision, not given: "{order.get("span") or order.get("canonical")}". '
                           "This simulator does not model a response to it in this case, so nothing changed.")
    if split.get("no_pending"):
        for order in turn["orders"]:
            if order.get("class") == "held_with_question" and order.get("fate") in L.HELD:
                L.set_fate(order, "UNRECOGNIZED", "the reader asked about the order; no answer can complete it",
                           minute=minute_before, modelled_effect=False,
                           receipt=L.unrecognized_receipt(order.get("span") or ""))
    for order in turn["orders"]:
        if order.get("fate") is None:
            # An order the engine never saw in this turn: a held bundle's question that
            # answered nothing, or an entry point that stopped before execution.
            L.set_fate(order, "HELD_CLARIFICATION" if not held_for_reasoning else "HELD_REASONING",
                       "not executed in this turn", minute=minute_before)
    return turn


def cancel(orders, *, reason, minute, superseded=False):
    """Held orders the resident cancelled, or discarded when a new order replaced them."""
    for order in orders:
        if order.get("fate") in L.HELD:
            L.set_fate(order, "CANCELLED", reason, minute=minute,
                       receipt=None if not superseded else None)
    return orders


def finish_held(orders, *, minute):
    """Orders held with a question and never written as actions end unrecognised once the
    question is answered: the answer runs the bundle, and they were never part of it."""
    for order in orders:
        if order.get("class") == "held_with_question" and order.get("fate") in L.HELD:
            L.set_fate(order, "UNRECOGNIZED", "the reader asked about the order and did not read this part of it",
                       minute=minute, modelled_effect=False, receipt=L.unrecognized_receipt(order.get("span") or ""))
    return orders


def restated_orders(actions, *, submission_id, minute, text=""):
    """Held orders restated in the answer to the reasoning gate: recorded, never given twice."""
    out = []
    for offset, action in enumerate(actions or []):
        order = L.order_from_action(action, submission_id=submission_id, index=4000 + offset, text=text,
                                    minute=minute)
        order["order_id"] = f"{submission_id}:r{4000 + offset}"
        L.set_fate(order, "DUPLICATE_IGNORED", "the held order restated in the answer; it runs once, as held",
                   minute=minute, modelled_effect=False,
                   receipt=f'"{order.get("span") or order.get("canonical")}" in your answer was taken as the held '
                           "order restated: it runs once, as it was held.")
        out.append(order)
    return out


def upsert(ledger, orders):
    """The encounter's ledger keeps the latest state of every order, in writing order."""
    index = {order["order_id"]: position for position, order in enumerate(ledger)}
    for order in orders:
        snapshot = L.snapshot([order])[0]
        if order["order_id"] in index:
            ledger[index[order["order_id"]]] = snapshot
        else:
            index[order["order_id"]] = len(ledger)
            ledger.append(snapshot)
    return ledger


def receipt_lines(turn):
    return L.receipt_lines(turn["orders"])


def check(turn):
    """The invariant: every order has a fate and every actionable text an order."""
    return L.validate(turn["orders"], turn.get("coverage"))


# --------------------------------------------------------------------------------------
# The encounter's ledger in the session (called by the page; module functions, so that the
# tests that load single page functions keep working)
# --------------------------------------------------------------------------------------
def _minute(session):
    return int(((session.get("state") or {}).get("sim_time")) or 0)


def ledger_record(session, turn, add_event):
    """Keep the turn's orders in the encounter's ledger and say every one that did not run."""
    problems = check(turn)
    if problems:
        # The invariant failed: an order without a fate or an actionable text unaccounted.
        # It is recorded, and the resident is told, never passed over in silence.
        turn.setdefault("limitations", []).append({"type": "engine_inconsistency", "detail": problems})
        add_event("prototype", "Part of this order could not be matched to what the simulator did: "
                  + "; ".join(problems) + ". Check the patient state before relying on it.")
    for line in receipt_lines(turn):
        add_event("prototype", line)
    upsert(session.setdefault("order_ledger", []), turn["orders"])
    return turn


def ledger_hold_reasoning(session, held_parsed, text, submission_id, add_event):
    """An answer that did not complete the reasoning: what it added waits with the held order."""
    minute = _minute(session)
    ledger = session.setdefault("order_ledger", [])
    turn = open_turn(text, held_parsed, coverage_parse=held_parsed.pop("_coverage_parse", None),
                     submission_id=submission_id, entry_point="reasoning_followup", minute=minute, ledger=ledger)
    held_parsed.pop("_coverage_text", None)
    turn["orders"].extend(restated_orders(held_parsed.pop("_followup_restated", None),
                                          submission_id=submission_id, minute=minute, text=text))
    settle(turn, result={"executed": False}, run_actions=list(held_parsed.get("actions") or []),
           minute_before=minute, minute_after=minute, held_for_reasoning=True)
    pending = session.get("pending_reasoning")
    if isinstance(pending, dict) and isinstance(pending.get("parsed"), dict):
        # The held order keeps its ids, so that its fate follows it.
        pending["parsed"]["actions"] = deepcopy(held_parsed.get("actions") or [])
    return ledger_record(session, turn, add_event)


def ledger_cancel(session, actions, reason):
    """Held orders cancelled by the resident, or discarded for a new order: CANCELLED.

    Returns the cancelled orders, so that the page can name what it set aside even when the
    reader had no name for it (a study it asked about, a fragment it could not read).
    """
    ledger = session.setdefault("order_ledger", [])
    minute = _minute(session)
    ids = {a.get("_order_id") for a in actions or [] if isinstance(a, dict) and a.get("_order_id")}
    submissions = {a.get("_submission_id") for a in actions or [] if isinstance(a, dict) and a.get("_submission_id")}
    cancelled = []
    for order in ledger:
        held_question = order.get("class") == "held_with_question" and order.get("submission_id") in submissions
        if (order.get("order_id") in ids or held_question) and order.get("fate") in L.HELD:
            L.set_fate(order, "CANCELLED", reason, minute=minute)
            cancelled.append(order)
    return cancelled


def ledger_resolve_held(session, actions, executed, minute, add_event):
    """A held bundle answered: what was held with its question and never read ends unrecognised."""
    if not executed:
        return
    ledger = session.setdefault("order_ledger", [])
    submissions = {a.get("_submission_id") for a in actions or [] if isinstance(a, dict) and a.get("_submission_id")}
    for order in ledger:
        if order.get("class") == "held_with_question" and order.get("submission_id") in submissions \
                and order.get("fate") in L.HELD:
            L.set_fate(order, "UNRECOGNIZED", "the reader asked about the order and did not read this part of it",
                       minute=minute, modelled_effect=False, receipt=L.unrecognized_receipt(order.get("span") or ""))
            add_event("prototype", order["receipt"])
